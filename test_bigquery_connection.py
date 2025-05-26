#!/usr/bin/env python3
"""
Test script to verify BigQuery connectivity and data availability.
Run this before starting the dashboard to ensure everything is working.
"""

from google.cloud import bigquery
import sys
import os

# Configuration
PROJECT = "proyectofinalbdne"
DATASET = "commerce_doc"

def test_authentication():
    """Test if we can authenticate with Google Cloud."""
    try:
        client = bigquery.Client(project=PROJECT)
        print("✅ Authentication successful")
        return client
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print("\nTroubleshooting:")
        print("1. Set GOOGLE_APPLICATION_CREDENTIALS environment variable")
        print("2. Or run: gcloud auth application-default login")
        return None

def test_dataset_access(client):
    """Test if we can access the dataset."""
    try:
        dataset_ref = client.dataset(DATASET, project=PROJECT)
        dataset = client.get_dataset(dataset_ref)
        print(f"✅ Dataset access successful: {dataset.dataset_id}")
        return True
    except Exception as e:
        print(f"❌ Dataset access failed: {e}")
        return False

def test_tables_access(client):
    """Test if we can access the required tables."""
    tables = ["sales", "stores"]
    success = True
    
    for table_name in tables:
        try:
            table_ref = client.dataset(DATASET, project=PROJECT).table(table_name)
            table = client.get_table(table_ref)
            print(f"✅ Table access successful: {table.table_id} ({table.num_rows} rows)")
        except Exception as e:
            print(f"❌ Table access failed for {table_name}: {e}")
            success = False
    
    return success

def test_sample_queries(client):
    """Test sample queries that the dashboard will use."""
    
    # Test sales data query
    sales_query = f"""
    SELECT 
        COUNT(*) as total_transactions,
        SUM(total_amount) as total_revenue
    FROM `{PROJECT}.{DATASET}.sales`
    LIMIT 1
    """
    
    try:
        result = client.query(sales_query).to_dataframe()
        if not result.empty:
            row = result.iloc[0]
            print(f"✅ Sales query successful: {row['total_transactions']} transactions, ${row['total_revenue']:,.2f} total revenue")
        else:
            print("⚠️  Sales query returned no data")
    except Exception as e:
        print(f"❌ Sales query failed: {e}")
        return False
    
    # Test stores data query
    stores_query = f"""
    SELECT 
        COUNT(*) as total_stores
    FROM `{PROJECT}.{DATASET}.stores`
    LIMIT 1
    """
    
    try:
        result = client.query(stores_query).to_dataframe()
        if not result.empty:
            row = result.iloc[0]
            print(f"✅ Stores query successful: {row['total_stores']} stores")
        else:
            print("⚠️  Stores query returned no data")
    except Exception as e:
        print(f"❌ Stores query failed: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("🔍 Testing BigQuery Connection for Commerce Dashboard")
    print("=" * 50)
    
    # Check environment
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print(f"📁 Service account key: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")
    else:
        print("📁 Using application default credentials")
    
    print()
    
    # Test authentication
    client = test_authentication()
    if not client:
        sys.exit(1)
    
    print()
    
    # Test dataset access
    if not test_dataset_access(client):
        sys.exit(1)
    
    print()
    
    # Test table access
    if not test_tables_access(client):
        sys.exit(1)
    
    print()
    
    # Test sample queries
    if not test_sample_queries(client):
        sys.exit(1)
    
    print()
    print("🎉 All tests passed! Your dashboard should work correctly.")
    print("\nNext steps:")
    print("1. cd pablito")
    print("2. reflex run")
    print("3. Open http://localhost:3000")

if __name__ == "__main__":
    main() 