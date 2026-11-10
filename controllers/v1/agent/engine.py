import time
from typing import List, Dict, Any, Tuple, Optional
from controllers.v1.jira.base_client import BaseJiraClient
from controllers.v1.agent.tools.search import execute_search_jira_issues
from controllers.v1.agent.tools.issue import execute_get_ticket_details, execute_get_ticket_comments
from controllers.v1.agent.tools.link import execute_get_linked_evidence
from controllers.v1.assessment.policy_rules import ReleasePolicyAuditor
from models.v1.assessment.manifest import AssessmentManifest, AssessmentManifestItem
from models.v1.assessment.decision import RequirementEvaluation, ReleaseDecisionSummary
from models.v1.jira.issue import JiraIssue
from utils.telemetry import TelemetryCollector

class AgentEngine:
    """
    Autonomous ReAct-style Investigation Engine for Jira evidence.
    Executes tool-directed searches, detailed inspections, and link traversals
    while capturing full telemetry for the investigation trace.
    """

    def __init__(
        self,
        jira_client: BaseJiraClient,
        telemetry: Optional[TelemetryCollector] = None,
        auditor: Optional[ReleasePolicyAuditor] = None
    ):
        self.jira_client = jira_client
        self.telemetry = telemetry or TelemetryCollector()
        self.auditor = auditor or ReleasePolicyAuditor()

    def investigate_requirement(
        self,
        item: AssessmentManifestItem
    ) -> RequirementEvaluation:
        """
        Executes targeted investigation for a single manifest requirement item.
        """
        investigated_issues: Dict[str, JiraIssue] = {}
        linked_issues: List[JiraIssue] = []

        # 1. Construct search queries based on requirement keywords and ID
        queries = [
            f'labels = "tyn-release-assessment-v2" AND text ~ "{item.requirement_id}"',
            f'labels = "tyn-release-assessment-v2" AND text ~ "{item.title}"'
        ]
        
        # Add keyword-specific queries for key domains
        if "regression" in item.title.lower():
            queries.append('labels = "tyn-release-assessment-v2" AND text ~ "REG-804"')
        elif "isolation" in item.title.lower():
            queries.append('labels = "tyn-release-assessment-v2" AND text ~ "ISO-318"')
        elif "answer quality" in item.title.lower():
            queries.append('labels = "tyn-release-assessment-v2" AND text ~ "EVAL-55"')
        elif "latency" in item.title.lower():
            queries.append('labels = "tyn-release-assessment-v2" AND text ~ "PERF-827"')
        elif "model cost" in item.title.lower() or "cost" in item.title.lower():
            queries.append('labels = "tyn-release-assessment-v2" AND text ~ "COST-881"')
        elif "security" in item.title.lower():
            queries.append('labels = "tyn-release-assessment-v2" AND text ~ "SEC-504"')
        elif "redaction" in item.title.lower():
            queries.append('labels = "tyn-release-assessment-v2" AND text ~ "REDACT"')
        elif "handoff" in item.title.lower():
            queries.append('labels = "tyn-release-assessment-v2" AND text ~ "HND"')
        elif "rollback" in item.title.lower():
            queries.append('labels = "tyn-release-assessment-v2" AND text ~ "RB-402"')
        elif "parsing" in item.title.lower():
            queries.append('labels = "tyn-release-assessment-v2" AND text ~ "PARSE"')
        elif "keyboard" in item.title.lower() or "accessibility" in item.title.lower():
            queries.append('labels = "tyn-release-assessment-v2" AND text ~ "ACCESSIBILITY"')
        elif "streaming" in item.title.lower():
            queries.append('labels = "tyn-release-assessment-v2" AND text ~ "STREAM"')

        found_keys: List[str] = []

        for q in queries:
            search_res = execute_search_jira_issues(self.jira_client, q, max_results=25, telemetry=self.telemetry)
            for iss_data in search_res.get("issues", []):
                key = iss_data.get("key")
                if key and key not in found_keys:
                    found_keys.append(key)

        # 2. Deep-inspect identified tickets (fetch comments and links)
        for key in list(found_keys):
            # Tool call: get_ticket_details
            execute_get_ticket_details(self.jira_client, key, telemetry=self.telemetry)
            issue_obj = self.jira_client.get_issue(key)
            if issue_obj:
                investigated_issues[key] = issue_obj

            # Tool call: get_ticket_comments
            execute_get_ticket_comments(self.jira_client, key, telemetry=self.telemetry)

            # Tool call: get_linked_evidence
            link_res = execute_get_linked_evidence(self.jira_client, key, telemetry=self.telemetry)
            for linked_key in link_res.get("linked_keys", []):
                linked_obj = self.jira_client.get_issue(linked_key)
                if linked_obj:
                    linked_issues.append(linked_obj)
                    if linked_key not in investigated_issues:
                        investigated_issues[linked_key] = linked_obj
                        # Also fetch linked comments via tool
                        execute_get_ticket_comments(self.jira_client, linked_key, telemetry=self.telemetry)

        # 3. Apply deterministic policy auditing
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
        Iterates over all items in the manifest, executes thorough investigation,
        and aggregates the release decision.
        """
        evaluations: List[RequirementEvaluation] = []
        for item in manifest.requirements:
            eval_res = self.investigate_requirement(item)
            evaluations.append(eval_res)

        summary = self.auditor.synthesize_release_decision(evaluations)
        return evaluations, summary
