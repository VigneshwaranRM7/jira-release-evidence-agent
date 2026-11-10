from typing import List, Dict, Any

AGENT_TOOLS_SCHEMA: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_jira_issues",
            "description": "Search Jira issues using JQL query. Always scope queries to the target project and dataset label.",
            "parameters": {
                "type": "object",
                "properties": {
                    "jql": {
                        "type": "string",
                        "description": "JQL query string (e.g. 'labels = \"tyn-release-assessment-v2\" AND summary ~ \"regression\"')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Max number of issues to return (default 20)"
                    }
                },
                "required": ["jql"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_ticket_details",
            "description": "Retrieve comprehensive ticket details including summary, status, release, description, and direct linked issue keys.",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "The Jira issue key (e.g. 'REL-1001') or source ID (e.g. 'REQ-01')"
                    }
                },
                "required": ["issue_key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_ticket_comments",
            "description": "Retrieve chronological comments on a ticket with extracted scenario metadata (actor, role, event timestamp, and QA verification details).",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "The Jira issue key or source ID"
                    }
                },
                "required": ["issue_key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_linked_evidence",
            "description": "Traverse inward and outward issue links to find connected dependencies, test records, or blocking defects.",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "The Jira issue key or source ID to inspect links for"
                    }
                },
                "required": ["issue_key"]
            }
        }
    }
]

AGENT_TOOLS = AGENT_TOOLS_SCHEMA

def get_tool_schema(name: str) -> Dict[str, Any]:
    for tool in AGENT_TOOLS_SCHEMA:
        fn = tool.get("function", {})
        if fn.get("name") == name:
            return fn
    return {}

