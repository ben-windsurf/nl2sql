import os
import streamlit as st
import pandas as pd

from config import DB_PATH, DEFAULT_OPENAI_MODEL
from nl2sql import natural_language_to_sql
from db import run_readonly_sql, get_schema_ddl
from utils import format_dataframe_currency

st.set_page_config(page_title="NL→SQL Chatbot", page_icon="🗄️", layout="wide")

st.title("🗄️ Natural Language → SQL Chatbot")
st.caption("Ask about your data in plain English. The app converts it to SQL (SQLite), runs it, and shows the results.")

# Sidebar
with st.sidebar:
    st.subheader("Settings")
    use_llm = st.toggle("Use OpenAI (gpt-4)", value=True)
    api_key = None
    if use_llm:
        api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
        st.write(f"Model: `{DEFAULT_OPENAI_MODEL}` (hard-coded)")
    st.divider()
    if st.button("Show schema"):
        schema = get_schema_ddl()
        st.json(schema)
    st.divider()
    st.caption(f"DB path: `{DB_PATH}`")

# Chat box
if "history" not in st.session_state:
    st.session_state["history"] = []

for msg in st.session_state["history"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

question = st.chat_input("Ask a question about the data...")

if question:
    st.session_state["history"].append({"role": "user", "content": question})
    with st.chat_message("assistant"):
        # Convert NL → SQL
        sql = natural_language_to_sql(question, api_key=api_key if use_llm else None)
        st.code(sql, language="sql")
        try:
            df = run_readonly_sql(sql)
            # Format financial columns as USD currency
            formatted_df = format_dataframe_currency(df)
            st.dataframe(formatted_df, use_container_width=True)
            # Use original df for CSV download to preserve raw numeric values
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download results (CSV)", csv, file_name="results.csv", mime="text/csv")
        except Exception as e:
            st.error(f"Error running SQL: {e}")
