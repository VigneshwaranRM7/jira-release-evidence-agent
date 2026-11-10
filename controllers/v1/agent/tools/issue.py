import time
from typing import Dict, Any, List, Optional
from controllers.v1.jira.base_client import BaseJiraClient

def _resolve_issue(jira_client: BaseJiraClient, issue_key: str):
    issue = jira_client.get_issue(issue_key)
    if issue:
        return issue
    # Fallback search if issue_key is a source_id (e.g. 'REQ-01', 'MANIFEST', 'REC-1001')
    try:
        search_res = jira_client.search_issues(f'labels = "tyn-release-assessment-v2" AND summary ~ "{issue_key}"', max_results=1)
        if search_res.issues:
            return search_res.issues[0]
        # Try text search if summary didn't match
        search_res = jira_client.search_issues(f'text ~ "{issue_key}"', max_results=1)
        if search_res.issues:
            return search_res.issues[0]
    except Exception:
        pass
    return None

def execute_get_ticket_details(jira_client: BaseJiraClient, issue_key: str, telemetry: Optional[Any] = None) -> Dict[str, Any]:
    """Retrieve issue fields, description, and direct links."""
    t0 = time.time()
    issue = _resolve_issue(jira_client, issue_key)
    duration_ms = (time.time() - t0) * 1000
    if not issue:
        out = {"error": f"Issue not found: {issue_key}"}
        if telemetry:
            telemetry.record_tool_call("get_ticket_details", {"issue_key": issue_key}, out, f"Issue {issue_key} not found", duration_ms)
        return out
        
    out = {
        "key": issue.key,
        "source_id": issue.source_id,
        "summary": issue.summary,
        "description": issue.description,
        "status": issue.status,
        "kind": issue.kind,
        "release": issue.release,
        "labels": issue.labels,
        "linked_issue_keys": issue.links
    }
    if telemetry:
        telemetry.record_tool_call(
            tool_name="get_ticket_details",
            arguments={"issue_key": issue_key},
            raw_output=out,
            output_summary=f"Retrieved ticket details for {issue.key} ({issue.source_id})",
            duration_ms=duration_ms
        )
    return out

def execute_get_ticket_comments(jira_client: BaseJiraClient, issue_key: str, telemetry: Optional[Any] = None) -> Dict[str, Any]:
    """Retrieve chronological comments with scenario actor, role, and timestamp."""
    t0 = time.time()
    issue = _resolve_issue(jira_client, issue_key)
    target_key = issue.key if issue else issue_key
    comments = jira_client.get_comments(target_key)
    duration_ms = (time.time() - t0) * 1000
    out = {
        "issue_key": target_key,
        "comment_count": len(comments),
        "comments": [
            {
                "id": c.id,
                "scenario_actor": c.scenario_actor,
                "scenario_role": c.scenario_role,
                "scenario_timestamp": c.scenario_timestamp,
                "body": c.body
            }
            for c in comments
        ]
    }
    if telemetry:
        telemetry.record_tool_call(
            tool_name="get_ticket_comments",
            arguments={"issue_key": issue_key},
            raw_output=out,
            output_summary=f"Retrieved {len(comments)} comment(s) for {target_key}",
            duration_ms=duration_ms
        )
    return out
