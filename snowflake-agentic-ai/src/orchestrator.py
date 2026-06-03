from src.agents.guardrails import validate_input, sanitize_prompt
from src.agents.planner import plan
from src.agents.tool_router import route
from src.tools.logger import log_event


def orchestrate(session, prompt):

    trace = []

    trace.append(f"Input: {prompt}")

    valid, msg = validate_input(prompt)
    if not valid:
        trace.append("Guardrail: BLOCKED")
        return {
            "intent": "BLOCKED",
            "tool": "GUARDRAIL",
            "trace": trace,
            "response": msg
        }

    trace.append("Guardrail: PASSED")

    prompt = sanitize_prompt(prompt)

    intent = plan(session, prompt)
    trace.append(f"Planner Decision: {intent}")

    tool = "CORTEX_AGENT" if intent != "FRAUD" else "FRAUD_TOOL"
    trace.append(f"Tool Selected: {tool}")

    response = route(session, intent, prompt)
    trace.append("Execution Completed")

    try:
        log_event(session, prompt, intent, str(response), tool)
    except Exception:
        pass

    return {
        "intent": intent,
        "tool": tool,
        "trace": trace,
        "response": response
    }