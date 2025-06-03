"""graph_benchmark.py

Compare execution time of a deep query in PostgreSQL vs Neo4j.
Requires:
  • PostgreSQL service populated (DB commerce)
  • Neo4j service with CSV import already loaded (see neo4j_load.cypher)

Measurements written to graph_times.csv
"""

import time, csv
from pathlib import Path
import psycopg2
from neo4j import GraphDatabase

PG = dict(host="localhost", port=5432, user="postgres", password="postgres", dbname="commerce")
NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "MyStrongPassword25")

OUT = Path("graph_times.csv")

# PostgreSQL Query: Find top 10 customers by purchase count in the last 24 months
# This query joins across all tables to count how many individual line items each customer
# has purchased, traversing: Customer -> Sale -> SaleLine -> Product -> Category
# The result shows customers who have bought the most individual items (not unique products)
SQL_QUERY = """
SELECT c.email, COUNT(*) AS purchases
FROM   Customer c
JOIN   Sale s      ON c.customer_id = s.customer_id
JOIN   SaleLine l  ON s.sale_id = l.sale_id
JOIN   Product p   ON l.product_id = p.product_id
JOIN   Category cat ON p.category_id = cat.category_id
WHERE  s.sale_timestamp >= NOW() - INTERVAL '24 months'
GROUP  BY c.email
ORDER  BY purchases DESC
LIMIT  10;
"""

# Multiple Cypher queries to test different relationship paths
CYPHER_QUERIES = {
    # Neo4j Query 1: Equivalent to SQL query above
    # Traverses the full relationship path from Customer through all entities to Category
    # Counts total line items purchased by each customer in the last 24 months
    "full_path": """
        MATCH (c:Customer)-[:PLACED]->(s:Sale)-[:CONTAINS]->(l:Line)-[:OF_PRODUCT]->(p:Product)-[:IN_CATEGORY]->(cat:Category)
        WHERE s.timestamp >= datetime() - duration({months:24})
        RETURN c.email AS email, COUNT(*) AS purchases
        ORDER BY purchases DESC
        LIMIT 10
    """,
    
    # Neo4j Query 2: Customer product diversity analysis
    # Finds customers who have purchased the most unique/distinct products (not total quantity)
    # Stops at Product level without going to Category, focusing on product variety
    "customer_to_product": """
        MATCH (c:Customer)-[:PLACED]->(s:Sale)-[:CONTAINS]->(l:Line)-[:OF_PRODUCT]->(p:Product)
        WHERE s.timestamp >= datetime() - duration({months:24})
        RETURN c.email AS email, COUNT(DISTINCT p) AS unique_products
        ORDER BY unique_products DESC
        LIMIT 10
    """,
    
    # Neo4j Query 3: Simple customer sales summary
    # Basic customer analysis showing purchase frequency and total spending
    # Only traverses Customer -> Sale relationship for simpler aggregation
    "customer_sales_simple": """
        MATCH (c:Customer)-[:PLACED]->(s:Sale)
        WHERE s.timestamp >= datetime() - duration({months:24})
        RETURN c.email AS email, COUNT(s) AS purchases, SUM(s.total) AS total_spent
        ORDER BY purchases DESC
        LIMIT 10
    """,
    
    # Neo4j Utility Query: Database introspection
    # Lists all relationship types available in the Neo4j database
    # Used for debugging and verifying the graph schema is loaded correctly
    "relationship_check": """
        CALL db.relationshipTypes() YIELD relationshipType
        RETURN relationshipType
        ORDER BY relationshipType
    """
}

results = []

# PostgreSQL benchmark
print("Running PostgreSQL benchmark...")
with psycopg2.connect(**PG) as conn:
    with conn.cursor() as cur:
        t0 = time.perf_counter()
        cur.execute(SQL_QUERY)
        cur.fetchall()
        sql_dt = time.perf_counter() - t0
        results.append(("sql_query", sql_dt))
        print(f"PostgreSQL query: {sql_dt:.3f} s")

# Neo4j benchmarks
print("Running Neo4j benchmarks...")
driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
with driver.session() as session:
    
    # First, check what relationships exist
    print("Checking available relationships...")
    rel_result = session.run(CYPHER_QUERIES["relationship_check"])
    available_rels = [record["relationshipType"] for record in rel_result]
    print(f"Available relationships: {sorted(available_rels)}")
    
    # Test each query
    for query_name, query in CYPHER_QUERIES.items():
        if query_name == "relationship_check":
            continue
            
        print(f"Testing {query_name}...")
        try:
            t0 = time.perf_counter()
            result = session.run(query)
            records = list(result)  # Consume all records
            cy_dt = time.perf_counter() - t0
            results.append((f"cypher_{query_name}", cy_dt))
            print(f"  ✓ {query_name}: {cy_dt:.3f} s ({len(records)} results)")
        except Exception as e:
            print(f"  ✗ {query_name} failed: {e}")
            results.append((f"cypher_{query_name}", -1))  # -1 indicates failure

driver.close()

# Save results
with OUT.open("w", newline="") as f:
    csv.writer(f).writerows([("query", "seconds")] + results)
print(f"✔ Benchmarks saved to {OUT}")

# Print summary
print("\n" + "="*50)
print("BENCHMARK SUMMARY")
print("="*50)
for query_type, time_taken in results:
    if time_taken >= 0:
        print(f"{query_type:<25}: {time_taken:.3f} s")
    else:
        print(f"{query_type:<25}: FAILED")
