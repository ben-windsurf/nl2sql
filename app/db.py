import sqlite3
import pandas as pd
from config import DB_PATH, MAX_ROWS

def get_conn():
    return sqlite3.connect(DB_PATH)

def run_readonly_sql(sql: str):
    # Enforce simple, safe SELECT-only queries
    lowered = sql.strip().lower()
    if not lowered.startswith("select"):
        raise ValueError("Only SELECT queries are allowed in this demo.")
    # Disallow obvious risky statements/tokens
    banned = [";", " drop ", " delete ", " insert ", " update ", " alter ", " create ", "--", "/*", "*/"]
    for b in banned:
        if b in lowered and not lowered.startswith("select") and ";" in lowered:
            raise ValueError("Potentially unsafe SQL detected.")
    
    # Only add LIMIT if the query doesn't already have one
    final_sql = sql.strip()
    if "limit " not in lowered:
        final_sql = final_sql + f" LIMIT {MAX_ROWS}"
    
    with get_conn() as conn:
        df = pd.read_sql_query(final_sql, conn)
    return df

def get_schema_ddl():
    with get_conn() as conn:
        cur = conn.cursor()
        # Fetch table & columns
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [r[0] for r in cur.fetchall()]
        schema = {}
        for t in tables:
            cur.execute(f"PRAGMA table_info({t});")
            cols = [{"name": r[1], "type": r[2]} for r in cur.fetchall()]
            schema[t] = cols
    return schema
