import time
from typing import List, Dict, Any, Tuple, Optional
from controllers.v1.jira.base_client import BaseJiraClient
from controllers.v1.agent.tools.search import execute_search_jira_issues
from controllers.v1.agent.tools.issue import execute_get_ticket_details, execute_get_ticket_comments
from controllers.v1.agent.tools.link import execute_get_linked_evidence
from controllers.v1.agent.llm_adapter import LLMAgentAdapter
from controllers.v1.agent.prompts import build_system_prompt
from controllers.v1.assessment.policy_rules import ReleasePolicyAuditor
from models.v1.assessment.manifest import AssessmentManifest, AssessmentManifestItem
from models.v1.assessment.decision import RequirementEvaluation, ReleaseDecisionSummary
from models.v1.jira.issue import JiraIssue
from utils.telemetry import TelemetryCollector

class AgentEngine:
    """
    Autonomous Investigation Engine for Jira evidence.
    Leverages LLM tool-calling (ReAct) with fallback to deterministic graph evidence traversal.
    Captures complete tool telemetry, tokens, latency, and cost numbers.
    """

    def __init__(
        self,
        jira_client: BaseJiraClient,
        telemetry: Optional[TelemetryCollector] = None,
        auditor: Optional[ReleasePolicyAuditor] = None,
        target_config: Optional[Dict[str, str]] = None
    ):
        self.jira_client = jira_client
        self.telemetry = telemetry or TelemetryCollector()
        self.auditor = auditor or ReleasePolicyAuditor()
        self.target_config = target_config or {
            "service": "atlas-assistant",
            "release": "R2.4",
            "commit": "b7a91f2",
            "prompt": "p7",
            "environment": "production"
        }
        self.system_prompt = build_system_prompt(self.target_config)
        self.llm_adapter = LLMAgentAdapter(
            jira_client=self.jira_client,
            telemetry=self.telemetry
        )

    def investigate_requirement(
        self,
        item: AssessmentManifestItem
    ) -> RequirementEvaluation:
        """
        Executes autonomous investigation for a single manifest requirement.
        Tries real LLM tool-calling loop first; falls back to autonomous tool traversal.
        """
        # 1. Attempt LLM tool-calling loop if LLM client is configured
        if self.llm_adapter and self.llm_adapter.client:
            try:
                eval_from_llm = self.llm_adapter.evaluate_requirement(
                    item=item,
                    system_prompt=self.system_prompt,
                    max_steps=6
                )
                if eval_from_llm:
                    return eval_from_llm
            except Exception as e:
                print(f"Notice: LLM evaluation encountered '{e}', continuing with autonomous evidence traversal.")

        # 2. Autonomous Jira evidence tool traversal (zero hardcoded queries)
        investigated_issues: Dict[str, JiraIssue] = {}
        linked_issues: List[JiraIssue] = []
        found_keys: List[str] = [item.requirement_id]

        # Inspect requirement ticket
        details = execute_get_ticket_details(self.jira_client, item.requirement_id, telemetry=self.telemetry)
        if "error" not in details:
            iss_obj = self.jira_client.get_issue(item.requirement_id)
            if iss_obj:
                investigated_issues[iss_obj.key] = iss_obj

        # Discover linked evidence
        link_res = execute_get_linked_evidence(self.jira_client, item.requirement_id, telemetry=self.telemetry)
        for lk in link_res.get("linked_keys", []):
            if lk not in found_keys:
                found_keys.append(lk)

        # Context search using requirement ID
        search_res = execute_search_jira_issues(
            self.jira_client,
            f'labels = "tyn-release-assessment-v2" AND text ~ "{item.requirement_id}"',
            max_results=10,
            telemetry=self.telemetry
        )
        for iss_data in search_res.get("issues", []):
            k = iss_data.get("key")
            if k and k not in found_keys:
                found_keys.append(k)

        # Inspect discovered tickets, comments, and deep links (e.g. blocking defects)
        for key in found_keys:
            execute_get_ticket_details(self.jira_client, key, telemetry=self.telemetry)
            issue_obj = self.jira_client.get_issue(key)
            if issue_obj:
                investigated_issues[issue_obj.key] = issue_obj
                linked_issues.append(issue_obj)

            # Retrieve comments
            execute_get_ticket_comments(self.jira_client, key, telemetry=self.telemetry)

            # Traverse secondary links (e.g., defects linked to test runs)
            sub_links = execute_get_linked_evidence(self.jira_client, key, telemetry=self.telemetry)
            for sub_k in sub_links.get("linked_keys", []):
                if sub_k not in investigated_issues:
                    sub_obj = self.jira_client.get_issue(sub_k)
                    if sub_obj:
                        investigated_issues[sub_obj.key] = sub_obj
                        execute_get_ticket_comments(self.jira_client, sub_k, telemetry=self.telemetry)

        # 3. Policy evaluation against manifest rules
        evaluation = self.auditor.audit_requirement(
            req_id=item.requirement_id,
            req_summary=item.title,
            criterion=item.acceptance_criteria,
            linked_issues=linked_issues,
            all_investigated_issues=investigated_issues
        )

        return evaluation

    def run_full_investigation(
        self,
        manifest: AssessmentManifest
    ) -> Tuple[List[RequirementEvaluation], ReleaseDecisionSummary]:
        """
        Investigates all requirements in manifest and synthesizes roll-up decision.
        """
        evaluations: List[RequirementEvaluation] = []
        for item in manifest.requirements:
            eval_res = self.investigate_requirement(item)
            evaluations.append(eval_res)

        summary = self.auditor.synthesize_release_decision(evaluations)
        return evaluations, summary
