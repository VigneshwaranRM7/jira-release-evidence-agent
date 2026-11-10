from fastapi import APIRouter, HTTPException, BackgroundTasks
from models.v1.assessment.report import AssessmentRunRequest, ReleaseReadinessReport
from controllers.v1.assessment.orchestrator import orchestrator

router = APIRouter(prefix="/assessment", tags=["Assessment Operations"])

@router.post("/run", response_model=ReleaseReadinessReport)
def run_assessment(request: AssessmentRunRequest = AssessmentRunRequest()):
    """
    Run evidence-backed release readiness assessment across all 12 mandatory requirements.
    Coordinates tool-calling agent, policy verification, artifact generation, and returns full report.
    """
    try:
        report, _ = orchestrator.run_assessment(request)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assessment failed: {str(e)}")

@router.get("/{assessment_id}/status")
def get_assessment_status(assessment_id: str):
    """
    Get the current status of an assessment run.
    """
    report = orchestrator.get_report(assessment_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Assessment '{assessment_id}' not found.")
    return {
        "assessment_id": assessment_id,
        "status": "COMPLETED",
        "generated_at": report.generated_at,
        "overall_decision": report.summary.overall_decision
    }
