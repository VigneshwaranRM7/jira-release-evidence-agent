from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class ToolInvocation(BaseModel):
    step_index: int
    tool_name: str
    arguments: Dict[str, Any]
    output_summary: str
    raw_output: Any
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    duration_ms: float

class InvestigationTrace(BaseModel):
    assessment_id: str
    target_release: str
    total_tool_calls: int
    tool_invocations: List[ToolInvocation]
    total_execution_time_seconds: float
    token_usage: Dict[str, int] = Field(default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
    cost_usd: float = 0.0
    model_name: Optional[str] = "gemini-2.0-flash"
