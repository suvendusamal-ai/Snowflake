"""Search Diagnostics & Agent Trace - Observability for AI operations."""

import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Diagnostics", page_icon="🔧", layout="wide")
st.title("🔧 Search Diagnostics & Agent Trace")


def get_session():
    try:
        return get_active_session()
    except Exception:
        return st.connection("snowflake").session()


session = get_session()

tab1, tab2, tab3 = st.tabs(["Search Diagnostics", "Agent Traces", "Token Usage"])

# ─── Search Diagnostics ──────────────────────────────────────────────────────
with tab1:
    st.markdown("### Recent Search Performance")

    search_metrics = session.sql("""
        SELECT
            DATE_TRUNC('HOUR', CREATED_AT) AS HOUR,
            COUNT(*) AS QUERY_COUNT,
            AVG(LATENCY_MS) AS AVG_LATENCY,
            AVG(TOP_SCORE) AS AVG_TOP_SCORE,
            AVG(RESULT_COUNT) AS AVG_RESULTS
        FROM OBSERVABILITY.SEARCH_DIAGNOSTICS
        WHERE CREATED_AT > DATEADD('DAY', -7, CURRENT_TIMESTAMP())
        GROUP BY DATE_TRUNC('HOUR', CREATED_AT)
        ORDER BY HOUR DESC
        LIMIT 168
    """).to_pandas()

    if not search_metrics.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Query Volume (hourly)**")
            st.line_chart(search_metrics.set_index("HOUR")["QUERY_COUNT"])
        with col2:
            st.markdown("**Average Latency (ms)**")
            st.line_chart(search_metrics.set_index("HOUR")["AVG_LATENCY"])

        st.markdown("**Average Relevance Score**")
        st.line_chart(search_metrics.set_index("HOUR")["AVG_TOP_SCORE"])
    else:
        st.info("No search diagnostics data yet.")

    # Recent queries
    st.markdown("### Recent Queries")
    recent_queries = session.sql("""
        SELECT QUERY_TEXT, RESULT_COUNT, TOP_SCORE, LATENCY_MS, CREATED_AT
        FROM OBSERVABILITY.SEARCH_DIAGNOSTICS
        ORDER BY CREATED_AT DESC
        LIMIT 20
    """).to_pandas()

    if not recent_queries.empty:
        st.dataframe(recent_queries, use_container_width=True, hide_index=True)

# ─── Agent Traces ────────────────────────────────────────────────────────────
with tab2:
    st.markdown("### Agent Execution Traces")

    traces = session.sql("""
        SELECT
            t.TRACE_ID,
            t.CONVERSATION_ID,
            t.STEP_TYPE,
            t.DURATION_MS,
            t.TOKENS_USED,
            t.MODEL,
            t.STATUS,
            t.CREATED_AT
        FROM AGENT.AGENT_TRACES t
        ORDER BY t.CREATED_AT DESC
        LIMIT 50
    """).to_pandas()

    if not traces.empty:
        # Summary metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Traces", len(traces))
        c2.metric("Avg Latency", f"{traces['DURATION_MS'].mean():.0f} ms")
        c3.metric("Avg Tokens", f"{traces['TOKENS_USED'].mean():.0f}")
        c4.metric("Success Rate", f"{(traces['STATUS'] == 'SUCCESS').mean() * 100:.1f}%")

        st.dataframe(traces, use_container_width=True, hide_index=True)
    else:
        st.info("No agent traces recorded yet.")

# ─── Token Usage ─────────────────────────────────────────────────────────────
with tab3:
    st.markdown("### Token Usage & Cost")

    cost_data = session.sql("""
        SELECT
            HOUR_BUCKET,
            MODEL,
            OPERATION_TYPE,
            INVOCATION_COUNT,
            TOTAL_TOKENS,
            ESTIMATED_COST_USD
        FROM OBSERVABILITY.COST_AGGREGATION
        ORDER BY HOUR_BUCKET DESC
        LIMIT 100
    """).to_pandas()

    if not cost_data.empty:
        # Total cost
        total_cost = cost_data["ESTIMATED_COST_USD"].sum()
        total_tokens = cost_data["TOTAL_TOKENS"].sum()
        total_invocations = cost_data["INVOCATION_COUNT"].sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("Est. Total Cost", f"${total_cost:.2f}")
        c2.metric("Total Tokens", f"{total_tokens:,.0f}")
        c3.metric("Total Invocations", f"{total_invocations:,.0f}")

        st.markdown("**Cost by Model**")
        cost_by_model = cost_data.groupby("MODEL")["ESTIMATED_COST_USD"].sum()
        st.bar_chart(cost_by_model)

        st.markdown("**Hourly Token Usage**")
        hourly = cost_data.groupby("HOUR_BUCKET")["TOTAL_TOKENS"].sum()
        st.line_chart(hourly)
    else:
        st.info("No cost data available yet.")
