# Ontology Knowledge Framework (OKF) Implementation Plan
**Project:** AIdvocate (Indian Supreme Court Legal Intelligence System)  
**Target Architecture:** Ontology-Guided Hybrid RAG using OpenAI (`gpt-4o-mini`), Qdrant Vector Store, and Structured Legal Taxonomies.

---

## 1. Executive Summary & Objective

The **Ontology Knowledge Framework (OKF)** upgrades the current naive RAG (character chunking + dense vector similarity) into a **Semantically Structured Legal Knowledge System**.

### Primary Bottlenecks in Current Naive RAG:
1. **Discourse Confusion:** The LLM cannot distinguish between lawyer arguments (*Petitioner/Respondent contentions*) and binding court rulings (*Ratio Decidendi*).
2. **Statutory Drift:** Pure vector search frequently misses exact statutory anchors (*Act, Article, Section, Schedule, Form*).
3. **Token & Latency Inefficiency:** Passing 4–5 bulky 1,000-character raw chunks wastes thousands of prompt tokens and increases OpenAI API costs by over 50%.

### OKF Target Metrics:
- **Retrieval Precision@K:** Increase from ~60% to >90% by using ontology payload filters.
- **Prompt Token Reduction:** Cut context token volume by **~50%–60%** via role-filtered, structured extraction.
- **Hallucination Elimination:** Restrict answers regarding rulings to chunks explicitly tagged `discourse_role: COURT_HOLDING`.

---

## 2. Legal Ontology Domain Schema

```
                   ┌──────────────────────────────────────┐
                   │            CaseDocument              │
                   │  - citation_id / title / date / year │
                   └──────────────────┬───────────────────┘
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            ▼                         ▼                         ▼
   ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
   │      Bench      │       │     Parties     │       │     Outcome     │
   │  - Judges       │       │  - Petitioner   │       │  - Allowed      │
   │  - Court        │       │  - Respondent   │       │  - Dismissed    │
   └─────────────────┘       └─────────────────┘       └─────────────────┘
            │                         │                         │
            └─────────────────────────┼─────────────────────────┘
                                      │
                   ┌──────────────────┴───────────────────┐
                   ▼                                      ▼
        ┌─────────────────────┐                ┌─────────────────────┐
        │  Statute / Section  │                │  Discourse Chunks   │
        │  - Act Name         │                │  - COURT_HOLDING    │
        │  - Section / Rule   │◄───tagged_to───│  - PETITIONER_ARG   │
        │  - Form (e.g. F-6)  │                │  - RESPONDENT_ARG   │
        └─────────────────────┘                │  - STATUTORY_TEXT   │
                   ▲                           └─────────────────────┘
                   │                                      │
                   └──────────────cites_precedent─────────┘
```

### Ontological Entities & Attributes:
1. **`LegalDocument`**: File name, case citation, judgment date, court level.
2. **`StatutoryAnchor`**: Act name (e.g. *Representation of the People Act, 1950*), Section / Rule (e.g. *Rule 26, Form 6*), Article.
3. **`DiscourseRole`**:
   - `COURT_HOLDING` / `RATIO_DECIDENDI` (binding ruling)
   - `PETITIONER_ARGUMENT`
   - `RESPONDENT_ARGUMENT`
   - `STATUTORY_ANALYSIS`
   - `OBITER_DICTA`
4. **`PrecedentCitation`**: Previous judgments referenced and whether followed/distinguished.

---

## 3. Architecture & File Structure

Inside the `OpenAI/` directory:

```
OpenAI/
├── .env                     # API keys and model configurations
├── ontology_schema.py       # Pydantic models defining Legal Ontology & Discourse Roles
├── ontology_extractor.py    # OpenAI Structured Extraction for chunk enrichment
├── index_okf.py             # Ingestion pipeline: chunks -> ontology tags -> Qdrant
├── query_parser.py          # Transforms user query into (Vector + Ontological Filter)
├── app.py                   # FastAPI server serving Ontology-Guided RAG
└── test_okf.py              # Benchmarking test suite comparing Naive vs OKF RAG
```

---

## 4. Step-by-Step Implementation Roadmap

### Phase 1: Define the Ontology Schema (`OpenAI/ontology_schema.py`)
- Define strongly-typed Pydantic schemas:
  - `DiscourseRoleEnum`: `COURT_HOLDING`, `PETITIONER_ARGUMENT`, `RESPONDENT_ARGUMENT`, `STATUTORY_TEXT`, `GENERAL`.
  - `LegalEntity`: `statutes` (List of Acts), `sections` (List of sections/forms/articles), `parties`, `bench`.
  - `OntologyChunkPayload`: Text snippet, page label, document name, `discourse_role`, `statutes`, `sections`, `core_concept`.

### Phase 2: Metadata & Discourse Extraction (`OpenAI/ontology_extractor.py`)
- Implement lightweight batch extraction using OpenAI `gpt-4o-mini` with structured JSON output.
- During document indexing:
  - Process text chunks.
  - Extract relevant Acts, Sections, and classify the chunk's `DiscourseRole`.
  - Attach this structured metadata into each Qdrant chunk payload.

### Phase 3: Qdrant Collection Optimization & Payload Indexing
- Create payload indexes in Qdrant for fast faceted filtering:
  - `payload_index("statutes", keyword)`
  - `payload_index("sections", keyword)`
  - `payload_index("discourse_role", keyword)`
- This enables sub-millisecond pre-filtering prior to dense vector search.

### Phase 4: Ontology-Aware Query Parser (`OpenAI/query_parser.py`)
- When a user asks a question (e.g., *"Can the Election Commissioner change Form 6 without Supreme Court permission?"*):
  - Parse the query to identify:
    - Target Legal Concept: `Form 6`, `Conduct of Election Rules`
    - Target Discourse Filter: Prioritize `COURT_HOLDING` if asking for rulings.
  - Formulate Qdrant search with:
    - **Filter**: Matches tagged Acts/Sections/Roles if detected.
    - **Dense Vector**: Embedding of the natural language question.

### Phase 5: Augmented Generation & Exact Citation Synthesis (`OpenAI/app.py`)
- Update `app.py` `/chat` endpoint:
  - Retrieve ontology-guided chunks.
  - Present the LLM with focused, pre-classified context:
    ```markdown
    [HOLDING - Page 14 - Rule 26/Form 6]
    "The Chief Election Commissioner cannot unilaterally..."
    ```
  - Generate response with court-grade citations (Act, Section, Page Number, and whether it represents the holding).

### Phase 6: Verification & Benchmarking
- Build `test_okf.py` to compare:
  1. **Naive RAG**: Average tokens used, hallucination check on argument vs. ruling.
  2. **OKF RAG**: Precision score, token count, execution latency.

---

## 5. Timeline & Execution Phases

| Phase | Task | Estimated Scope |
| :--- | :--- | :--- |
| **Phase 1** | Schema creation (`ontology_schema.py`) | ~1-2 hours |
| **Phase 2** | Entity & discourse extractor (`ontology_extractor.py`) | ~2-3 hours |
| **Phase 3** | Indexing pipeline with Qdrant payloads (`index_okf.py`) | ~2 hours |
| **Phase 4** | Query parser with hybrid Qdrant filters (`query_parser.py`) | ~2 hours |
| **Phase 5** | FastAPI integration & verification (`app.py`) | ~1-2 hours |

---

## 6. Immediate Next Action
To proceed with implementation, start by creating **`OpenAI/ontology_schema.py`** to formally establish the Pydantic data models for the legal framework.
