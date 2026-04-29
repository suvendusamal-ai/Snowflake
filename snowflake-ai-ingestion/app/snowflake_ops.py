from jinja2 import Environment, FileSystemLoader
import yaml
import snowflake.connector

env = Environment(loader=FileSystemLoader("templates"))

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

def create_table(table):
    template = env.get_template("table.sql.jinja")

    sql = template.render(
        table=table,
        stage=config["snowflake"]["stage"]   # ✅ ADD THIS
    )

    conn = get_conn()
    cs = conn.cursor()
    cs.execute(sql)
    cs.close()
    conn.close()

def create_pipe(table):
    template = env.get_template("pipe.sql.jinja")
    sql = template.render(table=table, stage=config["snowflake"]["stage"])

    conn = get_conn()
    cs = conn.cursor()
    cs.execute(sql)
    cs.close()
    conn.close()

def trigger_pipe(table):
    conn = get_conn()
    cs = conn.cursor()
    cs.execute(f"ALTER PIPE {table}_pipe REFRESH")
    cs.close()
    conn.close()
