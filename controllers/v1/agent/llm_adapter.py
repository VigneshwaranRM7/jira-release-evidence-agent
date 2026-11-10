import os
import json
import time
from typing import List, Dict, Any, Optional
from openai import OpenAI
from controllers.v1.jira.base_client import BaseJiraClient
from controllers.v1.agent.tools.registry import AGENT_TOOLS_SCHEMA
from controllers.v1.agent.tools.search import execute_search_jira_issues
from controllers.v1.agent.tools.issue import execute_get_ticket_details, execute_get_ticket_comments
from controllers.v1.agent.tools.link import execute_get_linked_evidence
from models.v1.assessment.manifest import AssessmentManifestItem
from models.v1.assessment.decision import RequirementEvaluation
from definitions import RequirementDecision
from utils.telemetry import TelemetryCollector
from utils.context import settings

class LLMAgentAdapter:
    """
    LLM-driven Agent Adapter using OpenAI/Gemini Function Calling specs.
    Executes an autonomous ReAct loop where the model selects tool calls to investigate Jira evidence.
    """

    def __init__(
        self,
        jira_client: BaseJiraClient,
        telemetry: Optional[TelemetryCollector] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        self.jira_client = jira_client
        self.telemetry = telemetry or TelemetryCollector()
        self.model_name = model_name or settings.llm_model
        self.tools_schema = AGENT_TOOLS_SCHEMA

        # Determine client configuration (OpenAI vs Gemini OpenAI-compatible endpoint)
        gemini_key = settings.gemini_api_key
        openai_key = settings.openai_api_key or api_key

        if openai_key:
            self.client = OpenAI(api_key=openai_key)
            self.model_name = self.model_name or "gpt-4o-mini"
        elif gemini_key:
            self.client = OpenAI(
                api_key=gemini_key,
                base_url=base_url or "https://generativelanguage.googleapis.com/v1beta/openai/"
            )
            self.model_name = self.model_name or "gemini-2.0-flash"
        else:
            self.client = None

    def get_system_prompt(self, target_release: str = "R2.4", target_commit: str = "b7a91f2") -> str:
        from controllers.v1.agent.prompts import build_system_prompt
        return build_system_prompt({"release": target_release, "commit": target_commit})

    def execute_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches model tool calls to Jira evidence tools."""
        if tool_name == "search_jira_issues":
            jql = arguments.get("jql") or arguments.get("jql_query", "")
            max_results = arguments.get("max_results", 15)
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

    def evaluate_requirement(
        self,
        item: AssessmentManifestItem,
        system_prompt: str,
        max_steps: int = 6
    ) -> Optional[RequirementEvaluation]:
        """
        Runs an autonomous tool-calling investigation loop with the LLM for a single requirement.
        """
        if not self.client:
            return None

        user_prompt = f"""Investigate Requirement: {item.requirement_id} - {item.title}
Acceptance Criterion: {item.acceptance_criteria}

Begin by inspecting the requirement ticket ({item.requirement_id}), discovering linked evidence, examining comments, and checking for defects or retests. When you have gathered conclusive evidence, respond with your evaluation JSON:
{{
  "decision": "PASS" | "FAIL" | "INSUFFICIENT_EVIDENCE",
  "explanation": "...",
  "evidence_ticket_keys": [...],
  "evidence_comment_references": [...],
  "outstanding_verification_or_clarification": "..."
}}"""

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        investigated_keys: List[str] = [item.requirement_id]

        for step in range(max_steps):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    tools=self.tools_schema,
                    tool_choice="auto",
                    temperature=0.0
                )
            except Exception as e:
                print(f"LLM API error on step {step+1}: {e}")
                break

            choice = response.choices[0]
            msg = choice.message
            usage = response.usage
            if usage:
                self.telemetry.add_tokens(
                    prompt=usage.prompt_tokens or 0,
                    completion=usage.completion_tokens or 0
                )

            # If model requested tool calls, execute them
            if msg.tool_calls:
                messages.append(msg)
                for tool_call in msg.tool_calls:
                    fn_name = tool_call.function.name
                    try:
                        fn_args = json.loads(tool_call.function.arguments)
                    except Exception:
                        fn_args = {}

                    if "issue_key" in fn_args and fn_args["issue_key"] not in investigated_keys:
                        investigated_keys.append(fn_args["issue_key"])

                    tool_result = self.execute_tool_call(fn_name, fn_args)
                    # Trim tool output string to avoid exceeding context
                    res_str = json.dumps(tool_result)
                    if len(res_str) > 3000:
                        res_str = res_str[:3000] + "... [trimmed]"

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": fn_name,
                        "content": res_str
                    })
            else:
                # Model provided final text
                content = msg.content or ""
                eval_res = self._parse_evaluation_json(
                    content,
                    item=item,
                    investigated_keys=investigated_keys
                )
                if eval_res:
                    return eval_res
                break

        return None

    def _parse_evaluation_json(
        self,
        text: str,
        item: AssessmentManifestItem,
        investigated_keys: List[str]
    ) -> Optional[RequirementEvaluation]:
        """Extracts JSON structure from LLM response text."""
        # Find JSON substring
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            raw_json = text[start:end+1]
            try:
                data = json.loads(raw_json)
                decision_str = str(data.get("decision", "INSUFFICIENT_EVIDENCE")).upper()
                if "PASS" in decision_str:
                    dec = RequirementDecision.PASS
                elif "FAIL" in decision_str:
                    dec = RequirementDecision.FAIL
                else:
                    dec = RequirementDecision.INSUFFICIENT_EVIDENCE

                return RequirementEvaluation(
                    requirement_id=item.requirement_id,
                    requirement_summary=item.title,
                    acceptance_criterion=item.acceptance_criteria,
                    decision=dec,
                    explanation=data.get("explanation", text[:200]),
                    evidence_ticket_keys=data.get("evidence_ticket_keys", []),
                    evidence_comment_references=data.get("evidence_comment_references", []),
                    outstanding_verification_or_clarification=data.get("outstanding_verification_or_clarification"),
                    investigated_keys=list(set(investigated_keys + data.get("evidence_ticket_keys", [])))
                )
            except Exception:
                pass
        return None
