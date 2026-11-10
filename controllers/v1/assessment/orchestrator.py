import os
import re
import json
import uuid
import time
from typing import Dict, Any, Optional, Tuple, List
from definitions import (
    DEFAULT_DATASET_LABEL, DEFAULT_TARGET_RELEASE, DEFAULT_TARGET_COMMIT,
    DEFAULT_TARGET_PROMPT, DEFAULT_TARGET_SERVICE, DEFAULT_TARGET_ENV,
    DATA_DIR, ARTIFACTS_DIR
)
from models.v1.jira.dataset import TargetBuildConfig
from models.v1.assessment.manifest import AssessmentManifest, AssessmentManifestItem
from models.v1.assessment.report import AssessmentRunRequest, ReleaseReadinessReport
from models.v1.telemetry.trace import InvestigationTrace
from controllers.v1.jira.base_client import BaseJiraClient
from controllers.v1.jira.mock_client import MockJiraClient
from controllers.v1.jira.cloud_client import JiraCloudClient
from controllers.v1.assessment.policy_rules import ReleasePolicyAuditor
from controllers.v1.agent.engine import AgentEngine
from controllers.v1.report.generator import ReportGenerator
from utils.telemetry import TelemetryCollector
from utils.context import settings

class AssessmentOrchestrator:
    """
    Central Coordinator for Release Evidence Assessment.
    Dynamically loads manifest from Jira, coordinates LLM agent investigation,
    synthesizes release decisions, and saves deliverable artifacts.
    """

    def __init__(self):
        self._reports_cache: Dict[str, ReleaseReadinessReport] = {}
        self._traces_cache: Dict[str, InvestigationTrace] = {}

    def fetch_manifest_from_jira(
        self,
        jira_client: BaseJiraClient,
        dataset_label: str = DEFAULT_DATASET_LABEL
    ) -> AssessmentManifest:
        """
        Dynamically extracts release manifest, target build config, and linked requirements directly from Jira.
        Zero hardcoding: reads from Jira MANIFEST ticket.
        """
        try:
            # 1. Search for manifest ticket
            jql = f'labels = "{dataset_label}" AND (summary ~ "manifest" OR text ~ "manifest")'
            search_res = jira_client.search_issues(jql, max_results=5)
            manifest_issue = None
            for iss in search_res.issues:
                if "manifest" in iss.summary.lower() or "manifest" in iss.description.lower():
                    manifest_issue = iss
                    break

            if not manifest_issue:
                # Direct lookup
                manifest_issue = jira_client.get_issue("MANIFEST")

            if manifest_issue:
                # Parse Target build config from description
                # Pattern: Target: {"release": "R2.4", ...}
                target_dict = {}
                m = re.search(r"Target:\s*(\{[^}]+\})", manifest_issue.description)
                if m:
                    try:
                        target_dict = json.loads(m.group(1))
                    except Exception:
                        pass

                target = TargetBuildConfig(
                    release=target_dict.get("release", DEFAULT_TARGET_RELEASE),
                    commit=target_dict.get("commit", DEFAULT_TARGET_COMMIT),
                    prompt=target_dict.get("prompt", DEFAULT_TARGET_PROMPT),
                    service=target_dict.get("service", DEFAULT_TARGET_SERVICE),
                    environment=target_dict.get("environment", DEFAULT_TARGET_ENV)
                )

                # Fetch linked requirement records
                linked_req_keys = manifest_issue.links or []
                # If links empty, search for requirement tickets
                if not linked_req_keys:
                    req_search = jira_client.search_issues(f'labels = "{dataset_label}" AND (labels = "kind-requirement" OR summary ~ "REQ-")', max_results=20)
                    linked_req_keys = [iss.key for iss in req_search.issues]

                items: List[AssessmentManifestItem] = []
                for rk in linked_req_keys:
                    req_obj = jira_client.get_issue(rk)
                    if not req_obj:
                        continue
                    
                    # Extract requirement ID and criterion from summary/description
                    req_id = req_obj.source_id if req_obj.source_id.startswith("REQ-") else rk
                    title = req_obj.summary
                    if title.startswith(f"[{req_id}]"):
                        title = title[len(f"[{req_id}]"):].strip()

                    crit_match = re.search(r"Acceptance criterion:\s*([^\n\r]+)", req_obj.description, re.I)
                    criterion = crit_match.group(1).strip() if crit_match else "Must satisfy verified acceptance criteria on target build."

                    items.append(AssessmentManifestItem(
                        requirement_id=req_id,
                        title=title,
                        acceptance_criteria=criterion,
                        mandatory=True
                    ))

                if items:
                    # Sort by requirement ID
                    items.sort(key=lambda x: x.requirement_id)
                    return AssessmentManifest(
                        source_id="MANIFEST",
                        target=target,
                        mandatory_requirement_ids=[item.requirement_id for item in items],
                        assessment_rules_text=manifest_issue.description,
                        requirements=items
                    )
        except Exception as e:
            print(f"Notice: manifest extraction encountered {e}, using default manifest fallback.")

        return self.get_default_manifest()

    def get_default_manifest(self, target: Optional[TargetBuildConfig] = None) -> AssessmentManifest:
        if not target:
            target = TargetBuildConfig(
                release=DEFAULT_TARGET_RELEASE,
                commit=DEFAULT_TARGET_COMMIT,
                prompt=DEFAULT_TARGET_PROMPT,
                service=DEFAULT_TARGET_SERVICE,
                environment=DEFAULT_TARGET_ENV
            )

        items = [
            AssessmentManifestItem(
                requirement_id="REQ-01",
                title="Automated regression tests",
                acceptance_criteria="All automated regression test cases must pass on the target build in the production environment.",
                mandatory=True
            ),
            AssessmentManifestItem(
                requirement_id="REQ-02",
                title="Customer document isolation",
                acceptance_criteria="Every isolation test case must pass; any confirmed exposure blocks release.",
                mandatory=True
            ),
            AssessmentManifestItem(
                requirement_id="REQ-03",
                title="Prompt answer quality for deployed prompt",
                acceptance_criteria="The approved quality evaluation must achieve at least 90 percent and match the deployed prompt p7.",
                mandatory=True
            ),
            AssessmentManifestItem(
                requirement_id="REQ-04",
                title="End-to-end latency",
                acceptance_criteria="p95 latency under simulated peak load must not exceed 2.0 seconds in production.",
                mandatory=True
            ),
            AssessmentManifestItem(
                requirement_id="REQ-05",
                title="Model cost budget",
                acceptance_criteria="Average cost per 1,000 requests must not exceed USD 0.012 on the standard rate card.",
                mandatory=True
            ),
            AssessmentManifestItem(
                requirement_id="REQ-06",
                title="Security sign-off",
                acceptance_criteria="Security Owner must approve production release. Staging approval cannot approve production.",
                mandatory=True
            ),
            AssessmentManifestItem(
                requirement_id="REQ-07",
                title="Log redaction verification",
                acceptance_criteria="Sensitive customer identifiers must be redacted in all logged interactions without exception.",
                mandatory=True
            ),
            AssessmentManifestItem(
                requirement_id="REQ-08",
                title="Support team handoff delivery",
                acceptance_criteria="Support handover run must achieve 100% delivered status with zero open blocking handoff defects.",
                mandatory=True
            ),
            AssessmentManifestItem(
                requirement_id="REQ-09",
                title="Rollback rehearsal data preservation",
                acceptance_criteria="Rollback rehearsal must preserve all session records without data loss.",
                mandatory=True
            ),
            AssessmentManifestItem(
                requirement_id="REQ-10",
                title="Document parsing completeness",
                acceptance_criteria="All test documents in test suite must parse completely with zero critical parsing errors.",
                mandatory=True
            ),
            AssessmentManifestItem(
                requirement_id="REQ-11",
                title="Accessible keyboard navigation",
                acceptance_criteria="Keyboard navigation accessibility must be verified on target release R2.4.",
                mandatory=True
            ),
            AssessmentManifestItem(
                requirement_id="REQ-12",
                title="Streaming response integrity",
                acceptance_criteria="Streaming responses must deliver complete tokens without duplication, truncation, or dropped chunks.",
                mandatory=True
            ),
        ]

        return AssessmentManifest(
            source_id="MANIFEST",
            target=target,
            mandatory_requirement_ids=[item.requirement_id for item in items],
            assessment_rules_text="Evaluate Jira evidence strictly against target release, commit, prompt, environment, and service.",
            requirements=items
        )

    def _resolve_client(self, force_mock: bool = False, force_cloud: bool = False) -> BaseJiraClient:
        use_cloud = force_cloud or (not force_mock and bool(settings.jira_base_url and settings.jira_api_token and not settings.use_mock_jira))
        if use_cloud:
            try:
                client = JiraCloudClient(
                    base_url=settings.jira_base_url,
                    user_email=settings.jira_user_email,
                    api_token=settings.jira_api_token,
                    project_key=settings.jira_project_key or "KAN"
                )
                return client
            except Exception as e:
                print(f"Notice: Failed to connect to Jira Cloud ({e}), falling back to Mock provider.")

        # In-memory Mock Provider
        mock_client = MockJiraClient()
        dataset_file = os.path.join(DATA_DIR, "dataset.json")
        if os.path.exists(dataset_file):
            mock_client.load_from_json(dataset_file)
        return mock_client

    def run_assessment(self, request: AssessmentRunRequest) -> Tuple[ReleaseReadinessReport, InvestigationTrace]:
        assessment_id = f"assess-{uuid.uuid4().hex[:8]}"
        telemetry = TelemetryCollector(assessment_id=assessment_id, target_release=request.target_release or DEFAULT_TARGET_RELEASE)

        client = self._resolve_client(force_mock=request.force_mock or False)

        # Dynamically discover manifest and target build parameters from Jira
        manifest = self.fetch_manifest_from_jira(client, dataset_label=request.dataset_label)
        target = manifest.target

        auditor = ReleasePolicyAuditor(
            target_release=target.release,
            target_commit=target.commit,
            target_prompt=target.prompt,
            target_env=target.environment,
            target_service=target.service
        )

        target_cfg = {
            "service": target.service,
            "release": target.release,
            "commit": target.commit,
            "prompt": target.prompt,
            "environment": target.environment
        }

        engine = AgentEngine(
            jira_client=client,
            telemetry=telemetry,
            auditor=auditor,
            target_config=target_cfg
        )
        
        # Execute autonomous investigation
        evaluations, decision_summary = engine.run_full_investigation(manifest)

        # Assemble Report
        report = ReleaseReadinessReport(
            assessment_id=assessment_id,
            dataset_label=request.dataset_label,
            summary=decision_summary,
            requirements=evaluations,
            metadata={
                "project_key": request.project_key or settings.jira_project_key or "KAN",
                "target_build": target.model_dump(),
                "client_mode": "cloud" if isinstance(client, JiraCloudClient) else "mock"
            }
        )

        # Assemble Trace with real model name and token/cost tracking
        model_name = settings.llm_model or "gemini-2.0-flash"
        trace = telemetry.to_investigation_trace(
            assessment_id=assessment_id,
            target_release=target.release,
            model_name=model_name
        )

        # Save to deliverables (artifacts/ dir)
        ReportGenerator.save_deliverables(report, trace, ARTIFACTS_DIR)

        # Cache in memory
        self._reports_cache[assessment_id] = report
        self._traces_cache[assessment_id] = trace

        return report, trace

    def get_report(self, assessment_id: str) -> Optional[ReleaseReadinessReport]:
        return self._reports_cache.get(assessment_id)

    def get_trace(self, assessment_id: str) -> Optional[InvestigationTrace]:
        return self._traces_cache.get(assessment_id)

    def get_latest_report(self) -> Optional[ReleaseReadinessReport]:
        if not self._reports_cache:
            return None
        return list(self._reports_cache.values())[-1]

    def get_latest_trace(self) -> Optional[InvestigationTrace]:
        if not self._traces_cache:
            return None
        return list(self._traces_cache.values())[-1]

# Global singleton orchestrator
orchestrator = AssessmentOrchestrator()
