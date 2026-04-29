# Snowflake Notebook Accelerator

## Setup
1. Install dependencies:
   pip install -r requirements.txt

2. Set environment variables (Windows PowerShell):
   setx SNOWFLAKE_USER admin
   setx SNOWFLAKE_PASSWORD your_password
   setx SNOWFLAKE_ACCOUNT KBQSGRQ-SFB22692
   setx SNOWFLAKE_WAREHOUSE COMPUTE_WH
   setx SNOWFLAKE_DATABASE DEMODB
   setx SNOWFLAKE_SCHEMA OI_ATLAS

3. Run:
   python src/main.py
