import re
from typing import Dict, Any, Optional

SCENARIO_PATTERN = re.compile(
    r"^Recorded event (?P<timestamp>[^|]+)\s*\|\s*actor (?P<actor>[^|]+)\s*\|\s*role (?P<role>[^\n]+)\n(?P<body>.*)$",
    re.DOTALL
)

def parse_scenario_comment(raw_text: str) -> Dict[str, Any]:
    """Parse scenario metadata preserved in Jira comment text."""
    match = SCENARIO_PATTERN.match(raw_text.strip())
    if match:
        return {
            "timestamp": match.group("timestamp").strip(),
            "actor": match.group("actor").strip(),
            "role": match.group("role").strip(),
            "body": match.group("body").strip(),
        }
    return {
        "timestamp": None,
        "actor": None,
        "role": None,
        "body": raw_text.strip(),
    }

def format_scenario_comment(actor: str, role: str, timestamp: str, body: str) -> str:
    """Format comment text to preserve scenario actor, role, and event timestamp."""
    return f"Recorded event {timestamp} | actor {actor} | role {role}\n{body}"

