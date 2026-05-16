# Datavant Prep: Secure Ingestion Vessel

## Architecture
This project uses **Pydantic V2** with **Annotated Types** to enforce 
data integrity at the edge.

## Privacy Standards
- **Deterministic Hashing:** Uses SHA-256 with a SHARED_SALT to ensure 
  linkability across disparate datasets without PII exposure.
- **Sanitization:** All identifiers are stripped and normalized 
  via `BeforeValidator` chains.

## Quality Control
- **Linting:** Enforced via `Ruff`.
- **Testing:** Unit tests via `Pytest`.