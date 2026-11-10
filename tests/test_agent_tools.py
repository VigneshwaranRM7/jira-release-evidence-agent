import pytest
from utils.telemetry import TelemetryCollector
from controllers.v1.agent.tools.search import execute_search_jira_issues
from controllers.v1.agent.tools.issue import execute_get_ticket_details, execute_get_ticket_comments
from controllers.v1.agent.tools.link import execute_get_linked_evidence
from controllers.v1.agent.tools.registry import AGENT_TOOLS, get_tool_schema

def test_tool_registry_schemas():
    assert len(AGENT_TOOLS) == 4
    for tool_name in ["search_jira_issues", "get_ticket_details", "get_ticket_comments", "get_linked_evidence"]:
        schema = get_tool_schema(tool_name)
        assert schema is not None
        assert schema["name"] == tool_name
        assert "description" in schema
        assert "parameters" in schema

def test_search_jira_issues_tool(mock_client):
    telemetry = TelemetryCollector(assessment_id="test-tool-trace")
    jql = 'labels = "tyn-release-assessment-v2" AND text ~ "REG-804"'
    
    result = execute_search_jira_issues(mock_client, jql, max_results=10, telemetry=telemetry)
    assert result["total"] > 0
    assert len(result["issues"]) > 0
    assert len(telemetry.invocations) == 1
    assert telemetry.invocations[0].tool_name == "search_jira_issues"
    assert telemetry.invocations[0].arguments["jql"] == jql
    assert telemetry.token_usage["total_tokens"] > 0

def test_ticket_details_and_comments_tools(mock_client):
    telemetry = TelemetryCollector(assessment_id="test-details-trace")
    
    # Details tool
    details = execute_get_ticket_details(mock_client, "REC-1001", telemetry=telemetry)
    assert details["source_id"] == "REC-1001"
    assert "Customer document isolation" in details["summary"]
    assert details["status"] == "To Do"


    # Comments tool
    comments_res = execute_get_ticket_comments(mock_client, "REC-1001", telemetry=telemetry)
    assert comments_res["issue_key"] in ("REC-1001", "REL-1305")
    assert comments_res["comment_count"] > 0
    assert len(comments_res["comments"]) == comments_res["comment_count"]

    assert len(telemetry.invocations) == 2
    assert telemetry.invocations[1].tool_name == "get_ticket_comments"

def test_linked_evidence_tool(mock_client):
    telemetry = TelemetryCollector(assessment_id="test-link-trace")
    
    # REC-4076 has linked dependency REC-9635
    links = execute_get_linked_evidence(mock_client, "REC-4076", telemetry=telemetry)
    assert links["issue_key"] in ("REC-4076", "REL-1341")
    assert links["count"] > 0
    assert len(telemetry.invocations) == 1
    assert telemetry.invocations[0].tool_name == "get_linked_evidence"

def test_llm_agent_adapter_dispatch(mock_client):
    from controllers.v1.agent.llm_adapter import LLMAgentAdapter
    telemetry = TelemetryCollector(assessment_id="test-llm-adapter")
    adapter = LLMAgentAdapter(jira_client=mock_client, telemetry=telemetry)
    
    # Test tool dispatch via adapter
    res = adapter.execute_tool_call("search_jira_issues", {"jql": 'labels = "tyn-release-assessment-v2" AND text ~ "REG-804"'})
    assert res.get("total") > 0
    
    prompt = adapter.get_system_prompt()
    assert "Release R2.4" in prompt
    assert "target commit b7a91f2" in prompt

