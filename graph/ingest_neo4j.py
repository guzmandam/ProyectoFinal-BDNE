"""ingest_neo4j.py

Bulk‑load the CSV files produced by `export_to_csv.py` directly from Python
using the Neo4j Bolt driver.  This avoids having to paste Cypher into the
Browser and works even if `LOAD CSV` is blocked by configuration.

Prerequisites
-------------
1. Run `export_to_csv.py` – you need the folder `graph/graph_csv/*`.
2. Neo4j container running (see docker‑compose) at bolt://localhost:7687.
3. Install deps:
      pip install neo4j tqdm pandas

Execution
---------
    python ingest_neo4j.py

The script streams the CSV rows in batches (size 500) and uses
`UNWIND $batch … MERGE` statements for each entity / relationship.
"""

import os
import csv
from pathlib import Path
from typing import List, Dict, Any

from neo4j import GraphDatabase, Transaction
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Get current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

CSV_DIR = Path(current_dir, "graph_csv")  # where export_to_csv.py saves files
BATCH   = 500                # rows per UNWIND batch

NEO4J_URI  = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "MyStrongPassword25"

# ---------------------------------------------------------------------------
def stream_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row

def chunks(iterable, size):
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch

# ---------------------------------------------------------------------------
# Cypher templates ----------------------------------------------------------
NODE_QUERIES: Dict[str, str] = {
    "nodes_category.csv": """
        UNWIND $rows AS row
        MERGE (c:Category {id: toInteger(row.id)})
          ON CREATE SET c.name = row.name
    """,
    "nodes_product.csv": """
        UNWIND $rows AS row
        MERGE (p:Product {id: toInteger(row.id)})
          ON CREATE SET p.name = row.name, p.price = toFloat(row.price)
    """,
    "nodes_store.csv": """
        UNWIND $rows AS row
        MERGE (s:Store {id: toInteger(row.id)})
          ON CREATE SET s.name = row.name, s.address = row.address
    """,
    "nodes_employee.csv": """
        UNWIND $rows AS row
        MERGE (e:Employee {id: toInteger(row.id)})
          ON CREATE SET e.first_name = row.first_name, e.last_name = row.last_name, e.position = row.position
    """,
    "nodes_customer.csv": """
        UNWIND $rows AS row
        MERGE (c:Customer {id: toInteger(row.id)})
          ON CREATE SET c.first_name = row.first_name, c.last_name = row.last_name, c.email = row.email
    """,
    "nodes_sale.csv": """
        UNWIND $rows AS row
        MERGE (s:Sale {id: toInteger(row.id)})
          ON CREATE SET s.timestamp = datetime(replace(row.sale_timestamp, ' ', 'T')), s.total = toFloat(row.total_amount)
    """,
    "nodes_line.csv": """
        UNWIND $rows AS row
        MERGE (l:Line {id: row.id})
          ON CREATE SET l.quantity = toInteger(row.quantity), l.unit_price = toFloat(row.unit_price), l.line_total = toFloat(row.line_total)
    """,
}

REL_QUERIES: Dict[str, str] = {
    "rels_product_category.csv": """
        UNWIND $rows AS row
        MATCH (p:Product {id: toInteger(row.product_id)}), (c:Category {id: toInteger(row.category_id)})
        MERGE (p)-[:IN_CATEGORY]->(c)
    """,
    "rels_sale_line.csv": """
        UNWIND $rows AS row
        MATCH (s:Sale {id: toInteger(row.sale_id)}), (l:Line {id: row.line_id})
        MERGE (s)-[:CONTAINS]->(l)
    """,
    "rels_line_product.csv": """
        UNWIND $rows AS row
        MATCH (l:Line {id: row.line_id}), (p:Product {id: toInteger(row.product_id)})
        MERGE (l)-[:OF_PRODUCT]->(p)
    """,
    "rels_customer_sale.csv": """
        UNWIND $rows AS row
        MATCH (c:Customer {id: toInteger(row.customer_id)}), (s:Sale {id: toInteger(row.sale_id)})
        MERGE (c)-[:PLACED]->(s)
    """,
    "rels_sale_store.csv": """
        UNWIND $rows AS row
        MATCH (s:Sale {id: toInteger(row.sale_id)}), (st:Store {id: toInteger(row.store_id)})
        MERGE (s)-[:HAPPENED_AT]->(st)
    """,
    "rels_sale_employee.csv": """
        UNWIND $rows AS row
        MATCH (s:Sale {id: toInteger(row.sale_id)}), (e:Employee {id: toInteger(row.employee_id)})
        MERGE (s)-[:HANDLED_BY]->(e)
    """,
    "rels_employee_store.csv": """
        UNWIND $rows AS row
        MATCH (e:Employee {id: toInteger(row.employee_id)}), (st:Store {id: toInteger(row.store_id)})
        MERGE (e)-[:WORKS_AT]->(st)
    """,
    "rels_store_product_qty.csv": """
        UNWIND $rows AS row
        MATCH (st:Store {id: toInteger(row.store_id)}), (p:Product {id: toInteger(row.product_id)})
        MERGE (st)-[r:STOCKS]->(p)
          ON CREATE SET r.qty = toInteger(row.quantity)
    """,
}

# ---------------------------------------------------------------------------


def ingest(file_name: str, query: str, tx: Transaction):
    path = CSV_DIR / file_name
    for batch in chunks(stream_csv(path), BATCH):
        tx.run(query, rows=batch)


def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    with driver.session() as session:
        # Nodes first -------------------------------------------------------
        for fname, cy in NODE_QUERIES.items():
            print(f"Loading {fname} …")
            with session.begin_transaction() as tx:
                ingest(fname, cy, tx)
            print("  ✓ done")

        # Relationships ----------------------------------------------------
        for fname, cy in REL_QUERIES.items():
            print(f"Loading {fname} …")
            with session.begin_transaction() as tx:
                ingest(fname, cy, tx)
            print("  ✓ done")

    driver.close()
    print("✔ All CSV data ingested into Neo4j")

if __name__ == "__main__":
    main()
