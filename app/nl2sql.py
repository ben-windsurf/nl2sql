import os
import re
import datetime as dt
from typing import Optional

import pandas as pd

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

from config import DEFAULT_OPENAI_MODEL
from db import get_schema_ddl

SYSTEM_PROMPT = """You are a helpful assistant that converts natural language questions into **SQLite SQL**.
- Output **ONLY** a valid SQL query, with no prose, backticks, or explanations.
- The database is SQLite.
- Use only the tables and columns provided.
- Prefer simple SELECT statements.
- LIMIT results if not specified.
"""

def _format_schema_for_prompt(schema: dict) -> str:
    lines = []
    for table, cols in schema.items():
        cols_str = ", ".join([f"{c['name']} ({c['type']})" for c in cols])
        lines.append(f"- {table}: {cols_str}")
    return "\n".join(lines)

def llm_to_sql(nl: str, schema: dict, api_key: Optional[str]) -> Optional[str]:
    """Return SQL from LLM if possible, else None."""
    if api_key is None or OpenAI is None:
        return None

    client = OpenAI(api_key=api_key)
    schema_text = _format_schema_for_prompt(schema)
    user_prompt = f"""Schema:
{schema_text}

Question: {nl}

Return ONLY SQL. SQLite dialect.
"""
    try:
        resp = client.chat.completions.create(
            model=DEFAULT_OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
        )
        sql = resp.choices[0].message.content.strip()
        # Strip any accidental markdown fences/backticks
        sql = re.sub(r"^```sql\s*|\s*```$", "", sql, flags=re.IGNORECASE)
        return sql
    except Exception as e:
        # Fallback to rules
        return None

def _month_bounds(year:int, month:int):
    import calendar
    start = dt.date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end = dt.date(year, month, last_day)
    return start.isoformat(), end.isoformat()

def rule_based(nl: str, schema: dict) -> str:
    """A tiny rule-based NL→SQL to keep the demo usable without an API key."""
    nl_l = nl.lower()

    # Simple templates grounded in our known schema (customers, orders, order_items, products)
    if "top" in nl_l and "products" in nl_l and ("revenue" in nl_l or "sales" in nl_l):
        m = re.search(r"top\s+(\d+)", nl_l)
        k = int(m.group(1)) if m else 5
        return f"""
SELECT p.product_id, p.name AS product_name, p.category, SUM(oi.quantity * oi.unit_price) AS revenue
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
GROUP BY p.product_id, p.name, p.category
ORDER BY revenue DESC
LIMIT {k}
""".strip()

    if "how many orders" in nl_l and ("last month" in nl_l or "previous month" in nl_l):
        today = dt.date.today()
        prev_month = today.month - 1 or 12
        year = today.year if today.month != 1 else today.year - 1
        start, end = _month_bounds(year, prev_month)
        return f"""
SELECT COUNT(*) AS orders_last_month
FROM orders
WHERE order_date BETWEEN '{start}' AND '{end}'
""".strip()

    if "total revenue by month" in nl_l or ("revenue by month" in nl_l):
        # default to current year if not specified
        m = re.search(r"(\d{4})", nl_l)
        year = int(m.group(1)) if m else dt.date.today().year
        return f"""
SELECT strftime('%Y-%m', o.order_date) AS ym,
       SUM(oi.quantity * oi.unit_price) AS revenue
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE strftime('%Y', o.order_date) = '{year}'
GROUP BY ym
ORDER BY ym ASC
""".strip()

    if "top" in nl_l and "customers" in nl_l and ("spent" in nl_l or "revenue" in nl_l or "sales" in nl_l):
        m = re.search(r"top\s+(\d+)", nl_l)
        k = int(m.group(1)) if m else 5
        return f"""
SELECT c.customer_id, c.first_name || ' ' || c.last_name AS customer, SUM(oi.quantity * oi.unit_price) AS total_spent
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id
JOIN order_items oi ON oi.order_id = o.order_id
GROUP BY c.customer_id, customer
ORDER BY total_spent DESC
LIMIT {k}
""".strip()

    if ("category" in nl_l) and ("highest" in nl_l or "best" in nl_l) and ("average order value" in nl_l or "aov" in nl_l):
        return f"""
WITH order_totals AS (
  SELECT o.order_id, SUM(oi.quantity * oi.unit_price) AS order_total
  FROM orders o
  JOIN order_items oi ON oi.order_id = o.order_id
  GROUP BY o.order_id
),
order_category AS (
  SELECT o.order_id, MAX(p.category) AS category -- crude: dominant category per order
  FROM orders o
  JOIN order_items oi ON oi.order_id = o.order_id
  JOIN products p ON p.product_id = oi.product_id
  GROUP BY o.order_id
)
SELECT oc.category, AVG(ot.order_total) AS avg_order_value
FROM order_totals ot
JOIN order_category oc ON oc.order_id = ot.order_id
GROUP BY oc.category
ORDER BY avg_order_value DESC
LIMIT 5
""".strip()

    # Generic fallback: simple search across table names
    if "customers" in nl_l and "count" in nl_l:
        return "SELECT COUNT(*) AS customer_count FROM customers"
    if "orders" in nl_l and "count" in nl_l:
        return "SELECT COUNT(*) AS order_count FROM orders"
    if "products" in nl_l and "count" in nl_l:
        return "SELECT COUNT(*) AS product_count FROM products"

    # Last-resort minimal default
    return "SELECT 1 AS result;"

def natural_language_to_sql(nl: str, api_key: Optional[str]) -> str:
    schema = get_schema_ddl()
    # Try LLM first if available
    sql = llm_to_sql(nl, schema, api_key)
    if sql:
        return sql
    # Otherwise fallback to rules
    return rule_based(nl, schema)
