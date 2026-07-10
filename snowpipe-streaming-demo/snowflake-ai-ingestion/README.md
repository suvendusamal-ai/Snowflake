# Snowflake AI Ingestion Demo

## 🚀 Features
- FastAPI ingestion trigger
- LLM metadata simulation
- SQL Server extraction
- Snowflake Snowpipe loading

## ▶️ Run

### 1. Install dependencies
pip install -r requirements.txt

### 2. Start API
uvicorn app.main:app --reload

### 3. Call API
c

## 📊 Validate in Snowflake
SELECT * FROM sales;

### Practical execution Step

D:\Suvendu\snowflake-ai-ingestion>uvicorn app.main:app --reload
←[32mINFO←[0m:     Will watch for changes in these directories: ['D:\\Suvendu\\snowflake-ai-ingestion']

D:\Suvendu\snowflake-ai-ingestion>curl -X POST http://127.0.0.1:8000/ingest -H "Content-Type: application/json" -d "{\"prompt\":\"Load the data from customers table\"}"
{"results":[{"table":"Customers","status":"loaded"}]}
D:\Suvendu\snowflake-ai-ingestion>

