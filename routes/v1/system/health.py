from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/health", tags=["System"])

@router.get("")
async def health_check():
    return {
        "status": "healthy",
        "service": "jira-release-evidence-agent",
        "timestamp": datetime.utcnow().isoformat()
    }

