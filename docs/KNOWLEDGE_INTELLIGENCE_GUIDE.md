# FocusBoard SaaS Knowledge Intelligence & Organizational Graph Guide (Phase 38)

## 1. Overview
Phase 38 delivers FocusBoard Knowledge Intelligence—an organizational brain connecting documentation, Architecture Decision Records (ADRs), runbooks, graph relationships, hybrid semantic search, and an AI Knowledge Assistant with verifiable source citations.

---

## 2. Core Capabilities
- **Document Management & Versioning**: Complete lifecycle for specifications, decision records, runbooks, and postmortems. Modifying document content automatically creates immutable `KnowledgeDocumentVersion` history.
- **Knowledge Collections**: Hierarchical and cross-workspace collections for engineering standards, compliance records, and product strategy.
- **Organizational Knowledge Graph**:
  - **Entities (`KnowledgeEntity`)**: Projects, Tasks, Decisions, Technologies, Goals, and Ideas.
  - **Relationships (`KnowledgeRelationship`)**: `RELATES_TO`, `DEPENDS_ON`, `IMPLEMENTS`, `INFORMED_BY`, `VALIDATES`, `SUPERSEDES`.
- **Hybrid Semantic Search**: Combines keyword matching, title weighting, quality scoring, and contextual text snippet highlights.
- **Grounded AI Knowledge Assistant**:
  - Answers user queries using exclusively verified internal documents.
  - Generates verifiable source citations (`source_id`, `source_title`, `snippet`, `relevance`) to prevent hallucination.
- **Organizational Memory & Gaps**: Captures architectural decisions and lessons learned, while detecting documentation gaps or outdated specifications.

---

## 3. REST API Endpoints (`/api/v1/knowledge`)
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/knowledge/overview` | `GET` | Document counts, quality scores, graph statistics, and gap summaries |
| `/knowledge/documents` | `GET`, `POST` | List and publish knowledge documents with slug generation |
| `/knowledge/documents/{id}` | `GET`, `PATCH`, `DELETE` | Read and update document content (with auto-versioning) |
| `/knowledge/documents/{id}/versions` | `GET` | Retrieve complete version history and diff summaries |
| `/knowledge/collections` | `GET`, `POST` | Manage workspace and cross-workspace collections |
| `/knowledge/graph` | `GET` | Graph Explorer API returning interactive nodes and edges |
| `/knowledge/graph/entities` | `POST` | Register entities into the organizational graph |
| `/knowledge/graph/relationships` | `POST` | Create semantic relations between entities |
| `/knowledge/search` | `POST` | Hybrid semantic search returning relevance scores and snippets |
| `/knowledge/assistant/query` | `POST` | AI assistant with verified citation attributions |
| `/knowledge/memories` | `GET`, `POST` | Organizational memory bank (facts, decisions, lessons) |
| `/knowledge/gaps` | `GET`, `POST`, `PATCH` | Track and resolve missing or outdated documentation |
