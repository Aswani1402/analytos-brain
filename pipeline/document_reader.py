from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .id_generator import sha256_text, source_document_slug


@dataclass(frozen=True)
class SourceDocumentInput:
    path: Path
    file_name: str
    title: str
    content: str
    content_hash: str
    document_type: str
    slug: str


def infer_document_type(path: Path, content: str) -> str:
    name = path.name.lower()
    if name.startswith("email-"):
        return "email_thread"
    if "icp" in name:
        return "icp"
    if "product-overview" in name:
        return "product_overview"
    return "source_document"


def read_document(path: str | Path) -> SourceDocumentInput:
    source_path = Path(path)
    content = source_path.read_text(encoding="utf-8")
    first_heading = next((line[2:].strip() for line in content.splitlines() if line.startswith("# ")), source_path.stem)
    content_hash = sha256_text(content)
    return SourceDocumentInput(
        path=source_path,
        file_name=source_path.name,
        title=first_heading,
        content=content,
        content_hash=content_hash,
        document_type=infer_document_type(source_path, content),
        slug=source_document_slug(source_path, content_hash),
    )
