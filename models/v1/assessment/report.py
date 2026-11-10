from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from models.v1.assessment.decision import RequirementEvaluation, ReleaseDecisionSummary

class AssessmentRunRequest(BaseModel):
    project_key: Optional[str] = "REL"
    dataset_label: str = "tyn-release-assessment-v2"
    target_release: str = "R2.4"
    force_mock: Optional[bool] = False

class ReleaseReadinessReport(BaseModel):
    assessment_id: str
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    dataset_label: str
    summary: ReleaseDecisionSummary
    requirements: List[RequirementEvaluation]
    metadata: Dict[str, Any] = Field(default_factory=dict)

