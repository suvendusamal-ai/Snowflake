import json


def retrieve_context(session, query):

    rows = session.sql(f"""
        SELECT PARSE_JSON(
            SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
                'AGENTIC_DB.BANKING.BANKING_SEARCH',
                '{{
                    "query": "{query}",
                    "columns": ["CONTENT"],
                    "limit": 5
                }}'
            )
        )['results'] AS results
    """).collect()

    data = json.loads(rows[0]["RESULTS"])

    return " ".join([item["CONTENT"] for item in data])