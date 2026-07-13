Extract Analytos Brain knowledge from the provided source document.

Return only structured entities and relationships matching the Pydantic schema:
Product, Feature, ProofPoint, Persona, ICPSegment, Person, EmailThread, Decision,
SourceDocument, ExtractionRun and the approved relationship types.

Rules:
- Never invent facts not present in the source.
- Preserve provenance using source file and concise source excerpts.
- Mark email-derived material internal by default.
- Mark proof points approved for external use only when the source explicitly says so.
- Use deterministic slugs.
- Do not write to the main graph branch.
