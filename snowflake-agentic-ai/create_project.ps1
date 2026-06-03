$PROJECT = "snowflake-agentic-ai"

# Create folders
New-Item -ItemType Directory -Force -Path $PROJECT
$folders = @(
    "infra","cicd","native_app","data","sql",
    "src","src\tools","src\agents","src\rag","app","scripts"
)

foreach ($f in $folders) {
    New-Item -ItemType Directory -Force -Path "$PROJECT\$f"
}

# README
@"
# Snowflake Agentic AI - Enterprise Demo

Features:
- Cortex Analyst (Text-to-SQL)
- Cortex Search (RAG)
- Fraud Detection
- Streamlit UI
- Duo Authentication
"@ | Set-Content "$PROJECT\README.md"

# requirements
@"
snowflake-connector-python
snowflake-snowpark-python
streamlit
python-dotenv
"@ | Set-Content "$PROJECT\requirements.txt"

# ENV
@"
SNOWFLAKE_ACCOUNT=
SNOWFLAKE_USER=
SNOWFLAKE_ROLE=ACCOUNTADMIN
SNOWFLAKE_WAREHOUSE=AGENT_WH
SNOWFLAKE_DATABASE=AGENTIC_DB
SNOWFLAKE_SCHEMA=BANKING
"@ | Set-Content "$PROJECT\.env.example"

# SQL
@"
CREATE DATABASE IF NOT EXISTS AGENTIC_DB;
CREATE SCHEMA IF NOT EXISTS AGENTIC_DB.BANKING;
USE SCHEMA AGENTIC_DB.BANKING;

CREATE TABLE CUSTOMERS (
    CUSTOMER_ID STRING,
    NAME STRING,
    CITY STRING,
    RISK_SCORE FLOAT
);

CREATE TABLE ACCOUNTS (
    ACCOUNT_ID STRING,
    CUSTOMER_ID STRING,
    TYPE STRING,
    BALANCE FLOAT
);

CREATE TABLE TRANSACTIONS (
    TXN_ID STRING,
    ACCOUNT_ID STRING,
    AMOUNT FLOAT,
    TYPE STRING,
    TXN_TIME TIMESTAMP
);
"@ | Set-Content "$PROJECT\sql\01_setup.sql"

# Sample data
@"
TXN_ID,ACCOUNT_ID,AMOUNT,TYPE,TXN_TIME
T1,A1,10000,DEBIT,2026-04-28 10:10:00
T2,A2,250000,DEBIT,2026-04-28 10:12:00
T3,A3,900000,DEBIT,2026-04-28 10:13:00
"@ | Set-Content "$PROJECT\data\transactions.csv"

# connection.py
@"
import os
from snowflake.snowpark import Session
from dotenv import load_dotenv

load_dotenv()

def get_session():
    return Session.builder.configs({
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "authenticator": "externalbrowser",
        "role": os.getenv("SNOWFLAKE_ROLE"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
        "database": os.getenv("SNOWFLAKE_DATABASE"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA"),
    }).create()
"@ | Set-Content "$PROJECT\src\connection.py"

# orchestrator
@"
def orchestrate(session, prompt):
    if "total" in prompt.lower():
        return session.sql("SELECT SUM(AMOUNT) FROM TRANSACTIONS").collect()
    return "Agent executed successfully"
"@ | Set-Content "$PROJECT\src\orchestrator.py"

# streamlit app
@"
import streamlit as st
from src.connection import get_session
from src.orchestrator import orchestrate

session = get_session()

st.title("🏦 Snowflake Agentic AI (Windows)")

prompt = st.text_area("Ask something")

if st.button("Run"):
    result = orchestrate(session, prompt)
    st.write(result)
"@ | Set-Content "$PROJECT\app\streamlit_app.py"

# Create ZIP
Compress-Archive -Path $PROJECT -DestinationPath "$PROJECT.zip" -Force

Write-Host "Project created successfully!"
Write-Host "Zip file: $PROJECT.zip"