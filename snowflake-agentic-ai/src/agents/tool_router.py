from src.tools.cortex_analyst import run
from src.tools.fraud_tool import detect_fraud


def route(session, intent, prompt):

    prompt_lower = (prompt or "").lower()

    # -----------------------------------------------------
    # FRAUD INTENT → DATA + EXPLANATION (Improved)
    # -----------------------------------------------------
    if intent == "FRAUD":

        result = detect_fraud(session)

        sql_output = f"""
SQL Executed:
{result['sql']}

Results:
{" | ".join(result['data'])}
"""

        needs_explanation = any(
            word in prompt_lower
            for word in ["explain", "why", "reason", "risky"]
        )

        if needs_explanation:

            try:
                # -------------------------------
                # Step 1: Fetch fraud rules (Cortex Search)
                # -------------------------------
                rules_query = """
                SELECT PARSE_JSON(
                  SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
                    'AGENTIC_DB.BANKING.BANKING_SEARCH',
                    '{
                      "query": "fraud rules high risk transactions",
                      "columns": ["CONTENT"],
                      "limit": 3
                    }'
                  )
                )['results'] AS results
                """

                rules_rows = session.sql(rules_query).collect()

                rules_text = ""

                if rules_rows and rules_rows[0]["RESULTS"]:
                    for r in rules_rows[0]["RESULTS"]:
                        if isinstance(r, dict):
                            rules_text += f"- {r.get('CONTENT', '')}\n"
                        elif isinstance(r, str):
                            rules_text += f"- {r}\n"

                if not rules_text.strip():
                    rules_text = "Transactions above 200000 are considered high risk."

                # -------------------------------
                # Step 2: Improved LLM Prompt (Data-grounded)
                # -------------------------------
                llm_prompt = f"""
You are a banking fraud analyst.

Fraud Rules:
{rules_text}

Suspicious Transactions:
{sql_output}

Explain clearly and specifically:

For EACH transaction:
- Mention transaction ID
- Mention amount
- Mention assigned risk (HIGH / MEDIUM)
- Explain WHY it is risky based on rules

Then provide:
- Summary of risk pattern
- Recommended actions

Keep response precise, structured, and professional.
"""

                llm_query = f"""
                SELECT SNOWFLAKE.CORTEX.COMPLETE(
                    'mistral-large',
                    $$ {llm_prompt} $$
                ) AS response
                """

                llm_resp = session.sql(llm_query).collect()

                explanation = (
                    llm_resp[0]["RESPONSE"]
                    if llm_resp and llm_resp[0]["RESPONSE"]
                    else "No explanation generated"
                )

                return f"""
{sql_output}

Explanation:
{explanation}
"""

            except Exception as e:
                return f"""
{sql_output}

Explanation:
Failed to generate explanation: {str(e)}
"""

        return sql_output

    # -----------------------------------------------------
    # CUSTOMER RISK + POLICY QUERY
    # -----------------------------------------------------
    if "customer" in prompt_lower and "risk" in prompt_lower:

        try:
            # -------------------------------
            # Step 1: High-risk customers
            # -------------------------------
            customer_query = """
            SELECT CUSTOMER_ID, NAME, RISK_PROFILE
            FROM CUSTOMERS
            WHERE RISK_PROFILE = 'HIGH'
            """

            rows = session.sql(customer_query).collect()

            customers = [
                f"{r['CUSTOMER_ID']} | {r['NAME']} | Risk: {r['RISK_PROFILE']}"
                for r in rows
            ]

            customer_text = "\n".join(customers) if customers else "No high-risk customers found"

            # -------------------------------
            # Step 2: Policies via Cortex Search
            # -------------------------------
            rules_query = """
            SELECT PARSE_JSON(
              SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
                'AGENTIC_DB.BANKING.BANKING_SEARCH',
                '{
                  "query": "high risk customer policies fraud rules",
                  "columns": ["CONTENT"],
                  "limit": 3
                }'
              )
            )['results'] AS results
            """

            rules_rows = session.sql(rules_query).collect()

            rules_text = ""

            if rules_rows and rules_rows[0]["RESULTS"]:
                for r in rules_rows[0]["RESULTS"]:
                    if isinstance(r, dict):
                        rules_text += f"- {r.get('CONTENT', '')}\n"
                    elif isinstance(r, str):
                        rules_text += f"- {r}\n"

            if not rules_text.strip():
                rules_text = "High-risk customers must be monitored closely."

            # -------------------------------
            # Step 3: LLM Explanation
            # -------------------------------
            llm_prompt = f"""
You are a banking compliance expert.

High Risk Customers:
{customer_text}

Policies:
{rules_text}

Explain:
1. Who the high-risk customers are
2. Why they are high risk
3. What policies apply to them

Keep response clear and professional.
"""

            llm_query = f"""
            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                'mistral-large',
                $$ {llm_prompt} $$
            ) AS response
            """

            llm_resp = session.sql(llm_query).collect()

            explanation = (
                llm_resp[0]["RESPONSE"]
                if llm_resp and llm_resp[0]["RESPONSE"]
                else "No explanation generated"
            )

            return f"""
High Risk Customers:
{customer_text}

Explanation:
{explanation}
"""

        except Exception as e:
            return f"Customer risk analysis failed: {str(e)}"

    # -----------------------------------------------------
    # DEFAULT → Cortex Agent (Analyst + Search)
    # -----------------------------------------------------
    try:
        return run(session, prompt)

    except Exception as e:
        return f"Agent execution failed: {str(e)}"