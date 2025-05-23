import random
import itertools
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from faker import Faker
from faker.providers import person, address, company, date_time

CURRENT_DIR = Path(__file__).parent

# ----------------------------- CONFIGURABLE CONSTANTS -----------------------------
CATEGORIES = 10
PRODUCTS = 100
STORES = 5
EMPLOYEES = 25  # should be multiple of STORES
CUSTOMERS = 1000
SALES = 20000
MIN_LINES = 1
MAX_LINES = 10
BATCH_SIZE = 1000
SQL_FILE = CURRENT_DIR / "commerce_load.sql"
RANDOM_SEED = 42
START_DATE = datetime(2023, 5, 23)
END_DATE = datetime(2025, 5, 22)

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

def chunks(iterable, size):
    """Yield successive size-d chunks from iterable."""
    it = iter(iterable)
    while True:
        chunk = list(itertools.islice(it, size))
        if not chunk:
            break
        yield chunk


def fmt_value(value):
    """Return SQL literal from Python value (basic types only)."""
    if value is None:
        return "NULL"
    if isinstance(value, str):
        return "'" + value.replace("'", "''") + "'"
    if isinstance(value, datetime):
        return "'" + value.strftime("%Y-%m-%d %H:%M:%S") + "'"
    return str(value)


def build_insert(table, columns, rows):
    """Build a single INSERT statement for up to BATCH_SIZE rows."""
    col_list = ", ".join(columns)
    values_parts = []
    for row in rows:
        values_parts.append("(" + ", ".join(fmt_value(v) for v in row) + ")")
    values_block = ",\n    ".join(values_parts)
    return f"INSERT INTO {table} ({col_list})\nVALUES\n    {values_block};\n"


# ----------------------------- DATA GENERATION ------------------------------------
print("Generating catalog data …")

# 1. Category
categories = [(i + 1, fake.unique.word().title()) for i in range(CATEGORIES)]

# 2. Product
products = []
for i in range(PRODUCTS):
    product_id = i + 1
    name = fake.unique.catch_phrase()
    price = round(random.uniform(5, 1000), 2)
    category_id = random.choice(categories)[0]
    products.append((product_id, name, price, category_id))

# 3. Store
stores = []
for i in range(STORES):
    store_id = i + 1
    name = fake.company()
    address = fake.address().replace("\n", ", ")
    stores.append((store_id, name, address))

# 4. Employee (≈ equal per store)
employees = []
positions = ["Cajero", "Vendedor", "Gerente"]
for i in range(EMPLOYEES):
    employee_id = i + 1
    first_name = fake.first_name()
    last_name = fake.last_name()
    position = random.choice(positions)
    store_id = (employee_id % STORES) + 1  # simple round-robin assignment
    employees.append((employee_id, first_name, last_name, position, store_id))

# 5. Customer
customers = []
for i in range(CUSTOMERS):
    customer_id = i + 1
    first_name = fake.first_name()
    last_name = fake.last_name()
    email = fake.email()
    customers.append((customer_id, first_name, last_name, email))

# 6. Inventory (≈50 % of products per store)
inventory = []
for store_id, _, _ in stores:
    prod_sample = random.sample(products, k=PRODUCTS // 2)
    for prod in prod_sample:
        quantity = random.randint(0, 200)
        inventory.append((store_id, prod[0], quantity))

# 7. Sales and SaleLines
print("Generating sales data … (this may take a few seconds)")

from numpy.random import zipf

def random_date():
    delta = END_DATE - START_DATE
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return START_DATE + timedelta(seconds=random_seconds)

zipf_samples = zipf(a=2.0, size=SALES)
zipf_indices = zipf_samples % CUSTOMERS  # map to 0..CUSTOMERS-1

sales = []
sale_lines = []
next_sale_id = 1
for i in range(SALES):
    sale_id = next_sale_id
    next_sale_id += 1

    sale_timestamp = random_date()
    store = random.choice(stores)
    store_id = store[0]
    # pick employee from that store
    employees_in_store = [e for e in employees if e[4] == store_id]
    employee_id = random.choice(employees_in_store)[0]
    customer_id = customers[zipf_indices[i]][0]

    n_lines = random.randint(MIN_LINES, MAX_LINES)
    products_in_sale = random.sample(products, k=n_lines)
    total_amount = 0.0
    line_number = 1
    for prod in products_in_sale:
        quantity = random.randint(1, 5)
        unit_price = prod[2]
        line_total = round(unit_price * quantity, 2)
        sale_lines.append((sale_id, line_number, prod[0], quantity, unit_price, line_total))
        line_number += 1
        total_amount += line_total
    total_amount = round(total_amount, 2)
    sales.append((sale_id, sale_timestamp, customer_id, store_id, employee_id, total_amount))

print("Writing SQL file …")

# ----------------------------- DDL STATEMENTS -------------------------------------
DDL = """
-- ====================== DDL SECTION (PostgreSQL) =====================
CREATE TABLE Category (
    category_id INT PRIMARY KEY,
    name VARCHAR(100)
);

CREATE TABLE Product (
    product_id INT PRIMARY KEY,
    name VARCHAR(100),
    price DECIMAL(10,2),
    category_id INT REFERENCES Category(category_id)
);

CREATE TABLE Store (
    store_id INT PRIMARY KEY,
    name VARCHAR(100),
    address VARCHAR(200)
);

CREATE TABLE Employee (
    employee_id INT PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    position VARCHAR(50),
    store_id INT REFERENCES Store(store_id)
);

CREATE TABLE Customer (
    customer_id INT PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100)
);

CREATE TABLE Inventory (
    store_id INT REFERENCES Store(store_id),
    product_id INT REFERENCES Product(product_id),
    quantity INT,
    PRIMARY KEY (store_id, product_id)
);

CREATE TABLE Sale (
    sale_id INT PRIMARY KEY,
    sale_timestamp TIMESTAMP,
    customer_id INT REFERENCES Customer(customer_id),
    store_id INT REFERENCES Store(store_id),
    employee_id INT REFERENCES Employee(employee_id),
    total_amount DECIMAL(12,2)
);

CREATE TABLE SaleLine (
    sale_id INT REFERENCES Sale(sale_id),
    line_number INT,
    product_id INT REFERENCES Product(product_id),
    quantity INT,
    unit_price DECIMAL(10,2),
    line_total DECIMAL(12,2),
    PRIMARY KEY (sale_id, line_number)
);

-- Simple performance indices
CREATE INDEX idx_sale_timestamp ON Sale(sale_timestamp);
CREATE INDEX idx_product_category ON Product(category_id);
-- ====================================================================
"""

# ----------------------------- WRITE SQL FILE -------------------------------------
with SQL_FILE.open("w", encoding="utf-8") as f:
    f.write(DDL)

    # Helper to write batches
    def write_batches(data, table, columns):
        for batch in chunks(data, BATCH_SIZE):
            f.write(build_insert(table, columns, batch))

    write_batches(categories, "Category", ["category_id", "name"])
    write_batches(products, "Product", ["product_id", "name", "price", "category_id"])
    write_batches(stores, "Store", ["store_id", "name", "address"])
    write_batches(employees, "Employee", ["employee_id", "first_name", "last_name", "position", "store_id"])
    write_batches(customers, "Customer", ["customer_id", "first_name", "last_name", "email"])
    write_batches(inventory, "Inventory", ["store_id", "product_id", "quantity"])
    write_batches(sales, "Sale", ["sale_id", "sale_timestamp", "customer_id", "store_id", "employee_id", "total_amount"])
    write_batches(sale_lines, "SaleLine", ["sale_id", "line_number", "product_id", "quantity", "unit_price", "line_total"])

    f.write("COMMIT;\n")

print(f"Done! Wrote {SQL_FILE.resolve()}")
