"""AI Chat - Conversational interface to the Enterprise Knowledge Agent."""

import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="AI Chat", page_icon="💬", layout="wide")

st.title("💬 AI Knowledge Assistant")
st.markdown("Ask questions about enterprise documents across all departments.")


def get_session():
    try:
        return get_active_session()
    except Exception:
        return st.connection("snowflake").session()


# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

session = get_session()

# Sidebar - conversation management
with st.sidebar:
    st.markdown("### Conversations")

    if st.button("➕ New Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.conversation_id = None
        st.rerun()

    # Department scope
    department = st.selectbox(
        "Scope to Department",
        ["All", "finance", "treasury", "procurement", "risk",
         "compliance", "audit", "hr", "legal", "operations"],
    )
    dept_filter = None if department == "All" else department

    # Model settings
    with st.expander("Settings"):
        temperature = st.slider("Temperature", 0.0, 1.0, 0.0, 0.1)
        max_results = st.slider("Max Search Results", 5, 20, 10)
        show_citations = st.checkbox("Show Citations", value=True)
        show_diagnostics = st.checkbox("Show Diagnostics", value=False)

    st.markdown("---")
    st.markdown("### Recent Conversations")
    user = session.sql("SELECT CURRENT_USER() AS U").collect()[0]["U"]
    recent = session.sql(f"""
        SELECT CONVERSATION_ID, TITLE, MESSAGE_COUNT, LAST_ACTIVITY_AT
        FROM AGENT.CONVERSATIONS
        WHERE USER_ID = '{user}' AND STATUS = 'ACTIVE'
        ORDER BY LAST_ACTIVITY_AT DESC LIMIT 10
    """).collect()

    for conv in recent:
        title = conv["TITLE"] or "Untitled"
        if st.button(f"📝 {title[:30]}...", key=conv["CONVERSATION_ID"]):
            st.session_state.conversation_id = conv["CONVERSATION_ID"]
            # Load history
            msgs = session.sql(f"""
                SELECT ROLE, CONTENT FROM AGENT.CONVERSATION_MESSAGES
                WHERE CONVERSATION_ID = '{conv["CONVERSATION_ID"]}'
                ORDER BY CREATED_AT ASC
            """).collect()
            st.session_state.messages = [
                {"role": m["ROLE"], "content": m["CONTENT"]} for m in msgs
            ]
            st.rerun()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "citations" in message and show_citations:
            with st.expander("📚 Sources"):
                for cite in message["citations"]:
                    st.markdown(f"- **{cite.get('file_name', 'Unknown')}** "
                               f"(score: {cite.get('score', 0):.2f})")

# Chat input
if prompt := st.chat_input("Ask about enterprise knowledge..."):
    # Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Searching knowledge base..."):
            try:
                # Build conversation context
                import json

                history_messages = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages[-10:]  # Last 10 messages
                ]

                # Add department context
                user_query = prompt
                if dept_filter:
                    user_query = f"[Department: {dept_filter}] {prompt}"

                messages_json = json.dumps(history_messages).replace("'", "''")

                # Call Cortex Complete with conversation
                result = session.sql(f"""
                    SELECT SNOWFLAKE.CORTEX.COMPLETE(
                        'claude-3-5-sonnet',
                        PARSE_JSON('{messages_json}'),
                        OBJECT_CONSTRUCT('temperature', {temperature}, 'max_tokens', 4096)
                    ) AS RESPONSE
                """).collect()

                response_text = result[0]["RESPONSE"] if result else "No response generated."

                # Also run search for citations
                escaped_query = prompt.replace("'", "''")
                dept_clause = f"AND DEPARTMENT = '{dept_filter}'" if dept_filter else ""
                search_results = session.sql(f"""
                    SELECT CHUNK_ID, DOCUMENT_ID, FILE_NAME, DEPARTMENT,
                           SECTION_HEADER,
                           VECTOR_COSINE_SIMILARITY(
                               EMBEDDING,
                               SNOWFLAKE.CORTEX.EMBED_TEXT_1024(
                                   'snowflake-arctic-embed-l-v2.0', '{escaped_query}'
                               )
                           ) AS SCORE
                    FROM KNOWLEDGE.DOCUMENT_CHUNKS
                    WHERE EMBEDDING IS NOT NULL {dept_clause}
                    ORDER BY SCORE DESC
                    LIMIT {max_results}
                """).collect()

                citations = [
                    {
                        "file_name": r["FILE_NAME"],
                        "department": r["DEPARTMENT"],
                        "section": r["SECTION_HEADER"],
                        "score": float(r["SCORE"]),
                    }
                    for r in search_results
                ]

                # Display response
                st.markdown(response_text)

                # Citations
                if citations and show_citations:
                    with st.expander("📚 Sources"):
                        for cite in citations:
                            st.markdown(
                                f"- **{cite['file_name']}** "
                                f"({cite['department']}) — "
                                f"score: {cite['score']:.3f}"
                            )

                # Diagnostics
                if show_diagnostics:
                    with st.expander("🔧 Diagnostics"):
                        st.json({
                            "model": "claude-3-5-sonnet",
                            "search_results": len(citations),
                            "top_score": citations[0]["score"] if citations else 0,
                            "department_filter": dept_filter,
                        })

                # Save to session state
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "citations": citations,
                })

                # Persist to database
                if not st.session_state.conversation_id:
                    conv_id = session.sql("""
                        SELECT UUID_STRING() AS ID
                    """).collect()[0]["ID"]
                    session.sql(f"""
                        INSERT INTO AGENT.CONVERSATIONS
                        (CONVERSATION_ID, USER_ID, TITLE, STATUS)
                        VALUES ('{conv_id}', '{user}', '{prompt[:60]}', 'ACTIVE')
                    """).collect()
                    st.session_state.conversation_id = conv_id

            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"I encountered an error: {str(e)}",
                })
