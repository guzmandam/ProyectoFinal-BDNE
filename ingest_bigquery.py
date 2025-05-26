from google.cloud import bigquery
from google.cloud import storage
from tqdm import tqdm

PROJECT   = "proyectofinalbdne"
DATASET   = "commerce_doc"
BUCKET    = "commerce-json-demo"
CAT_FILE  = "stores_catalog.ndjson"
SALE_FILE = "sales_docs.ndjson"

bq_client = bigquery.Client(project=PROJECT)
storage_client = storage.Client(project=PROJECT)

# 1️⃣ asegúrate de que exista el dataset
ds_ref = bigquery.DatasetReference(PROJECT, DATASET)
try:
    bq_client.get_dataset(ds_ref)
except Exception:
    bq_client.create_dataset(bigquery.Dataset(ds_ref), timeout=30)

# 2️⃣ esquema de destino (solo una muestra; ajusta si cambió tu JSON)
stores_schema = [
    bigquery.SchemaField("store_name", "STRING"),
    bigquery.SchemaField("address", "STRING"),
    bigquery.SchemaField("employees", "RECORD", mode="REPEATED", fields=[
        bigquery.SchemaField("first_name", "STRING"),
        bigquery.SchemaField("last_name",  "STRING"),
        bigquery.SchemaField("position",   "STRING"),
    ]),
    bigquery.SchemaField("inventory", "RECORD", mode="REPEATED", fields=[
        bigquery.SchemaField("product", "RECORD", fields=[
            bigquery.SchemaField("name",     "STRING"),
            bigquery.SchemaField("category", "STRING"),
            bigquery.SchemaField("price",    "NUMERIC")
        ]),
        bigquery.SchemaField("quantity", "INT64"),
    ]),
]

sales_schema = [
    bigquery.SchemaField("timestamp", "STRING"),   # we’ll parse in queries
    bigquery.SchemaField("store",   "RECORD", fields=[bigquery.SchemaField("name", "STRING")]),
    bigquery.SchemaField("employee","RECORD", fields=[
        bigquery.SchemaField("first_name","STRING"),
        bigquery.SchemaField("last_name", "STRING")
    ]),
    bigquery.SchemaField("customer","RECORD", fields=[
        bigquery.SchemaField("first_name","STRING"),
        bigquery.SchemaField("last_name", "STRING"),
        bigquery.SchemaField("email",     "STRING")
    ]),
    bigquery.SchemaField("lines","RECORD", mode="REPEATED", fields=[
        bigquery.SchemaField("product","RECORD", fields=[
            bigquery.SchemaField("name",    "STRING"),
            bigquery.SchemaField("category","STRING"),
            bigquery.SchemaField("price",   "NUMERIC")
        ]),
        bigquery.SchemaField("quantity",   "INT64"),
        bigquery.SchemaField("line_total", "NUMERIC")
    ]),
    bigquery.SchemaField("total_amount","NUMERIC"),
]

def load_ndjson(table_id, ndjson_path, schema):
    uri = f"gs://{BUCKET}/{ndjson_path}"

    job_cfg = bigquery.LoadJobConfig(
        source_format="NEWLINE_DELIMITED_JSON",
        schema=schema,
        write_disposition="WRITE_TRUNCATE",
        autodetect=not schema,
    )

    job = bq_client.load_table_from_uri(uri, table_id, job_config=job_cfg)
    job.result()

durations = []
# catálogo
durations.append(load_ndjson(f"{PROJECT}.{DATASET}.stores",
                            CAT_FILE,
                            schema=stores_schema))

# ventas    
durations.append(load_ndjson(f"{PROJECT}.{DATASET}.sales",
                            SALE_FILE,
                            schema=sales_schema))

print(f"Duraciones: {durations}")
