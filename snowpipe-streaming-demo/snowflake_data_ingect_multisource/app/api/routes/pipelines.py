from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.services.pipeline_generator import PipelineGenerator


router = APIRouter()


# -------------------------------
# REQUEST MODELS
# -------------------------------
class GenerateRequest(BaseModel):
    source_type: str
    database: str
    table: str


class DeployRequest(BaseModel):
    generated_sql: str
    table: str
    database: str   # 🔥 REQUIRED for SQL Server context switching


# -------------------------------
# GENERATE ENDPOINT
# -------------------------------
@router.post("/generate")
def generate(req: GenerateRequest):
    try:
        print("\n📥 GENERATE PAYLOAD:", req.dict())

        generated_sql = PipelineGenerator.generate(
            req.source_type,
            req.database,
            req.table
        )

        return {
            "generated_sql": generated_sql
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------
# DEPLOY ENDPOINT
# -------------------------------
@router.post("/deploy")
def deploy(req: DeployRequest):
    try:
        print("\n📥 DEPLOY PAYLOAD:", req.dict())

        result = PipelineGenerator.deploy(
            generated_sql=req.generated_sql,
            source_table=req.table,
            database=req.database   # 🔥 critical fix
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))