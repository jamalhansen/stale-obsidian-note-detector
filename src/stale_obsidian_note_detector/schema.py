from enum import Enum
from typing import List
from pydantic import BaseModel

class StaleAction(str, Enum):
    KEEP = "keep"
    ARCHIVE = "archive"
    DEEP_ARCHIVE = "deep_archive"

class StaleCandidate(BaseModel):
    file_path: str
    reason: str
    suggested_action: StaleAction
    confidence: float

class StaleReport(BaseModel):
    candidates: List[StaleCandidate]
