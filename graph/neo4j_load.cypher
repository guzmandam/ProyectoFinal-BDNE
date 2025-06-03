// neo4j_load.cypher
// Execute in Neo4j Browser or cypher-shell after placing CSVs in /var/lib/neo4j/import

:auto USING PERIODIC COMMIT 1000
LOAD CSV WITH HEADERS FROM 'file:///nodes_category.csv' AS row
MERGE (:Category {id: toInteger(row.id), name: row.name});

LOAD CSV WITH HEADERS FROM 'file:///nodes_product.csv' AS row
MERGE (p:Product {id: toInteger(row.id)})
  ON CREATE SET p.name = row.name, p.price = toFloat(row.price);

LOAD CSV WITH HEADERS FROM 'file:///nodes_store.csv' AS row
MERGE (:Store {id: toInteger(row.id), name: row.name, address: row.address});

LOAD CSV WITH HEADERS FROM 'file:///nodes_employee.csv' AS row
MERGE (e:Employee {id: toInteger(row.id)})
  SET e.first_name = row.first_name, e.last_name = row.last_name, e.position = row.position;

LOAD CSV WITH HEADERS FROM 'file:///nodes_customer.csv' AS row
MERGE (:Customer {id: toInteger(row.id), first_name: row.first_name, last_name: row.last_name, email: row.email});

LOAD CSV WITH HEADERS FROM 'file:///nodes_sale.csv' AS row
MERGE (s:Sale {id: toInteger(row.id)})
  SET s.timestamp = datetime(row.sale_timestamp), s.total = toFloat(row.total_amount);

LOAD CSV WITH HEADERS FROM 'file:///nodes_line.csv' AS row
MERGE (:Line {id: row.line_id, quantity: toInteger(row.quantity), unit_price: toFloat(row.unit_price), line_total: toFloat(row.line_total)});

// Relationships ------------------------------------------------------------
USING PERIODIC COMMIT 1000
LOAD CSV WITH HEADERS FROM 'file:///rels_product_category.csv' AS row
MATCH (p:Product {id: toInteger(row.product_id)}), (c:Category {id: toInteger(row.category_id)})
MERGE (p)-[:IN_CATEGORY]->(c);

LOAD CSV WITH HEADERS FROM 'file:///rels_sale_line.csv' AS row
MATCH (s:Sale {id: toInteger(row.sale_id)}), (l:Line {id: row.line_id})
MERGE (s)-[:CONTAINS]->(l);

LOAD CSV WITH HEADERS FROM 'file:///rels_line_product.csv' AS row
MATCH (l:Line {id: row.line_id}), (p:Product {id: toInteger(row.product_id)})
MERGE (l)-[:OF_PRODUCT]->(p);

LOAD CSV WITH HEADERS FROM 'file:///rels_customer_sale.csv' AS row
MATCH (c:Customer {id: toInteger(row.customer_id)}), (s:Sale {id: toInteger(row.sale_id)})
MERGE (c)-[:PLACED]->(s);

LOAD CSV WITH HEADERS FROM 'file:///rels_sale_store.csv' AS row
MATCH (s:Sale {id: toInteger(row.sale_id)}), (st:Store {id: toInteger(row.store_id)})
MERGE (s)-[:HAPPENED_AT]->(st);

LOAD CSV WITH HEADERS FROM 'file:///rels_sale_employee.csv' AS row
MATCH (s:Sale {id: toInteger(row.sale_id)}), (e:Employee {id: toInteger(row.employee_id)})
MERGE (s)-[:HANDLED_BY]->(e);

LOAD CSV WITH HEADERS FROM 'file:///rels_employee_store.csv' AS row
MATCH (e:Employee {id: toInteger(row.employee_id)}), (st:Store {id: toInteger(row.store_id)})
MERGE (e)-[:WORKS_AT]->(st);

LOAD CSV WITH HEADERS FROM 'file:///rels_store_product_qty.csv' AS row
MATCH (st:Store {id: toInteger(row.store_id)}), (p:Product {id: toInteger(row.product_id)})
MERGE (st)-[r:STOCKS]->(p)
  ON CREATE SET r.qty = toInteger(row.quantity);
