from __future__ import annotations

STATUS_EXTRACTING = "extracting"
STATUS_PENDING_REVIEW = "pending_review"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
STATUS_FAILED = "failed"

VALID_STATUSES = {
    STATUS_EXTRACTING,
    STATUS_PENDING_REVIEW,
    STATUS_APPROVED,
    STATUS_REJECTED,
    STATUS_FAILED,
}

NODE_TYPES = [
    "Product",
    "Feature",
    "ProofPoint",
    "Persona",
    "ICPSegment",
    "Person",
    "EmailThread",
    "Decision",
    "SourceDocument",
    "ExtractionRun",
]
