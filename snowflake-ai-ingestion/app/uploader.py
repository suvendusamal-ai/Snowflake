import snowflake.connector
import yaml

with open("config/config.yaml") as f:
    config = yaml.safe_load(f)

def get_conn():
    return snowflake.connector.connect(
        user=config["snowflake"]["user"],
        password=config["snowflake"]["password"],
        account=config["snowflake"]["account"],
        warehouse=config["snowflake"]["warehouse"],
        database=config["snowflake"]["database"],
        schema=config["snowflake"]["schema"]
    )

def upload_to_stage(file_path, table):
    conn = get_conn()
    cs = conn.cursor()

    stage = config["snowflake"]["stage"]

    cs.execute(f"PUT file://{file_path} @{stage}/{table}/ AUTO_COMPRESS=TRUE OVERWRITE=TRUE")


    
    cs.close()
    conn.close()
