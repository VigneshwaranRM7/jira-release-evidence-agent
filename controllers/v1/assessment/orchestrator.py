import os
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
    Manages client selection, manifest building, agent investigation,
    deliverable serialization, and session caching.
    """

    def __init__(self):
        self._reports_cache: Dict[str, ReleaseReadinessReport] = {}
        self._traces_cache: Dict[str, InvestigationTrace] = {}

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
                title="Prompt answer quality",
                acceptance_criteria="The exact prompt version deployed to production must meet or exceed quality benchmarks without regression.",
                mandatory=True
            ),
            AssessmentManifestItem(
                requirement_id="REQ-04",
                title="End-to-end latency",
                acceptance_criteria="p95 latency under simulated peak load must not exceed 2.0 seconds.",
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
                acceptance_criteria="Security team approval for target build and production environment is required before release.",
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
                acceptance_criteria="Rollback drill must succeed without session data loss or corruption.",
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
                acceptance_criteria="Audit must verify 100% keyboard navigability on the target release build.",
                mandatory=True
            ),
            AssessmentManifestItem(
                requirement_id="REQ-12",
                title="Streaming response integrity",
                acceptance_criteria="Streaming responses must deliver complete tokens without duplication, truncation, or out-of-order chunks.",
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

    def _resolve_client(self, force_mock: bool = False) -> BaseJiraClient:
        if not force_mock and settings.JIRA_BASE_URL and settings.JIRA_API_TOKEN:
            try:
                client = JiraCloudClient(
                    base_url=settings.JIRA_BASE_URL,
                    user_email=settings.JIRA_USER_EMAIL,
                    api_token=settings.JIRA_API_TOKEN
                )
                return client
            except Exception:
                pass

        # Fallback to Mock Client with loaded dataset
        mock_client = MockJiraClient()
        dataset_file = os.path.join(DATA_DIR, "dataset.json")
        if os.path.exists(dataset_file):
            mock_client.load_from_json(dataset_file)
        return mock_client

    def run_assessment(self, request: AssessmentRunRequest) -> Tuple[ReleaseReadinessReport, InvestigationTrace]:
        assessment_id = f"assess-{uuid.uuid4().hex[:8]}"
        telemetry = TelemetryCollector()

        # Build target configuration
        target = TargetBuildConfig(
            release=request.target_release or DEFAULT_TARGET_RELEASE,
            commit=DEFAULT_TARGET_COMMIT,
            prompt=DEFAULT_TARGET_PROMPT,
            service=DEFAULT_TARGET_SERVICE,
            environment=DEFAULT_TARGET_ENV
        )

        manifest = self.get_default_manifest(target)
        client = self._resolve_client(force_mock=request.force_mock or False)

        auditor = ReleasePolicyAuditor(
            target_release=target.release,
            target_commit=target.commit,
            target_prompt=target.prompt,
            target_env=target.environment,
            target_service=target.service
        )

        engine = AgentEngine(jira_client=client, telemetry=telemetry, auditor=auditor)
        
        # Execute investigation
        evaluations, decision_summary = engine.run_full_investigation(manifest)

        # Assemble Report
        report = ReleaseReadinessReport(
            assessment_id=assessment_id,
            dataset_label=request.dataset_label,
            summary=decision_summary,
            requirements=evaluations,
            metadata={
                "project_key": request.project_key,
                "target_build": target.model_dump(),
                "client_mode": "mock" if isinstance(client, MockJiraClient) else "cloud"
            }
        )

        # Assemble Trace
        trace = telemetry.to_investigation_trace(
            assessment_id=assessment_id,
            target_release=target.release,
            model_name="yellow-agent-engine-v1"
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

