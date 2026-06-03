import sys
import os

# Fix import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.connection import get_session

session = get_session()

print("Running setup SQL...")

with open("sql/01_setup.sql", "r") as f:
    sql_script = f.read()

# 🔥 Split SQL by semicolon
statements = sql_script.split(";")

for stmt in statements:
    stmt = stmt.strip()
    if stmt:
        print(f"Executing: {stmt[:50]}...")
        session.sql(stmt).collect()

print("✅ Setup completed")