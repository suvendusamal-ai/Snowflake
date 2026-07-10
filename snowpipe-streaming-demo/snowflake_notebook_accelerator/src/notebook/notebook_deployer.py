import os
from notebook.notebook_generator import get_notebook_json


def upload_notebook_to_stage(session):
    stage_name = "DEMODB.OI_ATLAS.MY_STAGE"

    # Create stage if not exists
    session.sql(f"CREATE STAGE IF NOT EXISTS {stage_name}").collect()

    # Create temporary notebook file
    notebook_json = get_notebook_json()

    temp_file = "temp_notebook.ipynb"
    with open(temp_file, "w") as f:
        f.write(notebook_json)

    # Upload to stage
    session.sql(f"""
        PUT file://{temp_file}
        @{stage_name}
        AUTO_COMPRESS=FALSE
        OVERWRITE=TRUE;
    """).collect()

    os.remove(temp_file)

    print("✅ Notebook uploaded to stage")


def create_notebook_from_stage(session):
    session.sql("""
        CREATE OR REPLACE NOTEBOOK DEMODB.OI_ATLAS.CUSTOMER_NB
        FROM '@DEMODB.OI_ATLAS.MY_STAGE'
        MAIN_FILE = 'temp_notebook.ipynb'
        QUERY_WAREHOUSE = COMPUTE_WH;
    """).collect()

    print("✅ Notebook created from stage")


def activate_notebook(session):
    session.sql("""
        ALTER NOTEBOOK DEMODB.OI_ATLAS.CUSTOMER_NB
        ADD LIVE VERSION FROM LAST;
    """).collect()

    print("🚀 Notebook LIVE version activated")