"""Administration Dashboard - Platform governance and monitoring."""

import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Administration", page_icon="⚙️", layout="wide")
st.title("⚙️ Administration & Monitoring")


def get_session():
    try:
        return get_active_session()
    except Exception:
        return st.connection("snowflake").session()


session = get_session()

tab1, tab2, tab3, tab4 = st.tabs([
    "Platform Overview", "Guardrail Violations", "Access Audit", "Data Lineage"
])

# ─── Platform Overview ───────────────────────────────────────────────────────
with tab1:
    st.markdown("### Platform Health")

    c1, c2, c3, c4 = st.columns(4)

    doc_count = session.sql("SELECT COUNT(*) AS C FROM RAW.DOCUMENT_REGISTRY").collect()[0]["C"]
    completed = session.sql(
        "SELECT COUNT(*) AS C FROM RAW.DOCUMENT_REGISTRY WHERE PROCESSING_STATUS = 'COMPLETED'"
    ).collect()[0]["C"]
    failed = session.sql(
        "SELECT COUNT(*) AS C FROM RAW.DOCUMENT_REGISTRY WHERE PROCESSING_STATUS = 'FAILED'"
    ).collect()[0]["C"]
    pending = session.sql(
        "SELECT COUNT(*) AS C FROM RAW.DOCUMENT_REGISTRY WHERE PROCESSING_STATUS = 'PENDING'"
    ).collect()[0]["C"]

    c1.metric("Total Documents", doc_count)
    c2.metric("Completed", completed)
    c3.metric("Failed", failed)
    c4.metric("Pending", pending)

    # Department breakdown
    st.markdown("### Documents by Department")
    dept_df = session.sql("""
        SELECT DEPARTMENT, PROCESSING_STATUS, COUNT(*) AS CNT
        FROM RAW.DOCUMENT_REGISTRY
        GROUP BY DEPARTMENT, PROCESSING_STATUS
        ORDER BY DEPARTMENT
    """).to_pandas()

    if not dept_df.empty:
        pivot = dept_df.pivot_table(index="DEPARTMENT", columns="PROCESSING_STATUS", values="CNT", fill_value=0)
        st.bar_chart(pivot)

    # Chunk distribution
    st.markdown("### Knowledge Distribution")
    chunk_df = session.sql("""
        SELECT DEPARTMENT, COUNT(*) AS CHUNKS, COUNT(DISTINCT DOCUMENT_ID) AS DOCS
        FROM KNOWLEDGE.DOCUMENT_CHUNKS
        GROUP BY DEPARTMENT
        ORDER BY CHUNKS DESC
    """).to_pandas()

    if not chunk_df.empty:
        st.dataframe(chunk_df, use_container_width=True, hide_index=True)

# ─── Guardrail Violations ────────────────────────────────────────────────────
with tab2:
    st.markdown("### Recent Guardrail Violations")

    violations = session.sql("""
        SELECT
            LOG_ID,
            VIOLATION_TYPE,
            USER_ID,
            VIOLATION_DETAILS,
            ACTION_TAKEN,
            CREATED_AT
        FROM GOVERNANCE.AI_GOVERNANCE_LOG
        WHERE EVENT_TYPE = 'GUARDRAIL_VIOLATION'
        ORDER BY CREATED_AT DESC
        LIMIT 50
    """).to_pandas()

    if not violations.empty:
        # Violation type distribution
        type_counts = violations["VIOLATION_TYPE"].value_counts()
        st.bar_chart(type_counts)
        st.dataframe(violations, use_container_width=True, hide_index=True)
    else:
        st.success("No guardrail violations recorded.")

# ─── Access Audit ────────────────────────────────────────────────────────────
with tab3:
    st.markdown("### Access Audit Log")

    audit_df = session.sql("""
        SELECT
            EVENT_TYPE,
            USER_ID,
            USER_ROLE,
            RESOURCE_TYPE,
            ACTION,
            DEPARTMENT,
            OUTCOME,
            CREATED_AT
        FROM GOVERNANCE.ACCESS_AUDIT_LOG
        ORDER BY CREATED_AT DESC
        LIMIT 100
    """).to_pandas()

    if not audit_df.empty:
        # Filter
        event_types = ["All"] + audit_df["EVENT_TYPE"].unique().tolist()
        selected_type = st.selectbox("Filter by Event Type", event_types)

        if selected_type != "All":
            audit_df = audit_df[audit_df["EVENT_TYPE"] == selected_type]

        st.dataframe(audit_df, use_container_width=True, hide_index=True)
    else:
        st.info("No audit events recorded yet.")

# ─── Data Lineage ────────────────────────────────────────────────────────────
with tab4:
    st.markdown("### Data Lineage")
    st.markdown("Document processing pipeline lineage:")

    lineage = session.sql("""
        SELECT SOURCE_OBJECT, TARGET_OBJECT, TRANSFORMATION_TYPE, DESCRIPTION
        FROM GOVERNANCE.DATA_LINEAGE
        ORDER BY CREATED_AT
    """).to_pandas()

    if not lineage.empty:
        st.dataframe(lineage, use_container_width=True, hide_index=True)

        # Visual lineage (text-based)
        st.markdown("### Pipeline Flow")
        st.code("""
DOCUMENT_REGISTRY (RAW)
    │ [AI_PARSE_DOCUMENT]
    ▼
PARSED_DOCUMENTS (PROCESSED)
    │ [CORTEX_COMPLETE]          │ [CORTEX_COMPLETE]
    ▼                             ▼
DOCUMENT_CLASSIFICATIONS     DOCUMENT_METADATA
    │
    ▼ [CHUNK_DOCUMENT_UDF]
DOCUMENT_CHUNKS (KNOWLEDGE)
    │ [EMBED_TEXT_1024]
    ▼
EMBEDDING (VECTOR 1024)
    │ [CORTEX_SEARCH]
    ▼
ENTERPRISE_KNOWLEDGE_SEARCH
    │
    ▼
KNOWLEDGE_CATALOG
        """)
    else:
        st.info("No lineage data available.")
