import pandas as pd
import pyodbc
import os
import yaml

with open("config/config.yaml") as f:
    config = yaml.safe_load(f)

def extract_data(table_name: str):
    conn = pyodbc.connect(config["sqlserver"]["connection_string"])
    
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql(query, conn)

    file_path = f"data/{table_name}.parquet"
    os.makedirs("data", exist_ok=True)

    df.to_parquet(file_path, index=False)
    return file_path