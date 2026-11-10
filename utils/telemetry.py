import time
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from models.v1.telemetry.trace import ToolInvocation, InvestigationTrace

class TelemetryCollector:
    def __init__(self, assessment_id: Optional[str] = None, target_release: str = "R2.4"):
        self.assessment_id = assessment_id or f"trace-{uuid.uuid4().hex[:8]}"
        self.target_release = target_release
        self.invocations: List[ToolInvocation] = []
        self.start_time = time.time()
        self.token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    def record_tool_call(self, tool_name: str, arguments: Dict[str, Any], raw_output: Any, output_summary: str, duration_ms: float):
        invocation = ToolInvocation(
            step_index=len(self.invocations) + 1,
            tool_name=tool_name,
            arguments=arguments,
            output_summary=output_summary,
            raw_output=raw_output,
            timestamp=datetime.utcnow().isoformat(),
            duration_ms=round(duration_ms, 2)
        )
        self.invocations.append(invocation)

    def add_tokens(self, prompt: int = 0, completion: int = 0):
        self.token_usage["prompt_tokens"] += prompt
        self.token_usage["completion_tokens"] += completion
        self.token_usage["total_tokens"] += (prompt + completion)

    def build_trace(self, assessment_id: Optional[str] = None, target_release: Optional[str] = None, model_name: str = "heuristic-rule-engine") -> InvestigationTrace:
        elapsed = round(time.time() - self.start_time, 3)
        return InvestigationTrace(
            assessment_id=assessment_id or self.assessment_id,
            target_release=target_release or self.target_release,
            total_tool_calls=len(self.invocations),
            tool_invocations=self.invocations,
            total_execution_time_seconds=elapsed,
            token_usage=self.token_usage,
            model_name=model_name
        )

    def to_investigation_trace(self, assessment_id: Optional[str] = None, target_release: Optional[str] = None, model_name: str = "heuristic-rule-engine") -> InvestigationTrace:
        return self.build_trace(assessment_id=assessment_id, target_release=target_release, model_name=model_name)
