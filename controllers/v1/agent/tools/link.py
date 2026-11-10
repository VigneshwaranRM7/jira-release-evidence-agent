import time
from typing import Dict, Any, List, Optional
from controllers.v1.jira.base_client import BaseJiraClient
from controllers.v1.agent.tools.issue import _resolve_issue

def execute_get_linked_evidence(jira_client: BaseJiraClient, issue_key: str, telemetry: Optional[Any] = None) -> Dict[str, Any]:
    """Retrieve all linked dependency/evidence keys."""
    t0 = time.time()
    issue = _resolve_issue(jira_client, issue_key)
    target_key = issue.key if issue else issue_key
    links = jira_client.get_linked_issues(target_key)
    duration_ms = (time.time() - t0) * 1000
    out = {
        "issue_key": target_key,
        "linked_keys": links,
        "count": len(links)
    }
    if telemetry:
        telemetry.record_tool_call(
            tool_name="get_linked_evidence",
            arguments={"issue_key": issue_key},
            raw_output=out,
            output_summary=f"Found {len(links)} linked issue(s) for {target_key}",
            duration_ms=duration_ms
        )
    return out
