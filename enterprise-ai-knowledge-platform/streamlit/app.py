"""Enterprise AI Knowledge Platform - Streamlit Application."""

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Enterprise AI Knowledge Platform",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        border-left: 4px solid #0066cc;
    }
    .stChatMessage {
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)


def get_snowflake_session():
    """Get Snowflake session from Streamlit connection."""
    from snowflake.snowpark.context import get_active_session
    try:
        return get_active_session()
    except Exception:
        # Fallback for local development
        connection = st.connection("snowflake")
        return connection.session()


def main():
    """Main application entry point."""
    # Sidebar navigation
    with st.sidebar:
        st.image("https://www.snowflake.com/wp-content/themes/flavor/assets/img/logo.svg", width=150)
        st.markdown("---")
        st.markdown("### Enterprise AI Knowledge Platform")
        st.markdown("Powered by Snowflake Cortex AI")
        st.markdown("---")

        # User context
        session = get_snowflake_session()
        current_role = session.sql("SELECT CURRENT_ROLE() AS ROLE").collect()[0]["ROLE"]
        current_user = session.sql("SELECT CURRENT_USER() AS USR").collect()[0]["USR"]

        st.markdown(f"**User:** {current_user}")
        st.markdown(f"**Role:** {current_role}")
        st.markdown("---")

        # Department filter
        department = st.selectbox(
            "Department Filter",
            ["All Departments", "finance", "treasury", "procurement", "risk",
             "compliance", "audit", "hr", "legal", "operations"],
            index=0,
        )
        if department == "All Departments":
            department = None

        st.session_state["department"] = department
        st.session_state["user"] = current_user
        st.session_state["role"] = current_role

    # Main content area - landing page
    st.markdown('<p class="main-header">Enterprise AI Knowledge Platform</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-powered enterprise knowledge management with Snowflake Cortex</p>', unsafe_allow_html=True)

    # Quick stats
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        doc_count = session.sql(
            "SELECT COUNT(*) AS C FROM RAW.DOCUMENT_REGISTRY"
        ).collect()[0]["C"]
        st.metric("Total Documents", f"{doc_count:,}")

    with col2:
        chunk_count = session.sql(
            "SELECT COUNT(*) AS C FROM KNOWLEDGE.DOCUMENT_CHUNKS"
        ).collect()[0]["C"]
        st.metric("Knowledge Chunks", f"{chunk_count:,}")

    with col3:
        conv_count = session.sql(
            "SELECT COUNT(*) AS C FROM AGENT.CONVERSATIONS WHERE STATUS = 'ACTIVE'"
        ).collect()[0]["C"]
        st.metric("Active Conversations", f"{conv_count:,}")

    with col4:
        dept_count = session.sql(
            "SELECT COUNT(DISTINCT DEPARTMENT) AS C FROM KNOWLEDGE.DOCUMENT_CHUNKS"
        ).collect()[0]["C"]
        st.metric("Departments", dept_count)

    st.markdown("---")

    # Quick actions
    st.markdown("### Quick Actions")
    action_col1, action_col2, action_col3 = st.columns(3)

    with action_col1:
        if st.button("💬 Start AI Chat", use_container_width=True):
            st.switch_page("pages/1_AI_Chat.py")
    with action_col2:
        if st.button("📄 Upload Documents", use_container_width=True):
            st.switch_page("pages/2_Document_Upload.py")
    with action_col3:
        if st.button("🔍 Search Knowledge", use_container_width=True):
            st.switch_page("pages/3_Knowledge_Explorer.py")

    # Recent activity
    st.markdown("### Recent Activity")
    recent_docs = session.sql("""
        SELECT FILE_NAME, DEPARTMENT, PROCESSING_STATUS, UPLOAD_TIMESTAMP
        FROM RAW.DOCUMENT_REGISTRY
        ORDER BY UPLOAD_TIMESTAMP DESC
        LIMIT 10
    """).to_pandas()

    if not recent_docs.empty:
        st.dataframe(recent_docs, use_container_width=True, hide_index=True)
    else:
        st.info("No documents uploaded yet. Start by uploading documents to get started.")


if __name__ == "__main__":
    main()
