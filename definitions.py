import os
from pathlib import Path
from enum import Enum

# Root project paths
ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
DATASET_PATH = DATA_DIR / "dataset.json"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

# Default Assessment Scope & Target Build (from manifest)
DEFAULT_DATASET_LABEL = "tyn-release-assessment-v2"
DEFAULT_TARGET_RELEASE = "R2.4"
DEFAULT_TARGET_COMMIT = "b7a91f2"
DEFAULT_TARGET_PROMPT = "p7"
DEFAULT_TARGET_ENV = "production"
DEFAULT_TARGET_SERVICE = "atlas-assistant"

class RequirementDecision(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"

class ReleaseDecision(str, Enum):
    READY = "READY"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    BLOCKED = "BLOCKED"

class AssessmentStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class IssueKind(str, Enum):
    MANIFEST = "manifest"
    REQUIREMENT = "requirement"
    EVIDENCE = "evidence"
    WORK = "work"
