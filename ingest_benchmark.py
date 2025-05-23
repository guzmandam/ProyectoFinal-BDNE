"""ingest_benchmark.py – v2

Benchmark three ingestion paths for the Commerce‑Minorista demo:
  1. SQL script → PostgreSQL database **commerce**              (baseline)
  2. JSON docs → MongoDB database **commerce**                  (document)
  3. JSON docs → PostgreSQL database **commerce_sql_json**      (relational via JSON)

Outputs `ingest_times.csv` with four rows:
  step,duration_seconds
  postgres_sql,<t>
  postgres_json,<t>
  mongo_catalog,<t>
  mongo_sales,<t>

Dependencies:
    pip install psycopg2-binary pymongo tqdm

Containers (via docker-compose.yml):
    postgres 16 exposed on 5432
    mongo 7     exposed on 27017
"""

from __future__ import annotations

import os
import time
import csv
import json
from io import StringIO
from pathlib import Path
from typing import Iterable, List

import psycopg2
from psycopg2 import sql
from pymongo import MongoClient
from tqdm import tqdm

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
PG_HOST     = os.getenv("PG_HOST", "localhost")
PG_PORT     = int(os.getenv("PG_PORT", 5432))
PG_PORT_JSON = int(os.getenv("PG_PORT_JSON", 5433))
PG_USER     = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "postgres")
PG_DB_SQL   = os.getenv("PG_DB", "commerce")          # baseline DB
PG_DB_JSON  = "commerce_sql_json"                       # new DB for JSON ingest

MONGO_URI   = os.getenv("MONGO_URI", "mongodb://localhost:27017")

CURRENT_DIR = Path(__file__).parent

SQL_FILE    = CURRENT_DIR / "sql/commerce_load.sql"     # full DDL + INSERTs
DDL_FILE    = CURRENT_DIR / "sql/commerce_schema.sql"    # pure DDL only
CATALOG_JSON= CURRENT_DIR / "json/stores_catalog.json"
SALES_JSON  = CURRENT_DIR / "json/sales_docs.json"
OUT_CSV     = CURRENT_DIR / "ingest_times.csv"

BATCH_SIZE  = 1000        # rows per batch INSERT / COPY

# ---------------------------------------------------------------------------
# UTILITIES
# ---------------------------------------------------------------------------

def timed(label: str):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            print(f"\n▶ {label} …")
            t0 = time.perf_counter()
            result = fn(*args, **kwargs)
            dt = time.perf_counter() - t0
            print(f"   {label}: {dt:.2f} s")
            return dt, result
        return wrapper
    return decorator

# small helper to COPY from memory -----------------------------------------

def copy_rows(cur, table: str, columns: List[str], rows: Iterable[Iterable]):
    if not rows:
        return
    
    buffer = StringIO()
    for row in rows:
        buffer.write("\t".join(str(v) for v in row) + "\n")
    buffer.seek(0)
    cols = sql.SQL(',').join(map(sql.Identifier, columns))
    # force lower‑case to match unquoted DDL table names
    cur.copy_expert(sql.SQL("COPY {} ({}) FROM STDIN WITH (FORMAT text)")
                    .format(sql.Identifier(table.lower()), cols), buffer)

# ---------------------------------------------------------------------------
# POSTGRES BASELINE (SQL file)
# ---------------------------------------------------------------------------
@timed("PostgreSQL load - SQL script")
def load_postgres_sql():
    with psycopg2.connect(host=PG_HOST, port=PG_PORT, user=PG_USER, password=PG_PASSWORD, dbname=PG_DB_SQL) as conn:
        conn.autocommit = False
        with conn.cursor() as cur:
            cur.execute(SQL_FILE.read_text())
        conn.commit()

# ---------------------------------------------------------------------------
# POSTGRES via JSON
# ---------------------------------------------------------------------------
@timed("PostgreSQL load – JSON")
def load_postgres_from_json():
    # 1. connect to new DB and create schema
    with psycopg2.connect(host=PG_HOST, port=PG_PORT_JSON, user=PG_USER, password=PG_PASSWORD, dbname=PG_DB_JSON) as conn:
        conn.autocommit = False
        with conn.cursor() as cur:
            cur.execute(DDL_FILE.read_text())

            # --- ingest catalog JSON ---
            catalog = json.loads(CATALOG_JSON.read_text())

            category_map, product_map, store_map, employee_map = {}, {}, {}, {}
            next_cat = next_prod = next_emp = 1

            for store_doc in catalog:
                s_id = len(store_map) + 1
                store_map[store_doc["store_name"]] = s_id
                copy_rows(cur, "store", ["store_id", "name", "address"],
                          [(s_id, store_doc["store_name"], store_doc.get("address", ""))])

                for emp in store_doc.get("employees", []):
                    eid = next_emp; next_emp += 1
                    employee_map[(emp["first_name"], emp["last_name"], s_id)] = eid
                    copy_rows(cur, "employee", ["employee_id", "first_name", "last_name", "position", "store_id"],
                              [(eid, emp["first_name"], emp["last_name"], emp.get("position", ""), s_id)])

                for inv in store_doc.get("inventory", []):
                    prod = inv["product"]
                    cat_name = prod["category"]
                    if cat_name not in category_map:
                        category_map[cat_name] = next_cat; next_cat += 1
                        copy_rows(cur, "category", ["category_id", "name"],
                                  [(category_map[cat_name], cat_name)])

                    if prod["name"] not in product_map:
                        pid = next_prod; next_prod += 1
                        product_map[prod["name"]] = pid
                        copy_rows(cur, "product", ["product_id", "name", "price", "category_id"],
                                  [(pid, prod["name"], prod["price"], category_map[cat_name])])

                    copy_rows(cur, "inventory", ["store_id", "product_id", "quantity"],
                              [(s_id, product_map[prod["name"]], inv["quantity"])])

            # Sales
            customers_map = {}
            next_cust = next_sale = 1

            sales_docs = json.loads(SALES_JSON.read_text())

            def extract_ts(ts):
                """Return plain ISO‑8601 string acceptable to Postgres."""
                if isinstance(ts, dict) and "$date" in ts:
                    return ts["$date"].replace("Z", "")  # keep ISO, drop Z for simplicity
                return ts  # already string
            
            for sale in tqdm(sales_docs, desc="sales json -> pg"):
                cust_email = sale["customer"]["email"]
                if cust_email not in customers_map:
                    cid = next_cust; next_cust += 1
                    customers_map[cust_email] = cid
                    c = sale["customer"]
                    copy_rows(cur, "customer", ["customer_id", "first_name", "last_name", "email"],
                              [(cid, c["first_name"], c["last_name"], c["email"])])

                store_id = store_map[sale["store"]["name"]]
                emp_key = (sale["employee"]["first_name"], sale["employee"]["last_name"], store_id)
                employee_id = employee_map[emp_key]

                sale_id = next_sale; next_sale += 1
                ts_value = extract_ts(sale["timestamp"])
                copy_rows(cur, "sale", ["sale_id", "sale_timestamp", "customer_id", "store_id", "employee_id", "total_amount"],
                          [(sale_id, ts_value, customers_map[cust_email], store_id, employee_id, sale["total_amount"])])

                line_no = 1
                for ln in sale["lines"]:
                    prod_id = product_map.get(ln["product"]["name"])
                    if prod_id is None:
                        #print(f"Product {ln['product']['name']} not found")
                        continue
                    copy_rows(cur, "saleline", ["sale_id", "line_number", "product_id", "quantity", "unit_price", "line_total"],
                              [(sale_id, line_no, prod_id, ln["quantity"], ln["product"]["price"], ln["line_total"])])
                    line_no += 1

        conn.commit()

# ---------------------------------------------------------------------------
# MONGO INGEST
# ---------------------------------------------------------------------------
@timed("MongoDB load - catalog")
def load_mongo_catalog():
    client = MongoClient(MONGO_URI)
    db = client["commerce"]
    coll = db["stores"]
    coll.drop()
    docs = json.loads(CATALOG_JSON.read_text())
    coll.insert_many(docs)
    client.close()

@timed("MongoDB load – sales")
def load_mongo_sales():
    client = MongoClient(MONGO_URI)
    db = client["commerce"]
    coll = db["sales"]
    coll.drop()
    docs = json.loads(SALES_JSON.read_text())
    CHUNK = 2000
    for chunk in tqdm([docs[i:i+CHUNK] for i in range(0, len(docs), CHUNK)], desc="mongo sales batches"):
        coll.insert_many(chunk)
    client.close()

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    results = []

    # 1. baseline SQL
    dt_pg_sql, _ = load_postgres_sql()
    results.append(("postgres_sql", dt_pg_sql))

    # 2. JSON → Postgres
    dt_pg_json, _ = load_postgres_from_json()
    results.append(("postgres_json", dt_pg_json))

    # 3. Mongo catalog & sales
    dt_cat, _ = load_mongo_catalog()
    dt_sales, _ = load_mongo_sales()
    results.extend([
        ("mongo_catalog", dt_cat),
        ("mongo_sales", dt_sales),
    ])

    with OUT_CSV.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["step", "duration_seconds"])
        writer.writerows(results)

    print(f"\n✔ Benchmark finished. Results saved to {OUT_CSV}")

if __name__ == "__main__":
    main()
