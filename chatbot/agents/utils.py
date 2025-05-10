from typing import List, Dict, Any


def compact_feedback_list(feedback_list):
    def compact_feedback(fb):
        return f"""🧾 {fb['Query'].strip()}
❌ {fb['Response'].strip().splitlines()[0]}
🛠 {fb['Feedback'].strip().split('.')[0]}.
✅ {fb['Correction'].strip().splitlines()[0]}"""

    return "\n\n---\n\n".join([compact_feedback(fb) for fb in feedback_list])


def optimize_business_logic(rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    (Same as before) Normalize your rules: dedupe by id, parse string-lists,
    wrap single stages into lists, etc.
    """
    optimized: Dict[str, Dict[str, Any]] = {}
    for rule in rules:
        rid = rule["id"]
        if rid in optimized:
            # merge workflow_stage lists
            existing = optimized[rid]
            ws = rule.get("workflow_stage", [])
            ws = [ws] if isinstance(ws, str) else ws
            existing["workflow_stage"] = list(set(existing["workflow_stage"]) | set(ws))
            continue

        norm = {"id": rid}
        # normalize workflow_stage
        ws = rule.get("workflow_stage", [])
        norm["workflow_stage"] = [ws] if isinstance(ws, str) else ws
        # carry over only the fields we care about
        norm["strategy"] = rule.get("strategy", "")
        optimized[rid] = norm
    return list(optimized.values())

def format_strategies_for_prompt(rules: List[Dict[str, Any]]) -> str:
    """
    Given your normalized rules, returns a markdown-style block
    with only the strategy lines.
    """
    normalized = optimize_business_logic(rules)
    lines = []
    for idx, rule in enumerate(normalized, start=1):
        lines.append(f"{idx}. {rule['id']}:\n   {rule['strategy'].strip()}")
    return "\n\n".join(lines)