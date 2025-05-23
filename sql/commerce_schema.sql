-- commerce_schema.sql
-- Pure DDL for the Commerce‑Minorista benchmark (PostgreSQL 16)
-- No INSERTs, suitable for initializing an empty database.

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

-- Indices for queries & benchmarks
CREATE INDEX idx_sale_timestamp ON Sale(sale_timestamp);
CREATE INDEX idx_product_category ON Product(category_id);