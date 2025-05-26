"""Configuration settings for the BigQuery dashboard."""

import os
from typing import Optional

# BigQuery Configuration
PROJECT_ID = "proyectofinalbdne"
DATASET_ID = "commerce_doc"
SALES_TABLE = "sales"
STORES_TABLE = "stores"

# Google Cloud Authentication
# Set this environment variable to your service account key file path
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Dashboard Configuration
DASHBOARD_TITLE = "Commerce Analytics Dashboard"
DEFAULT_DATE_RANGE_DAYS = 30
REFRESH_INTERVAL_SECONDS = 300  # 5 minutes

# Chart Configuration
CHART_HEIGHT = 400
CHART_COLORS = {
    "primary": "#3B82F6",
    "secondary": "#10B981", 
    "accent": "#8B5CF6",
    "warning": "#F59E0B",
    "danger": "#EF4444"
}

def get_table_id(table_name: str) -> str:
    """Get fully qualified table ID."""
    return f"{PROJECT_ID}.{DATASET_ID}.{table_name}"

def validate_config() -> bool:
    """Validate that required configuration is present."""
    if not GOOGLE_APPLICATION_CREDENTIALS:
        print("Warning: GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
        print("You may need to authenticate with Google Cloud")
        return False
    return True 