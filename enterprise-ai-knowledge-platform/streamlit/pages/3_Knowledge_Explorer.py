"""Knowledge Explorer - Browse and search the knowledge catalog."""

import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Knowledge Explorer", page_icon="🔍", layout="wide")
st.title("🔍 Knowledge Explorer")


def get_session():
    try:
        return get_active_session()
    except Exception:
        return st.connection("snowflake").session()


session = get_session()

# Search bar
search_query = st.text_input(
    "Search the knowledge base",
    placeholder="Enter a question or keywords...",
)

col1, col2, col3 = st.columns(3)
with col1:
    dept_filter = st.selectbox(
        "Department", ["All"] + ["finance", "treasury", "procurement", "risk",
                                  "compliance", "audit", "hr", "legal", "operations"]
    )
with col2:
    doc_type_filter = st.selectbox(
        "Document Type", ["All", "policy", "report", "memo", "contract",
                          "procedure", "manual", "form", "correspondence"]
    )
with col3:
    result_limit = st.slider("Max Results", 5, 30, 10)

if search_query:
    st.markdown("---")
    st.markdown("### Search Results")

    escaped_query = search_query.replace("'", "''")
    dept_clause = f"AND DEPARTMENT = '{dept_filter}'" if dept_filter != "All" else ""
    type_clause = f"AND DOCUMENT_TYPE = '{doc_type_filter}'" if doc_type_filter != "All" else ""

    with st.spinner("Searching..."):
        results = session.sql(f"""
            SELECT
                CHUNK_ID,
                DOCUMENT_ID,
                LEFT(CHUNK_TEXT, 500) AS PREVIEW,
                FILE_NAME,
                DEPARTMENT,
                DOCUMENT_TYPE,
                SECTION_HEADER,
                VECTOR_COSINE_SIMILARITY(
                    EMBEDDING,
                    SNOWFLAKE.CORTEX.EMBED_TEXT_1024(
                        'snowflake-arctic-embed-l-v2.0',
                        '{escaped_query}'
                    )
                ) AS RELEVANCE
            FROM KNOWLEDGE.DOCUMENT_CHUNKS
            WHERE EMBEDDING IS NOT NULL
                {dept_clause}
                {type_clause}
            ORDER BY RELEVANCE DESC
            LIMIT {result_limit}
        """).collect()

    if results:
        for i, row in enumerate(results):
            score = float(row["RELEVANCE"])
            score_color = "🟢" if score > 0.8 else "🟡" if score > 0.6 else "🔴"

            with st.expander(
                f"{score_color} **{row['FILE_NAME']}** — "
                f"{row['DEPARTMENT']} | Score: {score:.3f}",
                expanded=(i == 0),
            ):
                if row["SECTION_HEADER"]:
                    st.markdown(f"**Section:** {row['SECTION_HEADER']}")
                st.markdown(row["PREVIEW"])
                st.caption(f"Document ID: {row['DOCUMENT_ID']} | Type: {row['DOCUMENT_TYPE']}")
    else:
        st.warning("No results found. Try different keywords or broaden filters.")

else:
    # Show catalog when no search query
    st.markdown("---")
    st.markdown("### Knowledge Catalog")

    dept_where = f"WHERE DEPARTMENT = '{dept_filter}'" if dept_filter != "All" else ""

    catalog_df = session.sql(f"""
        SELECT
            DOCUMENT_ID,
            TITLE,
            DEPARTMENT,
            DOCUMENT_TYPE,
            SENSITIVITY_LEVEL,
            CHUNK_COUNT,
            TOTAL_TOKENS,
            LAST_UPDATED_AT
        FROM KNOWLEDGE.KNOWLEDGE_CATALOG
        {dept_where}
        ORDER BY LAST_UPDATED_AT DESC
        LIMIT 50
    """).to_pandas()

    if not catalog_df.empty:
        # Department distribution
        dept_counts = catalog_df["DEPARTMENT"].value_counts()
        st.bar_chart(dept_counts)

        st.dataframe(catalog_df, use_container_width=True, hide_index=True)
    else:
        st.info("Knowledge catalog is empty. Upload and process documents to populate it.")
