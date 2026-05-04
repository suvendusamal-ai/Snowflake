import os
import getpass
from snowflake.snowpark import Session
from dotenv import load_dotenv

# ✅ Correct way
load_dotenv()

def get_session():

    print("🔐 Enter Snowflake password (Duo will trigger)...")
    password = getpass.getpass()

    print("ACCOUNT:", os.getenv("SNOWFLAKE_ACCOUNT"))  # debug

    connection_parameters = {
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "password": password,
        "role": os.getenv("SNOWFLAKE_ROLE"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
        "database": os.getenv("SNOWFLAKE_DATABASE"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA"),
    }

    return Session.builder.configs(connection_parameters).create()