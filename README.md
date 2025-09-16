# NL → SQL Chatbot (with synthetic data)

An end-to-end demo app that:
1) Translates natural language questions into SQL,
2) Executes the SQL against local datasets (SQLite),
3) Returns the answer in a chat-like UI (Streamlit).

It uses a **default language model hard-coded to `gpt-4`** via the OpenAI API,
with the option to run a simple rule-based fallback if no API key is supplied.

---

## Quickstart

```bash
# 1) Create & activate a virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2) Install deps
pip install -r requirements.txt

# 3) (Optional) Set your OpenAI key if you want LLM-powered NL→SQL
export OPENAI_API_KEY=sk-...   # Windows PowerShell: $env:OPENAI_API_KEY="sk-..."

# 4) Seed the SQLite database with synthetic data (generates app/data/sample.db)
python app/seed_data.py

# 5) Run the UI
streamlit run app/app.py
```

Then open the local URL Streamlit prints (usually http://localhost:8501).

> If you **don't** set an API key, the app will use a **rule-based** NL→SQL conversion
> that handles a handful of common question types about the included schema.

---

## Project layout

```
nl2sql-chatbot/
├─ app/
│  ├─ app.py             # Streamlit chat UI
│  ├─ nl2sql.py          # LLM prompt & rule-based fallback
│  ├─ db.py              # SQLite utilities
│  ├─ seed_data.py       # Synthetic data generator (creates data/sample.db)
│  ├─ config.py          # Centralized config (default model hard-coded)
│  └─ data/
│     └─ sample.db       # (created by seed_data.py)
├─ tests/
│  └─ test_nl2sql_rules.py
├─ requirements.txt
├─ Dockerfile
└─ README.md
```

---

## Example questions you can try

- "Show me the top 5 products by revenue."
- "How many orders did we get last month?"
- "List total revenue by month for 2024."
- "What are the top 3 customers by total spent?"
- "Which category has the highest average order value?"

---

## Notes

- This is a demo, not a security-hardened production system.
- The LLM prompt asks the model to output **only SQL** for safety.
- The app verifies/limits the SQL to a whitelist (SELECT-only) before execution.