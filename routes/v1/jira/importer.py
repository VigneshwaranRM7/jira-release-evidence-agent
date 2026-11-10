import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from definitions import DATA_DIR
from controllers.v1.jira.bulk_importer import JiraBulkImporter
from controllers.v1.jira.mock_client import MockJiraClient
from controllers.v1.jira.cloud_client import JiraCloudClient
from utils.context import settings

router = APIRouter(prefix="/jira", tags=["Jira Operations"])

class ImportRequest(BaseModel):
    file_path: Optional[str] = None
    project_key: str = "REL"
    force_mock: bool = False

@router.post("/import")
def trigger_jira_import(req: ImportRequest = ImportRequest()):
    """
    Trigger repeatable bulk import of dataset records into Jira Cloud (or Mock Jira).
    Executes 2-pass import: Pass 1 creates issues and comments; Pass 2 links dependencies.
    """
    file_path = req.file_path or os.path.join(DATA_DIR, "dataset.json")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Dataset file not found at: {file_path}")

    # Determine target client
    if not req.force_mock and settings.JIRA_BASE_URL and settings.JIRA_API_TOKEN:
        client = JiraCloudClient(
            base_url=settings.JIRA_BASE_URL,
            user_email=settings.JIRA_USER_EMAIL,
            api_token=settings.JIRA_API_TOKEN
        )
    else:
        client = MockJiraClient()

    importer = JiraBulkImporter(client=client)
    try:
        stats = importer.import_from_json(file_path, project_key=req.project_key)
        return {
            "status": "success",
            "project_key": req.project_key,
            "target": "cloud" if isinstance(client, JiraCloudClient) else "mock",
            "imported_issues": stats.get("issues_created", 0),
            "imported_comments": stats.get("comments_created", 0),
            "created_links": stats.get("links_created", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
