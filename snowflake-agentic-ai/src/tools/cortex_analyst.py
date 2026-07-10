import json


def run(session, prompt):

    request_body = json.dumps({
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt or ""}
                ]
            }
        ],
        "stream": False
    })

    query = f"""
        SELECT TRY_PARSE_JSON(
            SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
                'AGENTIC_DB.BANKING.BANKING_AGENT',
                $$ {request_body} $$
            )
        ) AS resp
    """

    rows = session.sql(query).collect()

    if not rows:
        return "No response from agent"

    raw_resp = rows[0]["RESP"]

    if not raw_resp:
        return "Empty agent response"

    # Normalize JSON
    if isinstance(raw_resp, str):
        try:
            response_json = json.loads(raw_resp)
        except Exception as e:
            return f"JSON parse error: {e}"
    else:
        response_json = raw_resp

    # Handle agent error
    if isinstance(response_json, dict) and "code" in response_json:
        return f"Agent error: {response_json.get('message', 'Unknown error')}"

    # 🔥 ROBUST EXTRACTION LOGIC
    try:
        messages = response_json.get("messages", [])

        extracted_texts = []

        for msg in messages:
            if msg.get("role") == "assistant":

                for item in msg.get("content", []):

                    # Only capture final readable responses
                    if item.get("type") == "text":
                        text = item.get("text", "").strip()

                        # Filter garbage / formatting noise
                        if text and len(text) > 10:
                            extracted_texts.append(text)

        # Return best available response
        if extracted_texts:
            return extracted_texts[-1]   # latest valid response

        # 🔁 FALLBACK: check tool_result (sometimes text is embedded there)
        for msg in messages:
            if msg.get("role") == "assistant":
                for item in msg.get("content", []):
                    if item.get("type") == "tool_result":
                        content = item.get("content", [])
                        for c in content:
                            if "text" in c:
                                return c["text"]

        return "No readable response found"

    except Exception as e:
        return f"Parsing error: {e}"