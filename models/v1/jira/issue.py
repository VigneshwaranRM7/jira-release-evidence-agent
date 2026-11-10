from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class JiraComment(BaseModel):
    id: Optional[str] = None
    author: Optional[str] = None
    created: Optional[str] = None
    body: str
    scenario_actor: Optional[str] = None
    scenario_role: Optional[str] = None
    scenario_timestamp: Optional[str] = None

class JiraIssueLink(BaseModel):
    id: Optional[str] = None
    relationship: str = "relates to"
    inward_issue_key: Optional[str] = None
    outward_issue_key: Optional[str] = None
    target_key: str

class JiraIssue(BaseModel):
    id: Optional[str] = None
    key: str
    source_id: str
    summary: str
    description: str
    status: str
    kind: str
    release: Optional[str] = None
    labels: List[str] = Field(default_factory=list)
    comments: List[JiraComment] = Field(default_factory=list)
    links: List[str] = Field(default_factory=list)
    created: Optional[str] = None
    updated: Optional[str] = None

class JiraSearchResult(BaseModel):
    total: int
    issues: List[JiraIssue]

