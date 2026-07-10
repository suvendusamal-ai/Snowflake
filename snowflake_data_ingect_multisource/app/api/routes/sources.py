from fastapi import APIRouter
from app.api.services.sqlserver_service import SQLServerService
from app.api.services.sqlite_service import SQLiteService

router = APIRouter()


# -------------------------------
# SQL SERVER
# -------------------------------
@router.get("/sqlserver/databases")
def sqlserver_databases():
    return SQLServerService.get_databases()   # ✅ FIXED


@router.get("/sqlserver/tables/{database}")
def sqlserver_tables(database: str):
    return SQLServerService.get_tables(database)


# -------------------------------
# SQLITE
# -------------------------------
@router.get("/sqlite/tables")
def sqlite_tables():
    return SQLiteService.get_tables()