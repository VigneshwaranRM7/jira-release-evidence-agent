from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from models.v1.jira.dataset import TargetBuildConfig

class AssessmentManifestItem(BaseModel):
    requirement_id: str
    title: str
    acceptance_criteria: str
    mandatory: bool = True

class AssessmentManifest(BaseModel):
    source_id: str = "MANIFEST"
    target: TargetBuildConfig
    mandatory_requirement_ids: List[str] = Field(default_factory=list)
    assessment_rules_text: str = ""
    requirements: List[AssessmentManifestItem] = Field(default_factory=list)
