from __future__ import annotations

import hashlib
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "unknown"


def source_document_slug(path: Path, content_hash: str) -> str:
    return f"source-document:{slugify(path.name)}:{content_hash[:12]}"


def ingestion_branch(path: Path, content_hash: str, now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d%H%M%S%f")
    document_slug = slugify(path.stem)[:12].strip("-") or "document"
    return f"ing-{timestamp}-{document_slug}-{content_hash[:8]}-{uuid.uuid4().hex[:12]}"


def extraction_run_slug(branch_name: str) -> str:
    return f"extraction-run:{slugify(branch_name)}"
