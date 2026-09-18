# PromptGuard-KVKK

Privacy Firewall for Generative AI prompts. **Current phase: Phase 3 - Explainable Risk and Sanitization.** The project detects supported entities in memory, assigns a bounded deterministic risk score, maps it to a policy decision, and returns a span-safe sanitized prompt. External LLM integration, authentication, and Phase 4 workflow features are not implemented.

## Architecture

- `frontend/` - Next.js, TypeScript, App Router, Tailwind CSS
- `backend/` - FastAPI, Pydantic, SQLAlchemy, SQLite
- `docs/` - architecture and privacy design notes

## Supported entity types

- Validated deterministic: `TC_ID`, `PHONE`, `EMAIL`, `IBAN`, `CREDIT_CARD`, `IP_ADDRESS`, `DATE`, `URL`, `PASSPORT_ID`
- Lightweight local semantic provider: `PERSON`, `LOCATION`, `ORGANIZATION`

The pipeline preserves offsets from the original prompt: identifier-specific normalization is used only for validation, then regex and semantic candidates are deduplicated and overlap-resolved. The semantic provider is a conservative local heuristic fallback, so no model is downloaded or loaded at startup.

## Phase 3 risk policy

`backend/app/services/risk/weights.py` is the single source of truth for entity weights, sensitivity categories, combination bonuses, and score boundaries. Scores are the rounded sum of `weight * detector confidence`, plus bounded explainable factors:

| Level | Score | Decision |
| --- | ---: | --- |
| LOW | 0-20 | ALLOW |
| MEDIUM | 21-45 | WARN |
| HIGH | 46-70 | MASK |
| CRITICAL | 71-100 | BLOCK |

Direct identifiers receive an explicit sensitivity factor. Direct-identifier/contact, direct-identifier/financial, financial/contact, three-category diversity, and repeated-entity rules are additive and capped by the final 100-point clamp. This is an engineering heuristic, not a legal determination or a KVKK compliance certification.

| Entity | Weight | Category |
| --- | ---: | --- |
| TC_ID, PASSPORT_ID | 40 | DIRECT_IDENTIFIER |
| CREDIT_CARD | 40 | FINANCIAL_INFORMATION |
| IBAN | 32 | FINANCIAL_INFORMATION |
| PHONE | 18 | CONTACT_INFORMATION |
| EMAIL | 15 | CONTACT_INFORMATION |
| IP_ADDRESS | 12 | NETWORK_IDENTIFIER |
| PERSON | 12 | PERSONAL_INFORMATION |
| LOCATION | 10 | PERSONAL_INFORMATION |
| DATE | 6 | PERSONAL_INFORMATION |
| ORGANIZATION | 5 | OTHER |
| URL | 4 | OTHER |

Detection, risk, and sanitization are separate decisions. The centralized sanitizer applies `MASK` to high-sensitivity identifiers (`TC_ID`, `PASSPORT_ID`, `CREDIT_CARD`, `IBAN`, `PHONE`, `EMAIL`, `IP_ADDRESS`), `PSEUDONYMIZE` to `PERSON`, and `KEEP` to city-level `LOCATION`, `ORGANIZATION`, `DATE`, and `URL`. Exact resolved spans are transformed left-to-right, preserving every non-entity character. Repeated people receive consistent in-memory placeholders such as `[PERSON_1]`; mappings are discarded after the request. Preserving useful context improves downstream generative-AI utility without lowering the risk score. This is an academic prototype policy, not a legal KVKK determination.

## Run locally

1. Copy `backend/.env.example` to `backend/.env` if you need non-default settings. From `backend/`, create and activate a virtual environment, install requirements, then run:

   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

2. Copy `frontend/.env.example` to `frontend/.env.local`. From `frontend/`, run:

   ```powershell
   npm install
   npm run dev
   ```

The frontend is available at `http://localhost:3000`; the backend is available at `http://localhost:8000`.

## Test

From `backend/` with the virtual environment activated:

```powershell
pytest
```

From `frontend/`:

```powershell
npm run lint
npm run build
```

## Privacy baseline

Prompts and entity values are processed transiently: they are neither logged nor persisted. The SQLite schema has no raw-prompt or entity-text field. Exceptions return a generic message without prompt content. The API returns risk explanations and a sanitized view, but does not save either form.

The semantic provider is `heuristic-local`: a small deterministic rule set for Turkish/English capitalization and contextual phrases. It is intentionally conservative. For example, it can identify `Ahmet Yilmaz` and `Istanbul`, but a bare organization such as `Microsoft` may not be identified; the response reports this limitation rather than claiming model-grade NER.
