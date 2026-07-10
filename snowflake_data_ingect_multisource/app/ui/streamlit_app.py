import streamlit as st
import requests

API_BASE = "http://127.0.0.1:8000"

st.title("Snowflake Pipeline Generator using Cortex")

# -------------------------
# SOURCE
# -------------------------
source_type = st.selectbox("Select Source", ["sqlserver", "sqlite"])

# -------------------------
# DATABASE
# -------------------------
dbs = requests.get(f"{API_BASE}/sources/{source_type}/databases").json()
database = st.selectbox("Select Database", dbs)

# -------------------------
# TABLE
# -------------------------
tables = requests.get(
    f"{API_BASE}/sources/{source_type}/tables/{database}"
).json()

table = st.selectbox("Select Table", tables)

# -------------------------
# GENERATE
# -------------------------
if st.button("Generate Pipeline"):

    payload = {
        "source_type": source_type,
        "database": database,
        "table": table
    }

    response = requests.post(
        f"{API_BASE}/pipelines/generate",
        json=payload
    )

    data = response.json()

    generated_sql = data.get("generated_sql")

    if not generated_sql:
        st.error(data)
    else:
        st.session_state["generated_sql"] = generated_sql
        st.session_state["table"] = table
        st.session_state["database"] = database   # 🔥 FIX

# -------------------------
# SHOW SQL
# -------------------------
if "generated_sql" in st.session_state:

    st.subheader("Generated Snowflake Execution DDL")
    st.code(st.session_state["generated_sql"], language="sql")

    # -------------------------
    # DEPLOY
    # -------------------------
    if st.button("Deploy to Snowflake"):

        deploy_payload = {
            "generated_sql": st.session_state["generated_sql"],
            "table": st.session_state["table"],
            "database": st.session_state["database"]   # 🔥 CRITICAL FIX
        }

        deploy_response = requests.post(
            f"{API_BASE}/pipelines/deploy",
            json=deploy_payload
        )

        deploy_data = deploy_response.json()

        if deploy_data.get("status") != "success":
            st.error(deploy_data)
        else:
            st.success("Pipeline deployed successfully")

            st.subheader(f"Snowflake Table: {deploy_data['table']}")

            preview = deploy_data.get("preview", [])

            if preview:
                st.dataframe(preview)
            else:
                st.warning("No data returned")