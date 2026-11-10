from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class TargetBuildConfig(BaseModel):
    release: str
    commit: str
    prompt: Optional[str] = None
    environment: str
    service: str

class DatasetRecord(BaseModel):
    source_id: str
    kind: str
    summary: str
    release: Optional[str] = None
    recorded_status: str
    description: str
    comments: List[str] = Field(default_factory=list)
    links: List[str] = Field(default_factory=list)

class DatasetPayload(BaseModel):
    dataset_label: str
    target: TargetBuildConfig
    records: List[DatasetRecord]
    note: Optional[str] = None

