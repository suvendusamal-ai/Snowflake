from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.llm import get_metadata
from app.extractor import extract_data
from app.uploader import upload_to_stage
from app.snowflake_ops import create_pipe, trigger_pipe, create_table

app = FastAPI()


# ✅ Request model (recommended)
class IngestRequest(BaseModel):
    prompt: str


@app.post("/ingest")
def ingest(payload: IngestRequest):

    try:
        # 🔹 Step 1: Get metadata from LLM (Cortex)
        metadata = get_metadata(payload.prompt)

        if not metadata or "tables" not in metadata:
            raise ValueError("Invalid metadata returned from LLM")

        tables = metadata["tables"]

        if not tables:
            raise ValueError("No tables identified from prompt")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"LLM error: {str(e)}")

    results = []

    # 🔹 Step 2: Process each table
    for table in tables:
        try:
            print(f"🚀 Processing table: {table}")

            file_path = extract_data(table)

            if not file_path:
                raise Exception("No data extracted")

            upload_to_stage(file_path, table)

            create_table(table)
            create_pipe(table)
            trigger_pipe(table)

            results.append({
                "table": table,
                "status": "loaded"
            })

        except Exception as e:
            print(f"❌ Error for table {table}: {str(e)}")

            results.append({
                "table": table,
                "status": "failed",
                "error": str(e)
            })

    return {"results": results}
