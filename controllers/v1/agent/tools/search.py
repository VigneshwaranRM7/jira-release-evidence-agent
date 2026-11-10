import time
from typing import Dict, Any, List, Optional
from controllers.v1.jira.base_client import BaseJiraClient

def execute_search_jira_issues(jira_client: BaseJiraClient, jql: str, max_results: int = 20, telemetry: Optional[Any] = None) -> Dict[str, Any]:
    """Execute JQL search against Jira client."""
    t0 = time.time()
    res = jira_client.search_issues(jql, max_results=max_results)
    out = {
        "total": res.total,
        "returned": len(res.issues),
        "issues": [
            {
                "key": issue.key,
                "source_id": issue.source_id,
                "summary": issue.summary,
                "status": issue.status,
                "release": issue.release,
                "labels": issue.labels,
                "links": issue.links
            }
            for issue in res.issues
        ]
    }
    duration_ms = (time.time() - t0) * 1000
    if telemetry:
        telemetry.record_tool_call(
            tool_name="search_jira_issues",
            arguments={"jql": jql, "max_results": max_results},
            raw_output=out,
            output_summary=f"Found {out['total']} issues matching JQL (returned {out['returned']})",
            duration_ms=duration_ms
        )
        telemetry.add_tokens(prompt=max(10, len(jql.split()) * 2), completion=max(20, len(str(out).split()) // 4))
    return out
