from fastapi import APIRouter, HTTPException
from controllers.v1.assessment.orchestrator import orchestrator
from models.v1.telemetry.trace import InvestigationTrace

router = APIRouter(prefix="/assessment", tags=["Assessment Traces"])

@router.get("/{assessment_id}/trace", response_model=InvestigationTrace)
def get_assessment_trace(assessment_id: str):
    """
    Fetch investigation tool execution trace, tool arguments, latency, and token metrics.
    Supports 'latest' to retrieve the most recent assessment trace.
    """
    if assessment_id == "latest":
        trace = orchestrator.get_latest_trace()
    else:
        trace = orchestrator.get_trace(assessment_id)

    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace for assessment '{assessment_id}' not found.")

    return trace
