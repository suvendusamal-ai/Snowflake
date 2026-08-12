"""Document Upload - Upload and manage enterprise documents."""

import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Document Upload", page_icon="📄", layout="wide")
st.title("📄 Document Upload")
st.markdown("Upload documents to the enterprise knowledge base for AI-powered search.")


def get_session():
    try:
        return get_active_session()
    except Exception:
        return st.connection("snowflake").session()


session = get_session()

# Upload section
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Upload New Document")

    department = st.selectbox(
        "Target Department",
        ["finance", "treasury", "procurement", "risk",
         "compliance", "audit", "hr", "legal", "operations"],
    )

    uploaded_files = st.file_uploader(
        "Choose files",
        type=["pdf", "docx", "xlsx", "pptx", "csv", "json", "html", "txt", "png", "jpg"],
        accept_multiple_files=True,
        help="Supported: PDF, DOCX, XLSX, PPTX, CSV, JSON, HTML, TXT, PNG, JPG (max 100MB each)",
    )

    if uploaded_files:
        st.markdown(f"**{len(uploaded_files)} file(s) selected:**")
        for f in uploaded_files:
            size_mb = f.size / (1024 * 1024)
            st.markdown(f"- {f.name} ({size_mb:.1f} MB)")

        if st.button("🚀 Upload & Process", type="primary", use_container_width=True):
            progress = st.progress(0)
            status = st.empty()

            for i, file in enumerate(uploaded_files):
                status.markdown(f"Uploading **{file.name}**...")
                progress.progress((i + 1) / len(uploaded_files))

                try:
                    # Upload to stage via PUT
                    file_bytes = file.read()
                    stage_name = f"RAW.{department.upper()}_DOCS"

                    # Use session file.put equivalent via SQL
                    import tempfile, os
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=os.path.splitext(file.name)[1]
                    ) as tmp:
                        tmp.write(file_bytes)
                        tmp_path = tmp.name

                    doc_id = session.sql("SELECT UUID_STRING() AS ID").collect()[0]["ID"]

                    session.file.put(
                        tmp_path,
                        f"@{stage_name}/{doc_id}/",
                        auto_compress=False,
                        overwrite=True,
                    )

                    # Register in DOCUMENT_REGISTRY
                    escaped_name = file.name.replace("'", "''")
                    ext = os.path.splitext(file.name)[1].lower()
                    session.sql(f"""
                        INSERT INTO RAW.DOCUMENT_REGISTRY (
                            DOCUMENT_ID, FILE_NAME, FILE_TYPE, FILE_SIZE_BYTES,
                            DEPARTMENT, STAGE_PATH, UPLOADED_BY, PROCESSING_STATUS
                        ) VALUES (
                            '{doc_id}', '{escaped_name}', '{ext}', {len(file_bytes)},
                            '{department}', '@{stage_name}/{doc_id}/{file.name}',
                            CURRENT_USER(), 'PENDING'
                        )
                    """).collect()

                    os.unlink(tmp_path)
                    st.success(f"✅ {file.name} uploaded successfully (ID: {doc_id})")

                except Exception as e:
                    st.error(f"❌ Failed to upload {file.name}: {e}")

            progress.progress(1.0)
            status.markdown("**Upload complete!** Documents will be processed automatically.")

with col2:
    st.markdown("### Upload Guidelines")
    st.info("""
    **Supported formats:**
    - PDF, DOCX, PPTX, XLSX
    - CSV, JSON, HTML, TXT
    - PNG, JPG (OCR)
    
    **Size limit:** 100 MB per file
    
    **Processing pipeline:**
    1. Upload → Stage
    2. Parse (AI_PARSE_DOCUMENT)
    3. Classify (department, type)
    4. Chunk + Embed
    5. Index in Cortex Search
    
    Processing typically takes 1-3 minutes.
    """)

# Document status table
st.markdown("---")
st.markdown("### Document Processing Status")

status_filter = st.selectbox(
    "Filter by status",
    ["All", "PENDING", "PARSING", "CLASSIFYING", "COMPLETED", "FAILED"],
)

where_clause = "" if status_filter == "All" else f"WHERE PROCESSING_STATUS = '{status_filter}'"

docs_df = session.sql(f"""
    SELECT
        DOCUMENT_ID,
        FILE_NAME,
        DEPARTMENT,
        FILE_TYPE,
        ROUND(FILE_SIZE_BYTES / 1024.0, 1) AS SIZE_KB,
        PROCESSING_STATUS,
        UPLOAD_TIMESTAMP,
        ERROR_MESSAGE
    FROM RAW.DOCUMENT_REGISTRY
    {where_clause}
    ORDER BY UPLOAD_TIMESTAMP DESC
    LIMIT 50
""").to_pandas()

if not docs_df.empty:
    # Color-code status
    st.dataframe(
        docs_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "PROCESSING_STATUS": st.column_config.TextColumn("Status", width="small"),
            "SIZE_KB": st.column_config.NumberColumn("Size (KB)", format="%.1f"),
        },
    )
else:
    st.info("No documents found. Upload your first document above.")
