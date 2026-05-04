def log_event(session, prompt, intent, response, tool="UNKNOWN"):

    try:
        session.sql(
            """
            INSERT INTO AGENT_LOGS
            (EVENT_TIME, PROMPT, INTENT, TOOL, RESPONSE)
            VALUES (CURRENT_TIMESTAMP, ?, ?, ?, ?)
            """,
            params=[prompt, intent, tool, str(response)[:500]]
        ).collect()

    except Exception as e:
        print("Logging failed:", e)