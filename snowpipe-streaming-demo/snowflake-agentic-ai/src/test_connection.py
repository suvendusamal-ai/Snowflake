from snowflake.snowpark import Session
import getpass
import warnings

warnings.filterwarnings(
    "ignore",
    message="Bad owner or permissions on.*config.toml"
)

print("====================================")
print("Starting Snowflake connection test...")
print("====================================")

print("Connecting using password + Duo...")
password = getpass.getpass("Enter Snowflake password: ")

try:
    connection_parameters = {
        "account": "zhb88243.us-east-1",
        "user": "SUVENDU",
#        "password": "DataCloudW0rld@2025",   # 🔴 ENTER PASSWORD HERE
        "password": password,
        "role": "SNOWFLAKE_INTELLIGENCE_ADMIN",
        "warehouse": "COMPUTE_WH",
    }

    

    session = Session.builder.configs(connection_parameters).create()

    print("✅ Connected successfully!")

    result = session.sql(
        "SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_ACCOUNT()"
    ).collect()

    print(result)

except Exception as e:
    print("❌ ERROR OCCURRED:")
    print(type(e).__name__)
    print(e)