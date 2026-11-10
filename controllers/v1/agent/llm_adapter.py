import os
from typing import List, Dict, Any, Optional
from controllers.v1.jira.base_client import BaseJiraClient
from controllers.v1.agent.tools.registry import AGENT_TOOLS_SCHEMA
from controllers.v1.agent.tools.search import execute_search_jira_issues
from controllers.v1.agent.tools.issue import execute_get_ticket_details, execute_get_ticket_comments
from controllers.v1.agent.tools.link import execute_get_linked_evidence
from utils.telemetry import TelemetryCollector
from utils.context import settings

class LLMAgentAdapter:
    """
    LLM-driven Agent Adapter using OpenAI/Gemini/Anthropic Function Calling specs.
    Binds the 4 assessment Jira tools into dynamic LLM execution loops.
    """

    def __init__(
        self,
        jira_client: BaseJiraClient,
        telemetry: Optional[TelemetryCollector] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        self.jira_client = jira_client
        self.telemetry = telemetry or TelemetryCollector()
        self.api_key = api_key or settings.openai_api_key or settings.gemini_api_key
        self.model_name = model_name or settings.llm_model
        self.tools_schema = AGENT_TOOLS_SCHEMA

    def execute_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatches incoming LLM tool calls directly to our assessment tool implementations.
        """
        if tool_name == "search_jira_issues":
            jql = arguments.get("jql") or arguments.get("jql_query", "")
            max_results = arguments.get("max_results", 20)
            return execute_search_jira_issues(self.jira_client, jql, max_results=max_results, telemetry=self.telemetry)
        
        elif tool_name == "get_ticket_details":
            issue_key = arguments.get("issue_key", "")
            return execute_get_ticket_details(self.jira_client, issue_key, telemetry=self.telemetry)
        
        elif tool_name == "get_ticket_comments":
            issue_key = arguments.get("issue_key", "")
            return execute_get_ticket_comments(self.jira_client, issue_key, telemetry=self.telemetry)
        
        elif tool_name == "get_linked_evidence":
            issue_key = arguments.get("issue_key", "")
            return execute_get_linked_evidence(self.jira_client, issue_key, telemetry=self.telemetry)
        
        return {"error": f"Unknown tool: {tool_name}"}

    def get_system_prompt(self, target_release: str = "R2.4", target_commit: str = "b7a91f2") -> str:
        """
        Returns the core system prompt guiding the LLM ReAct investigation loop.
        """
        return f"""You are the Yellow Network Release Evidence AI Agent.
Your mission is to autonomously inspect Jira Cloud to verify whether Release {target_release} (target commit {target_commit}) is ready for production deployment.

You have access to 4 investigation tools:
1. search_jira_issues(jql)
2. get_ticket_details(issue_key)
3. get_ticket_comments(issue_key)
4. get_linked_evidence(issue_key)

Rules:
- For every requirement, search for relevant Jira tickets scoped to label 'tyn-release-assessment-v2'.
- Check comments for actor roles, timestamps, environments, and commit hashes.
- Follow linked blocker issues to verify if fixes or defects remain open.
- Provide clear evidence citations (Ticket keys, comments, actors) for every decision (PASS, FAIL, INSUFFICIENT_EVIDENCE).
"""

