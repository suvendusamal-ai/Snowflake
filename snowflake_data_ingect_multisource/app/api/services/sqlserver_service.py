import pyodbc
from app.core.config import settings


class SQLServerService:

    # -----------------------------------
    # GET CONNECTION (🔥 REQUIRED FIX)
    # -----------------------------------
    @staticmethod
    def get_connection():
        try:
            conn = pyodbc.connect(settings.sqlserver_conn)
            return conn
        except Exception as e:
            raise Exception(f"SQL Server connection failed: {str(e)}")

    # -----------------------------------
    # GET DATABASES
    # -----------------------------------
    @staticmethod
    def get_databases():
        conn = SQLServerService.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT name FROM sys.databases WHERE database_id > 4")
            return [row[0] for row in cursor.fetchall()]
        finally:
            cursor.close()
            conn.close()

    # -----------------------------------
    # GET TABLES
    # -----------------------------------
    @staticmethod
    def get_tables(database):
        conn = SQLServerService.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(f"USE {database}")

            cursor.execute("""
                SELECT TABLE_SCHEMA, TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
            """)

            return [f"{row[0]}.{row[1]}" for row in cursor.fetchall()]

        finally:
            cursor.close()
            conn.close()