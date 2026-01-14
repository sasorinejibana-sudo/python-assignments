import json
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from typing import Tuple


import pyodbc
import ijson

JSON_PATH = r"C:\python\assignment1\.venv\ransomware_overview.json"

SQL_CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost\\SQLEXPRESS;"
    "DATABASE=RansomwareDB;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

BATCH_SIZE = 1000

INSERT_SQL = """
INSERT INTO dbo.RansomwareOverview
(
    CanonicalName, NameJson, Extensions, ExtensionPattern, RansomNoteFilenames,
    Comment, EncryptionAlgorithm, Decryptor, ResourcesJson, Screenshots,
    MicrosoftDetectionName, MicrosoftInfo, Sandbox, Iocs, Snort, RawJson
)
SELECT
    ?, ?, ?, ?, ?,
    ?, ?, ?, ?, ?,
    ?, ?, ?, ?, ?, ?
WHERE NOT EXISTS
(
    SELECT 1 FROM dbo.RansomwareOverview WITH (UPDLOCK, HOLDLOCK)
    WHERE CanonicalName = ?
);
"""

@dataclass
class Counters:
    parsed: int = 0
    inserted: int = 0
    duplicates: int = 0
    failed: int = 0

def norm_str(v: Any) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, str):
        s = v.strip()
        return s if s != "" else None
    return str(v).strip() or None

def json_text(v: Any) -> Optional[str]:
    if v is None:
        return None
    return json.dumps(v, ensure_ascii=False)

def get_canonical_name(item: Dict[str, Any]) -> str:
    """
    Your sample has: "name": [".CryptoHasYou."]
    Sometimes it might be a string; handle both.
    """
    n = item.get("name")
    if isinstance(n, list) and len(n) > 0:
        first = norm_str(n[0])
        return first if first else "UNKNOWN"
    if isinstance(n, str):
        first = norm_str(n)
        return first if first else "UNKNOWN"
    return "UNKNOWN"

def map_row(item: Dict[str, Any]) -> List[Any]:
    canonical = get_canonical_name(item)

    row = [
        canonical,
        json_text(item.get("name")),
        norm_str(item.get("extensions")),
        norm_str(item.get("extensionPattern")),
        norm_str(item.get("ransomNoteFilenames")),
        norm_str(item.get("comment")),
        norm_str(item.get("encryptionAlgorithm")),
        norm_str(item.get("decryptor")),
        json_text(item.get("resources")),
        norm_str(item.get("screenshots")),
        norm_str(item.get("microsoftDetectionName")),
        norm_str(item.get("microsoftInfo")),
        norm_str(item.get("sandbox")),
        norm_str(item.get("iocs")),
        norm_str(item.get("snort")),
        json.dumps(item, ensure_ascii=False),  # RawJson
        canonical  # for NOT EXISTS check
    ]
    return row

def flush_batch(cur, cn, batch: List[List[Any]]) -> Tuple[int, int]:
    before = get_count(cur)
    cur.fast_executemany = True
    cur.executemany(INSERT_SQL, batch)
    cn.commit()
    after = get_count(cur)
    inserted = after - before
    duplicates = len(batch) - inserted
    return inserted, duplicates

def get_count(cur) -> int:
    cur.execute("SELECT COUNT(*) FROM dbo.RansomwareOverview;")
    return int(cur.fetchone()[0])

def main():
    counters = Counters()
    start = time.time()

    cn = pyodbc.connect(SQL_CONN_STR)
    cn.autocommit = False
    cur = cn.cursor()

    batch: List[List[Any]] = []

    try:
        with open(JSON_PATH, "rb") as f:
            for item in ijson.items(f, "item"):
                counters.parsed += 1
                try:
                    batch.append(map_row(item))
                except Exception:
                    counters.failed += 1
                    continue

                if len(batch) >= BATCH_SIZE:
                    ins, dup = flush_batch(cur, cn, batch)
                    counters.inserted += ins
                    counters.duplicates += dup
                    batch.clear()

        if batch:
            ins, dup = flush_batch(cur, cn, batch)
            counters.inserted += ins
            counters.duplicates += dup
            batch.clear()

    finally:
        cur.close()
        cn.close()

    elapsed = time.time() - start
    print("=== INGESTION RESULTS ===")
    print(f"Parsed:     {counters.parsed}")
    print(f"Inserted:   {counters.inserted}")
    print(f"Duplicates: {counters.duplicates}")
    print(f"Failed:     {counters.failed}")
    print(f"Elapsed:    {elapsed:.2f}s")
    print("Invariant check:", counters.parsed == (counters.inserted + counters.duplicates + counters.failed))

if __name__ == "__main__":
    main()
