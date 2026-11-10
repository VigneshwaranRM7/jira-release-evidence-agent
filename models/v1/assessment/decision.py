from typing import List, Optional
from pydantic import BaseModel, Field
from definitions import RequirementDecision, ReleaseDecision

class RequirementEvaluation(BaseModel):
    requirement_id: str
    requirement_summary: str
    acceptance_criterion: str
    decision: RequirementDecision
    explanation: str
    evidence_ticket_keys: List[str] = Field(default_factory=list)
    evidence_comment_references: List[str] = Field(default_factory=list)
    outstanding_verification_or_clarification: Optional[str] = None
    investigated_keys: List[str] = Field(default_factory=list)

class ReleaseDecisionSummary(BaseModel):
    overall_decision: ReleaseDecision
    target_release: str
    target_commit: str
    target_service: str
    target_environment: str
    target_prompt: Optional[str] = None
    total_requirements: int
    passed_count: int
    failed_count: int
    insufficient_count: int
    summary_explanation: str

