from __future__ import annotations

import random
import itertools
import json
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from faker import Faker
from faker.providers import person, address, company, date_time
from jsonschema import Draft202012Validator

# ============================ CONFIGURABLE CONSTANTS ==============================
CATEGORIES = 10
PRODUCTS   = 100
STORES     = 5
EMPLOYEES  = 25   # ≈5 per store
CUSTOMERS  = 1000
SALES      = 20000  # ≈60k sale lines
MIN_LINES  = 1
MAX_LINES  = 10
RANDOM_SEED = 42
START_DATE  = datetime(2023, 5, 23)
END_DATE    = datetime(2025, 5, 22)

DATA_DIR = Path(__file__).parent

CATALOG_FILE = DATA_DIR / "stores_catalog.json"
SALES_FILE   = DATA_DIR / "sales_docs.json"
CAT_SCHEMA   = DATA_DIR / "stores_catalog_schema.json"
SALE_SCHEMA  = DATA_DIR / "sales_docs_schema.json"

# ----------------------------------------------------------------------------------
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

fake = Faker("es_MX")
Faker.seed(RANDOM_SEED)

fake.add_provider(person)
fake.add_provider(address)
fake.add_provider(company)
fake.add_provider(date_time)

# ----------------------------- HELPER FUNCTIONS -----------------------------------

def mongo_date(dt):
    """Return Extended-JSON representation so mongoimport stores a Date."""
    return {"$date": dt.strftime("%Y-%m-%dT%H:%M:%SZ")}


def chunks(iterable, size):
    it = iter(iterable)
    while True:
        batch = list(itertools.islice(it, size))
        if not batch:
            break
        yield batch


def rand_dt() -> datetime:
    delta = END_DATE - START_DATE
    return START_DATE + timedelta(seconds=random.randint(0, int(delta.total_seconds())))

# ----------------------------- CATALOG GENERATION ---------------------------------
print("▶ Generating catalog data …")

categories = [(i + 1, fake.unique.word().title()) for i in range(CATEGORIES)]

products = [
    {
        "product_id": i + 1,
        "name": fake.unique.catch_phrase(),
        "price": round(random.uniform(5, 1000), 2),
        "category_id": random.choice(categories)[0],
    }
    for i in range(PRODUCTS)
]

stores = [
    {
        "store_id": i + 1,
        "name": fake.company(),
        "address": fake.address().replace("\n", ", "),
    }
    for i in range(STORES)
]

positions = ["Cajero", "Vendedor", "Gerente"]
employees = [
    {
        "employee_id": i + 1,
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "position": random.choice(positions),
        "store_id": (i + 1) % STORES + 1,
    }
    for i in range(EMPLOYEES)
]

customers = [
    {
        "customer_id": i + 1,
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.email(),
    }
    for i in range(CUSTOMERS)
]

# Inventory: ≈50% of products per store
inventory = []
for st in stores:
    sample = random.sample(products, k=PRODUCTS // 2)
    for prod in sample:
        inventory.append({
            "store_id": st["store_id"],
            "product_id": prod["product_id"],
            "quantity": random.randint(0, 200),
        })

# ----------------------------- SALES GENERATION -----------------------------------
print("▶ Generating sales data …")

from numpy.random import zipf
zipf_ids = zipf(a=2.0, size=SALES) % CUSTOMERS

sales_hdr  = []
sale_lines = []

for sale_id in range(1, SALES + 1):
    st  = random.choice(stores)
    emp = random.choice([e for e in employees if e["store_id"] == st["store_id"]])
    cust= customers[zipf_ids[sale_id - 1]]

    n_lines = random.randint(MIN_LINES, MAX_LINES)
    chosen  = random.sample(products, k=n_lines)

    total = 0.0
    for line_num, prod in enumerate(chosen, start=1):
        qty        = random.randint(1, 5)
        line_total = round(prod["price"] * qty, 2)
        sale_lines.append({
            "sale_id": sale_id,
            "line_number": line_num,
            "product_id": prod["product_id"],
            "quantity": qty,
            "unit_price": prod["price"],
            "line_total": line_total,
        })
        total += line_total

    sales_hdr.append({
        "sale_id": sale_id,
        "timestamp": rand_dt(),
        "customer_id": cust["customer_id"],
        "store_id": st["store_id"],
        "employee_id": emp["employee_id"],
        "total_amount": round(total, 2),
    })

# ----------------------------- BUILD DOCUMENTS ------------------------------------
print("▶ Building JSON documents …")

cat_by_id  = {cid: cname for cid, cname in categories}
prod_by_id = {p["product_id"]: p for p in products}
emp_by_id  = {e["employee_id"]: e for e in employees}
store_by_id= {s["store_id"]: s for s in stores}
cust_by_id = {c["customer_id"]: c for c in customers}

# group sale lines by sale_id for fast access
lines_by_sale = {}
for line in sale_lines:
    lines_by_sale.setdefault(line["sale_id"], []).append(line)

# 1️⃣ catalog docs (stores)
store_docs = []
for st in stores:
    inv_embedded = []
    for inv in (i for i in inventory if i["store_id"] == st["store_id"]):
        pr = prod_by_id[inv["product_id"]]
        inv_embedded.append({
            "product": {
                "name": pr["name"],
                "category": cat_by_id[pr["category_id"]],
                "price": pr["price"],
            },
            "quantity": inv["quantity"],
        })
    emp_embedded = [{
        "first_name": e["first_name"],
        "last_name":  e["last_name"],
        "position":   e["position"],
    } for e in employees if e["store_id"] == st["store_id"]]

    store_docs.append({
        "store_name": st["name"],
        "address": st["address"],
        "employees": emp_embedded,
        "inventory": inv_embedded,
    })

# 2️⃣ sales docs (transactions)
sale_docs = []
for sh in sales_hdr:
    st  = store_by_id[sh["store_id"]]
    emp = emp_by_id[sh["employee_id"]]
    cust= cust_by_id[sh["customer_id"]]

    embedded_lines = []
    for ln in lines_by_sale[sh["sale_id"]]:
        pr = prod_by_id[ln["product_id"]]
        embedded_lines.append({
            "product": {
                "name": pr["name"],
                "category": cat_by_id[pr["category_id"]],
                "price": pr["price"],
            },
            "quantity": ln["quantity"],
            "line_total": ln["line_total"],
        })

    sale_docs.append({
        "timestamp": mongo_date(sh["timestamp"]),
        "store":    {"name": st["name"]},
        "employee": {"first_name": emp["first_name"], "last_name": emp["last_name"]},
        "customer": {"first_name": cust["first_name"], "last_name": cust["last_name"], "email": cust["email"]},
        "lines": embedded_lines,
        "total_amount": sh["total_amount"],
    })

# ----------------------------- SCHEMA (OPTIONAL) ----------------------------------
# print("▶ Building JSON Schema …")

# catalog_schema = {
#     "$schema": "https://json-schema.org/draft/2020-12/schema",
#     "title": "StoreCatalog",
#     "type": "array",
#     "items": {
#         "type": "object",
#         "required": ["store_name", "inventory"],
#         "properties": {
#             "store_name": {"type": "string"},
#             "address":    {"type": "string"},
#             "employees":  {"type": "array"},
#             "inventory":  {"type": "array"},
#         },
#     },
# }

# sales_schema = {
#     "$schema": "https://json-schema.org/draft/2020-12/schema",
#     "title": "SaleDocument",
#     "type": "array",
#     "items": {
#         "type": "object",
#         "required": ["timestamp", "store", "lines", "total_amount"],
#         "properties": {
#             "timestamp":    {"type": "string"},
#             "store":        {"type": "object"},
#             "employee":     {"type": "object"},
#             "customer":     {"type": "object"},
#             "lines":        {"type": "array"},
#             "total_amount": {"type": "number"},
#         },
#     },
# }

# ----------------------------- WRITE FILES ----------------------------------------
print("▶ Writing files …")
CATALOG_FILE.write_text(json.dumps(store_docs, ensure_ascii=False, indent=2))
SALES_FILE.write_text(json.dumps(sale_docs, ensure_ascii=False, indent=2))
# CAT_SCHEMA.write_text(json.dumps(catalog_schema, indent=2))
# SALE_SCHEMA.write_text(json.dumps(sales_schema, indent=2))

# # quick validation on first doc of each collection
# Draft202012Validator(catalog_schema).validate(store_docs[:1])
# Draft202012Validator(sales_schema).validate(sale_docs[:1])

print("✔ JSON artefacts generated successfully:")
print(f"  • {CATALOG_FILE}")
print(f"  • {SALES_FILE}")
print("  (Schemas saved for reference)")
