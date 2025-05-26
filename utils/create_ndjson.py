from pathlib import Path
import json

def make_ndjson(src_path: Path, dst_path: Path, fix_date=False):
    """
    Convert array-json → ndjson. If `fix_date` is True, replace
    {"$date":"…Z"} with simple ISO string (YYYY-MM-DDTHH:MM:SS).
    """
    objs = json.loads(src_path.read_text())
    with dst_path.open("w", encoding="utf-8") as out:
        for obj in objs:
            if fix_date:
                # guaranteed one field path: obj["timestamp"]["$date"]
                iso = obj["timestamp"]["$date"].replace("Z", "")
                obj["timestamp"] = iso                 # flat string
            out.write(json.dumps(obj, ensure_ascii=False) + "\n")

SALES_FILE_ND = Path("./json/sales_docs.ndjson")
STORES_FILE_ND = Path("./json/stores_catalog.ndjson")

make_ndjson(Path("./json/sales_docs.json"), SALES_FILE_ND, fix_date=True)    # fix $date
make_ndjson(Path("./json/stores_catalog.json"), STORES_FILE_ND)                 # no date fix






