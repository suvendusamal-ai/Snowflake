import snowflake.connector
from app.core.config import settings


class SnowflakeService:

    # -----------------------------------
    # GET CONNECTION
    # -----------------------------------
    @staticmethod
    def get_connection():
        return snowflake.connector.connect(
            user=settings.snowflake_user,
            password=settings.snowflake_password,
            account=settings.snowflake_account,
            warehouse=settings.snowflake_warehouse,
            database=settings.snowflake_database,
            schema=settings.snowflake_schema
        )

    # -----------------------------------
    # EXECUTE MULTI-STATEMENT SQL
    # -----------------------------------
    @staticmethod
    def execute(sql_text: str):
        conn = SnowflakeService.get_connection()
        cur = conn.cursor()

        try:
            # Split multiple SQL statements safely
            statements = [s.strip() for s in sql_text.split(";") if s.strip()]

            for stmt in statements:
                print("\nExecuting:\n", stmt)
                cur.execute(stmt)

        finally:
            cur.close()
            conn.close()

    # -----------------------------------
    # EXECUTE SINGLE STATEMENT
    # -----------------------------------
    @staticmethod
    def execute_single(query: str):
        conn = SnowflakeService.get_connection()
        cur = conn.cursor()

        try:
            print("\nExecuting:\n", query)
            cur.execute(query)
        finally:
            cur.close()
            conn.close()

    # -----------------------------------
    # FETCH DATA (FOR PREVIEW)
    # -----------------------------------
    @staticmethod
    def fetch_all(query: str):
        conn = SnowflakeService.get_connection()
        cur = conn.cursor()

        try:
            print("\nFetching:\n", query)
            cur.execute(query)

            columns = [col[0] for col in cur.description]
            rows = cur.fetchall()

            return [dict(zip(columns, row)) for row in rows]

        finally:
            cur.close()
            conn.close()