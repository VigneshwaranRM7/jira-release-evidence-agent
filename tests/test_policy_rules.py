import pytest
from controllers.v1.assessment.policy_rules import ReleasePolicyAuditor
from controllers.v1.agent.engine import AgentEngine
from controllers.v1.assessment.orchestrator import orchestrator
from models.v1.assessment.decision import RequirementDecision, ReleaseDecision
from models.v1.assessment.report import AssessmentRunRequest

def test_full_policy_evaluation_decisions(mock_client):
    request = AssessmentRunRequest(target_release="R2.4", force_mock=True)
    report, trace = orchestrator.run_assessment(request)

    assert report.summary.overall_decision == ReleaseDecision.BLOCKED
    assert report.summary.total_requirements == 12
    assert report.summary.passed_count == 4
    assert report.summary.failed_count == 7
    assert report.summary.insufficient_count == 1

    decisions_map = {r.requirement_id: r.decision for r in report.requirements}

    # Verify exact decisions matching manifest acceptance criteria
    assert decisions_map["REQ-01"] == RequirementDecision.PASS
    assert decisions_map["REQ-02"] == RequirementDecision.FAIL
    assert decisions_map["REQ-03"] == RequirementDecision.FAIL
    assert decisions_map["REQ-04"] == RequirementDecision.PASS
    assert decisions_map["REQ-05"] == RequirementDecision.FAIL
    assert decisions_map["REQ-06"] == RequirementDecision.FAIL
    assert decisions_map["REQ-07"] == RequirementDecision.PASS
    assert decisions_map["REQ-08"] == RequirementDecision.FAIL
    assert decisions_map["REQ-09"] == RequirementDecision.FAIL
    assert decisions_map["REQ-10"] == RequirementDecision.PASS
    assert decisions_map["REQ-11"] == RequirementDecision.INSUFFICIENT_EVIDENCE
    assert decisions_map["REQ-12"] == RequirementDecision.FAIL

def test_release_synthesis_logic():
    auditor = ReleasePolicyAuditor()
    from models.v1.assessment.decision import RequirementEvaluation

    # 1. Blocked when any failure
    evals_blocked = [
        RequirementEvaluation(requirement_id="REQ-01", requirement_summary="Reg", acceptance_criterion="Pass", decision=RequirementDecision.PASS, explanation="ok"),
        RequirementEvaluation(requirement_id="REQ-02", requirement_summary="Iso", acceptance_criterion="Pass", decision=RequirementDecision.FAIL, explanation="defect")
    ]
    summary_blocked = auditor.synthesize_release_decision(evals_blocked)
    assert summary_blocked.overall_decision == ReleaseDecision.BLOCKED
    assert summary_blocked.failed_count == 1

    # 2. Needs review when no failures but insufficient
    evals_review = [
        RequirementEvaluation(requirement_id="REQ-01", requirement_summary="Reg", acceptance_criterion="Pass", decision=RequirementDecision.PASS, explanation="ok"),
        RequirementEvaluation(requirement_id="REQ-11", requirement_summary="Kbd", acceptance_criterion="Pass", decision=RequirementDecision.INSUFFICIENT_EVIDENCE, explanation="missing")
    ]
    summary_review = auditor.synthesize_release_decision(evals_review)
    assert summary_review.overall_decision == ReleaseDecision.NEEDS_REVIEW
    assert summary_review.insufficient_count == 1

    # 3. Ready when all pass
    evals_ready = [
        RequirementEvaluation(requirement_id="REQ-01", requirement_summary="Reg", acceptance_criterion="Pass", decision=RequirementDecision.PASS, explanation="ok"),
        RequirementEvaluation(requirement_id="REQ-04", requirement_summary="Perf", acceptance_criterion="Pass", decision=RequirementDecision.PASS, explanation="ok")
    ]
    summary_ready = auditor.synthesize_release_decision(evals_ready)
    assert summary_ready.overall_decision == ReleaseDecision.READY
    assert summary_ready.passed_count == 2

