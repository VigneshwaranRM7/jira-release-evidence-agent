from fastapi import APIRouter
from routes.v1.system.health import router as health_router
from routes.v1.jira.importer import router as jira_router
from routes.v1.assessment.assessment import router as assessment_router
from routes.v1.assessment.report import router as report_router
from routes.v1.assessment.trace import router as trace_router

api_v1_router = APIRouter(prefix="/api/v1")

# Mount sub-routers
api_v1_router.include_router(health_router)
api_v1_router.include_router(jira_router)
api_v1_router.include_router(assessment_router)
api_v1_router.include_router(report_router)
api_v1_router.include_router(trace_router)

