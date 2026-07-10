import sqlite3
from app.core.config import settings


class SQLiteService:

    @staticmethod
    def connection():
        return sqlite3.connect(settings.sqlite_path)


    @staticmethod
    def tables():

        conn=SQLiteService.connection()
        cur=conn.cursor()

        try:
            cur.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type='table'
                ORDER BY name
            """)

            return [r[0] for r in cur.fetchall()]

        finally:
            cur.close()
            conn.close()


    @staticmethod
    def schema_metadata(table_name):

        conn=SQLiteService.connection()
        cur=conn.cursor()

        try:
            cur.execute(
                f"PRAGMA table_info('{table_name}')"
            )

            rows=cur.fetchall()

            return [
                {
                    "column":r[1],
                    "type":r[2]
                }
                for r in rows
            ]

        finally:
            cur.close()
            conn.close()