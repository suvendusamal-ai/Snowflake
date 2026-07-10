import snowflake.connector
import json
import yaml
import re

with open("config/config.yaml") as f:
    config = yaml.safe_load(f)


def get_metadata(prompt: str):

    conn = snowflake.connector.connect(
        user=config["snowflake"]["user"],
        password=config["snowflake"]["password"],
        account=config["snowflake"]["account"],
        warehouse=config["snowflake"]["warehouse"],
        database=config["snowflake"]["database"],
        schema=config["snowflake"]["schema"]
    )

    cs = conn.cursor()

    query = """
    SELECT SNOWFLAKE.CORTEX.AI_COMPLETE(
        'mistral-large',
        %s
    )
    """

    # ✅ Strong prompt for consistent JSON
    prompt_text = f"""
    Extract table names from the user input.
    Return ONLY strict JSON in this format:
    {{"tables":["Customers"]}}

    User Input: {prompt}
    """

    cs.execute(query, (prompt_text,))
    result = cs.fetchone()[0]

    cs.close()
    conn.close()

    # 🔵 Debug log
    print("🔵 RAW LLM OUTPUT:", result)

    # ✅ Clean response
    result = result.replace("```json", "").replace("```", "").strip()

    # ✅ Try parsing JSON
    try:
        data = json.loads(result)

        # normalize possible formats
        if isinstance(data, dict):

            if "tables" in data and isinstance(data["tables"], list):
                return {"tables": [t.capitalize() for t in data["tables"]]}

            if "table_name" in data:
                return {"tables": [data["table_name"].capitalize()]}

    except Exception:
        pass

    # ✅ Regex fallback (handles bad LLM output)
    match = re.search(r'"table_name"\s*:\s*"(\w+)"', result, re.IGNORECASE)
    if match:
        return {"tables": [match.group(1).capitalize()]}

    match = re.search(r'"tables"\s*:\s*\[\s*"(\w+)"\s*\]', result, re.IGNORECASE)
    if match:
        return {"tables": [match.group(1).capitalize()]}

    # ✅ Final fallback (extract from prompt directly)
    words = re.findall(r'\b[a-zA-Z_]+\b', prompt)
    ignore = {"load", "data", "from", "table", "extract", "the"}

    candidates = [w for w in words if w.lower() not in ignore]

    if candidates:
        return {"tables": [candidates[-1].capitalize()]}

    return {"tables": []}
