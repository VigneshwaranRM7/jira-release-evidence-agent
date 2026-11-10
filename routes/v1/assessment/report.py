from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import PlainTextResponse
from controllers.v1.assessment.orchestrator import orchestrator
from controllers.v1.report.generator import ReportGenerator

router = APIRouter(prefix="/assessment", tags=["Assessment Reports"])

@router.get("/{assessment_id}/report")
def get_assessment_report(assessment_id: str, format: str = "json"):
    """
    Fetch generated release-readiness report (JSON or Markdown format).
    Supports 'latest' to retrieve the most recent assessment.
    """
    if assessment_id == "latest":
        report = orchestrator.get_latest_report()
    else:
        report = orchestrator.get_report(assessment_id)

    if not report:
        raise HTTPException(status_code=404, detail=f"Report for assessment '{assessment_id}' not found.")

    if format.lower() == "markdown" or format.lower() == "md":
        md_text = ReportGenerator.generate_markdown_report(report)
        return PlainTextResponse(content=md_text, media_type="text/markdown")

    return report
