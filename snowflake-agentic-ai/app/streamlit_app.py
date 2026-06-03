import sys
import os

# Ensure src is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from snowflake.snowpark import Session

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(
    page_title="Snowflake Agent Demo",
    layout="wide"
)

st.title("🏦 Snowflake Agent Demo")

# -------------------------
# CONNECTION SECTION
# -------------------------
st.subheader("🔐 Connect to Snowflake")

with st.form("connection_form"):
    col1, col2 = st.columns(2)

    with col1:
        account = st.text_input("Account", value="zhb88243.us-east-1")
        user = st.text_input("User", value="SUVENDU")
        password = st.text_input("Password", type="password")

    with col2:
        role = st.text_input("Role", value="ACCOUNTADMIN")
        warehouse = st.text_input("Warehouse", value="COMPUTE_WH")
        database = st.text_input("Database", value="AGENTIC_DB")
        schema = st.text_input("Schema", value="BANKING")

    connect_btn = st.form_submit_button("Connect")

# -------------------------
# CONNECTION LOGIC
# -------------------------
if connect_btn:

    try:
        connection_parameters = {
            "account": account,
            "user": user,
            "password": password,
            "role": role,
            "warehouse": warehouse,
            "database": database,
            "schema": schema,
        }

        session = Session.builder.configs(connection_parameters).create()
        st.session_state["session"] = session

        st.success("✅ Connected to Snowflake")

    except Exception as e:
        st.error(f"❌ Connection failed: {e}")

# -------------------------
# AGENT SECTION
# -------------------------
if "session" in st.session_state:

    session = st.session_state["session"]

    st.divider()
    st.subheader("🤖 Agent Query")

    prompt = st.text_area(
        "Ask a question",
        placeholder="e.g., What is the average transaction amount?"
    )

    run_clicked = st.button("Run Agent")

    if run_clicked:

        if not prompt.strip():
            st.warning("⚠️ Please enter a question")
        else:
            from src.orchestrator import orchestrate

            try:
                # -------------------------
                # STATUS / PROGRESS UI
                # -------------------------
                with st.status("⏳ Agent is thinking...", expanded=True) as status:

                    status.write("🧠 Understanding the question...")
                    status.write("🔍 Planning and selecting tools...")
                    status.write("⚙️ Executing request via Snowflake Agent...")

                    result = orchestrate(session, prompt)

                    status.write("📊 Formatting response...")
                    status.update(label="✅ Completed", state="complete")

                # -------------------------
                # OUTPUT SECTION
                # -------------------------
                st.markdown("### 📊 Agent Output")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**🧠 Intent**")
                    st.info(result.get("intent", "N/A"))

                with col2:
                    st.markdown("**🔧 Tool Used**")
                    st.info(result.get("tool", "N/A"))

                # -------------------------
                # TRACE (Expandable)
                # -------------------------
                with st.expander("🔍 Agent Trace (Debug View)", expanded=False):
                    for step in result.get("trace", []):
                        st.write(f"- {step}")

                # -------------------------
                # FINAL RESPONSE (CLEAN)
                # -------------------------
                st.markdown("### 💡 Response")
                st.success(result.get("response", "No response generated"))

            except Exception as e:
                st.error(f"❌ Agent execution failed: {e}")

# -------------------------
# FOOTER
# -------------------------
st.divider()
st.caption("Agentic AI Demo | Snowflake Cortex + Analyst + Search + Tools")