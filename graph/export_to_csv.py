"""export_to_csv.py

Dump PostgreSQL tables to CSVs that Neo4j can import (nodes & relationships).
The script creates a folder `graph_csv` (same dir) and writes:
  nodes_*.csv - Category, Product, Store, Employee, Customer, Sale, Line
  rels_*.csv - individual relationship edge files

Run after Postgres is populated:
    docker compose up -d postgres
    pip install psycopg2-binary tqdm
    python export_to_csv.py

CSV delimiter = comma, HEADER row included.
"""

import csv, os, pathlib
from pathlib import Path
import psycopg2
from tqdm import tqdm

# Get current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

PG_CONN = dict(host="localhost", port=5432, user="postgres", password="postgres", dbname="commerce")
OUT_DIR = Path(current_dir, "graph_csv")

# Create directory with proper permissions
try:
    OUT_DIR.mkdir(exist_ok=True, mode=0o755)
except PermissionError:
    print(f"Permission denied creating directory: {OUT_DIR}")
    print("Try running with sudo or check directory permissions")
    exit(1)

def dump(cur, query: str, out_path: Path):
    cur.execute(query)
    cols = [d[0] for d in cur.description]
    try:
        with out_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(cols)
            writer.writerows(cur.fetchall())
    except PermissionError:
        print(f"Permission denied writing to: {out_path}")
        print("Try running with sudo or check file/directory permissions")
        raise

with psycopg2.connect(**PG_CONN) as conn:
    with conn.cursor() as cur:
        print("Dumping node CSVs …")
        dump(cur, "SELECT category_id AS id, name FROM Category", OUT_DIR/"nodes_category.csv")
        dump(cur, "SELECT product_id AS id, name, price FROM Product", OUT_DIR/"nodes_product.csv")
        dump(cur, "SELECT store_id AS id, name, address FROM Store", OUT_DIR/"nodes_store.csv")
        dump(cur, "SELECT employee_id AS id, first_name, last_name, position, store_id FROM Employee", OUT_DIR/"nodes_employee.csv")
        dump(cur, "SELECT customer_id AS id, first_name, last_name, email FROM Customer", OUT_DIR/"nodes_customer.csv")
        dump(cur, "SELECT sale_id AS id, sale_timestamp, total_amount, store_id, employee_id, customer_id FROM Sale", OUT_DIR/"nodes_sale.csv")
        dump(cur, "SELECT sale_id AS sale_id, line_number AS id, product_id, quantity, unit_price, line_total FROM SaleLine", OUT_DIR/"nodes_line.csv")

        print("Dumping relationship CSVs …")
        dump(cur, "SELECT product_id, category_id FROM Product", OUT_DIR/"rels_product_category.csv")
        dump(cur, "SELECT sale_id, sale_id||'-'||line_number AS line_id FROM SaleLine", OUT_DIR/"rels_sale_line.csv")
        dump(cur, "SELECT sale_id||'-'||line_number AS line_id, product_id FROM SaleLine", OUT_DIR/"rels_line_product.csv")
        dump(cur, "SELECT customer_id, sale_id FROM Sale", OUT_DIR/"rels_customer_sale.csv")
        dump(cur, "SELECT sale_id, store_id FROM Sale", OUT_DIR/"rels_sale_store.csv")
        dump(cur, "SELECT sale_id, employee_id FROM Sale", OUT_DIR/"rels_sale_employee.csv")
        dump(cur, "SELECT employee_id, store_id FROM Employee", OUT_DIR/"rels_employee_store.csv")
        dump(cur, "SELECT store_id, product_id, quantity FROM Inventory", OUT_DIR/"rels_store_product_qty.csv")

print("✔ CSV export ready in graph_csv/")
