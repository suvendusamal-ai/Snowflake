import re

def validate_input(prompt: str):

    # Basic injection / abuse patterns
    blocked_patterns = [
        r"drop\s+table",
        r"delete\s+from",
        r"--",
        r";",
    ]

    for pattern in blocked_patterns:
        if re.search(pattern, prompt, re.IGNORECASE):
            return False, "❌ Potentially unsafe query detected."

    if len(prompt) > 500:
        return False, "❌ Query too long."

    return True, prompt


def sanitize_prompt(prompt: str):
    return prompt.strip()