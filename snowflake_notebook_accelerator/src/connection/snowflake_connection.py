from snowflake.snowpark import Session


def create_session():
    connection_parameters = {
        "account": "KBQSGRQ-SFB22692",   # use lowercase if needed
        "user": "admin",
        "password": "H@ppyN3wY3ar2026",
        "warehouse": "COMPUTE_WH",
        "database": "DEMODB",
        "schema": "OI_ATLAS",
        "role": "ACCOUNTADMIN"
    }

    session = Session.builder.configs(connection_parameters).create()
    print("✅ Connected to Snowflake successfully")

    return session