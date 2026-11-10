import re
from typing import Optional, Tuple

MAX_MODEL_COST_PER_REQUEST = 0.012  # USD 0.012 for REQ-05

def evaluate_model_cost(comment_text: str) -> Tuple[bool, Optional[float], str]:
    """
    Parses mean cost from QA comments and compares against acceptance criterion (<= 0.012 USD).
    Returns (is_compliant, cost_value, explanation).
    """
    match = re.search(r"Mean cost USD\s*([0-9.]+)", comment_text, re.IGNORECASE)
    if not match:
        return False, None, "No mean cost measurement found in record."
    
    cost = float(match.group(1))
    if cost <= MAX_MODEL_COST_PER_REQUEST:
        return True, cost, f"Mean cost USD {cost:.3f} satisfies requirement (<= USD {MAX_MODEL_COST_PER_REQUEST:.3f})."
    else:
        return False, cost, f"Mean cost USD {cost:.3f} exceeds threshold of USD {MAX_MODEL_COST_PER_REQUEST:.3f}."

def calculate_llm_cost(prompt_tokens: int, completion_tokens: int, model_name: str = "gemini-2.0-flash") -> float:
    """Calculates dollar cost of LLM tokens based on standard model rate cards."""
    model_lower = (model_name or "").lower()
    if "gpt-4o-mini" in model_lower or "flash" in model_lower:
        cost = (prompt_tokens * 0.00000015) + (completion_tokens * 0.00000060)
    elif "gpt-4o" in model_lower:
        cost = (prompt_tokens * 0.0000025) + (completion_tokens * 0.0000100)
    else:
        cost = (prompt_tokens * 0.00000015) + (completion_tokens * 0.00000060)
    return round(cost, 6)
