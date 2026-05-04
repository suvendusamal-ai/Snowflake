def plan(session, prompt):

    result = session.sql(f"""
        SELECT TRIM(
            SNOWFLAKE.CORTEX.COMPLETE(
                'mistral-large',
                $$
                You are an AI planner.

                Classify the user request into ONLY ONE of these categories:
                - SQL (for data queries, totals, counts)
                - FRAUD (only if user explicitly asks to detect, check, or find fraud transactions)
                - GENERAL (for explanations, definitions, policies, rules)

                Examples:
                "What is fraud rule?" → GENERAL
                "Explain fraud detection" → GENERAL
                "Check fraud transactions" → FRAUD
                "Find suspicious transactions" → FRAUD
                "Total transaction amount" → SQL

                Return ONLY one word: SQL, FRAUD, or GENERAL.

                Request: {prompt}
                $$
            )
        )
    """).collect()

    return result[0][0].strip().upper()