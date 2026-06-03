import os
import pandas as pd
import pyodbc
from app.core.config import settings


class DataLoader:

    @staticmethod
    def extract_to_parquet(table_name: str) -> str:
        """
        Extracts data from SQL Server and writes to parquet file
        """

        print(f"Loading data from SQL Server: {table_name}")

        conn = pyodbc.connect(settings.sqlserver_conn)

        query = f"SELECT * FROM {table_name}"

        df = pd.read_sql(query, conn)

        conn.close()

        if df.empty:
            raise Exception(f"No data found in table: {table_name}")

        # Save parquet in project root
        file_name = f"{table_name}.parquet"
        file_path = os.path.join(os.getcwd(), file_name)

        df.to_parquet(file_path, index=False)

        print(f"Parquet file created: {file_path}")

        return file_path