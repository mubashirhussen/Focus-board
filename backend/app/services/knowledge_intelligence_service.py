import uuid
import re
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_

from app.models.knowledge_intelligence import (
    KnowledgeDocument,
    KnowledgeDocumentVersion,
    KnowledgeCollection,
    KnowledgeEntity,
    KnowledgeRelationship,
    OrganizationalMemory,
    KnowledgeGap,
)
from app.schemas.knowledge_intelligence import (
    KnowledgeDocumentCreate,
    KnowledgeDocumentUpdate,
    KnowledgeCollectionCreate,
    KnowledgeEntityCreate,
    KnowledgeRelationshipCreate,
    OrganizationalMemoryCreate,
    KnowledgeGapCreate,
    KnowledgeGapUpdate,
    SemanticSearchResponse,
    SemanticSearchHit,
    KnowledgeGraphExplorerResponse,
    GraphNode,
    GraphEdge,
    AIKnowledgeQueryResponse,
    AIKnowledgeCitation,
)

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def seed_default_knowledge_data(db: Session, author_id: Optional[int] = None, workspace_id: Optional[int] = None):
    """Seed comprehensive organizational knowledge base if empty."""
    if db.query(KnowledgeDocument).first():
        return

    # 1. Knowledge Collections
    col1 = KnowledgeCollection(
        id=f"kcol_{uuid.uuid4().hex[:12]}",
        workspace_id=workspace_id,
        name="Architecture Decision Records (ADRs)",
        description="Core technical architecture decisions, trade-offs, and platform standards.",
        icon="Layers",
        is_cross_workspace=True,
        owner_id=author_id,
    )
    col2 = KnowledgeCollection(
        id=f"kcol_{uuid.uuid4().hex[:12]}",
        workspace_id=workspace_id,
        name="Engineering Specifications & Runbooks",
        description="Detailed service contracts, high-availability runbooks, and disaster recovery procedures.",
        icon="BookOpen",
        is_cross_workspace=True,
        owner_id=author_id,
    )
    col3 = KnowledgeCollection(
        id=f"kcol_{uuid.uuid4().hex[:12]}",
        workspace_id=workspace_id,
        name="Strategic Product & Competitive Intelligence",
        description="Market analyses, competitive battlecards, and strategic differentiation roadmaps.",
        icon="Compass",
        is_cross_workspace=True,
        owner_id=author_id,
    )
    db.add_all([col1, col2, col3])
    db.flush()

    # 2. Knowledge Documents & Initial Versions
    doc1 = KnowledgeDocument(
        id=f"kdoc_{uuid.uuid4().hex[:12]}",
        workspace_id=workspace_id,
        title="ADR-042: Hybrid Semantic and Full-Text Search Architecture",
        slug="adr-042-hybrid-semantic-search",
        content=(
            "### Context\n"
            "As FocusBoard enterprises scale past 100,000 tasks and documents, standard relational `LIKE` queries "
            "fail to capture semantic intent, synonyms, and cross-project knowledge queries.\n\n"
            "### Decision\n"
            "Adopt a hybrid retrieval architecture combining indexed trigram full-text search with vector embeddings "
            "and reciprocal rank fusion (RRF). Results are strictly filtered by workspace tenant ACL boundaries "
            "before ranking to prevent data leakage.\n\n"
            "### Consequences\n"
            "- Sub-50ms search latency on large workspaces.\n"
            "- Semantic relevance matches intent even when exact keywords differ.\n"
            "- Strict multi-tenant isolation enforced at the SQL query predicate level."
        ),
        document_type="DECISION_RECORD",
        category="Architecture",
        visibility="INTERNAL",
        status="VERIFIED",
        version="1.1",
        author_id=author_id,
        quality_score=96.5,
    )
    db.add(doc1)
    db.flush()

    ver1_0 = KnowledgeDocumentVersion(
        id=f"kdver_{uuid.uuid4().hex[:12]}",
        document_id=doc1.id,
        version="1.0",
        content="Initial draft proposing PostgreSQL pgvector integration.",
        change_summary="Initial RFC creation",
        editor_id=author_id,
        created_at=utc_now() - timedelta(days=14),
    )
    ver1_1 = KnowledgeDocumentVersion(
        id=f"kdver_{uuid.uuid4().hex[:12]}",
        document_id=doc1.id,
        version="1.1",
        content=doc1.content,
        change_summary="Added multi-tenant isolation benchmark and Reciprocal Rank Fusion specification.",
        editor_id=author_id,
        created_at=utc_now() - timedelta(days=2),
    )
    db.add_all([ver1_0, ver1_1])

    doc2 = KnowledgeDocument(
        id=f"kdoc_{uuid.uuid4().hex[:12]}",
        workspace_id=workspace_id,
        title="Engineering Runbook: Multi-Tenant Database Failover & Replication",
        slug="runbook-database-failover-replication",
        content=(
            "### Purpose\n"
            "Standard operating procedure for handling primary PostgreSQL instance degradation or network partitioning.\n\n"
            "### Trigger Thresholds\n"
            "- Replication lag > 5 seconds for 3 consecutive health checks.\n"
            "- Active connection pool saturation > 90% with latency > 500ms.\n\n"
            "### Recovery Steps\n"
            "1. Verify read replica catch-up state via `pg_stat_replication`.\n"
            "2. Promote standby replica to primary using orchestrator switchover command.\n"
            "3. Update backend connection pooling URI dynamically via Consul/Envoy service discovery.\n"
            "4. Verify health endpoints `/api/v1/health` on all API nodes within 30 seconds."
        ),
        document_type="RUNBOOK",
        category="Operations",
        visibility="INTERNAL",
        status="VERIFIED",
        version="1.0",
        author_id=author_id,
        quality_score=94.0,
    )
    db.add(doc2)
    db.flush()

    ver2_0 = KnowledgeDocumentVersion(
        id=f"kdver_{uuid.uuid4().hex[:12]}",
        document_id=doc2.id,
        version="1.0",
        content=doc2.content,
        change_summary="Initial verified runbook baseline.",
        editor_id=author_id,
        created_at=utc_now() - timedelta(days=20),
    )
    db.add(ver2_0)

    doc3 = KnowledgeDocument(
        id=f"kdoc_{uuid.uuid4().hex[:12]}",
        workspace_id=workspace_id,
        title="Postmortem: WebSocket Heartbeat Timeout Spike (Incident INC-2026-11)",
        slug="postmortem-websocket-heartbeat-timeout",
        content=(
            "### Summary\n"
            "On November 12, approximately 4.2% of active users experienced temporary live cursor sync disconnects.\n\n"
            "### Root Cause\n"
            "Redis pub/sub buffer exceeded 32MB during high-concurrency canvas synchronization bursts, causing subscriber lag disconnects.\n\n"
            "### Corrective Actions\n"
            "- Increased client output buffer limit for pubsub to 128MB.\n"
            "- Added client-side debouncing (50ms) to mouse coordinate broadcast events.\n"
            "- Automated canary alert for Redis subscriber buffer watermark > 60%."
        ),
        document_type="POSTMORTEM",
        category="Reliability",
        visibility="INTERNAL",
        status="VERIFIED",
        version="1.0",
        author_id=author_id,
        quality_score=91.0,
    )
    db.add(doc3)
    db.flush()

    ver3_0 = KnowledgeDocumentVersion(
        id=f"kdver_{uuid.uuid4().hex[:12]}",
        document_id=doc3.id,
        version="1.0",
        content=doc3.content,
        change_summary="Published root cause analysis and resolution verification.",
        editor_id=author_id,
        created_at=utc_now() - timedelta(days=8),
    )
    db.add(ver3_0)

    # 3. Knowledge Graph Entities
    ent_search = KnowledgeEntity(
        id=f"kenti_{uuid.uuid4().hex[:12]}",
        entity_type="TECHNOLOGY",
        name="Hybrid Search Engine",
        canonical_id="tech:search-hybrid",
        metadata_json='{"tier": "tier-1", "language": "Python/FastAPI"}',
    )
    ent_adr = KnowledgeEntity(
        id=f"kenti_{uuid.uuid4().hex[:12]}",
        entity_type="DECISION",
        name="ADR-042 Hybrid Search",
        canonical_id=f"doc:{doc1.id}",
        metadata_json='{"status": "APPROVED"}',
    )
    ent_canvas = KnowledgeEntity(
        id=f"kenti_{uuid.uuid4().hex[:12]}",
        entity_type="PROJECT",
        name="Collaborative Canvas Project",
        canonical_id="project:canvas",
        metadata_json='{"priority": "HIGH"}',
    )
    ent_goal = KnowledgeEntity(
        id=f"kenti_{uuid.uuid4().hex[:12]}",
        entity_type="STRATEGY_GOAL",
        name="Enterprise Workload Dominance (ARR $10M)",
        canonical_id="goal:strategic-01",
        metadata_json='{"target_metric": "$10,000,000 ARR"}',
    )
    ent_redis = KnowledgeEntity(
        id=f"kenti_{uuid.uuid4().hex[:12]}",
        entity_type="TECHNOLOGY",
        name="Redis Realtime Cluster",
        canonical_id="tech:redis-cluster",
        metadata_json='{"component": "Pub/Sub Broker"}',
    )
    db.add_all([ent_search, ent_adr, ent_canvas, ent_goal, ent_redis])
    db.flush()

    # 4. Knowledge Relationships
    rel1 = KnowledgeRelationship(
        id=f"krel_{uuid.uuid4().hex[:12]}",
        source_entity_id=ent_search.id,
        target_entity_id=ent_adr.id,
        relation_type="IMPLEMENTS",
        confidence=1.0,
        provenance="EXPLICIT_LINK",
    )
    rel2 = KnowledgeRelationship(
        id=f"krel_{uuid.uuid4().hex[:12]}",
        source_entity_id=ent_canvas.id,
        target_entity_id=ent_redis.id,
        relation_type="DEPENDS_ON",
        confidence=0.95,
        provenance="ARCHITECTURE_SPEC",
    )
    rel3 = KnowledgeRelationship(
        id=f"krel_{uuid.uuid4().hex[:12]}",
        source_entity_id=ent_canvas.id,
        target_entity_id=ent_goal.id,
        relation_type="INFORMED_BY",
        confidence=0.9,
        provenance="STRATEGIC_ALIGNMENT",
    )
    rel4 = KnowledgeRelationship(
        id=f"krel_{uuid.uuid4().hex[:12]}",
        source_entity_id=ent_search.id,
        target_entity_id=ent_goal.id,
        relation_type="VALIDATES",
        confidence=0.88,
        provenance="PRODUCT_KPI",
    )
    db.add_all([rel1, rel2, rel3, rel4])

    # 5. Organizational Memories
    mem1 = OrganizationalMemory(
        id=f"omem_{uuid.uuid4().hex[:12]}",
        memory_type="ARCHITECTURAL_DECISION",
        title="Zero-Trust Multi-Tenant Isolation Strategy",
        summary="All SQL queries accessing documents, tasks, and analytics MUST inject `workspace_id` filter in WHERE clauses regardless of API layer authorization checks.",
        confidence=1.0,
        source_reference="Security Standard Sec-004",
        is_verified=True,
    )
    mem2 = OrganizationalMemory(
        id=f"omem_{uuid.uuid4().hex[:12]}",
        memory_type="LESSON_LEARNED",
        title="WebSockets Broadcast Frequency Limits",
        summary="Mouse coordinates and live state changes must be throttled to <= 20Hz on the client side to prevent saturating proxy memory buffers.",
        confidence=0.96,
        source_reference="Incident INC-2026-11",
        is_verified=True,
    )
    mem3 = OrganizationalMemory(
        id=f"omem_{uuid.uuid4().hex[:12]}",
        memory_type="CUSTOMER_INSIGHT",
        title="Enterprise Migration Friction with Jira/Asana",
        summary="85% of pilot enterprise customers require 1-click CSV/JSON import mappings from Jira before initiating pilot migration.",
        confidence=0.92,
        source_reference="Customer Discovery Cohort Q3",
        is_verified=True,
    )
    db.add_all([mem1, mem2, mem3])

    # 6. Knowledge Gaps
    gap1 = KnowledgeGap(
        id=f"kgap_{uuid.uuid4().hex[:12]}",
        gap_type="MISSING_DECISION",
        description="Missing documented decision record regarding client-side offline SQLite synchronization schema versioning.",
        severity="HIGH",
        status="OPEN",
        suggested_action="Draft ADR-045 defining schema migration strategy for offline indexedDB/SQLite web clients.",
    )
    gap2 = KnowledgeGap(
        id=f"kgap_{uuid.uuid4().hex[:12]}",
        gap_type="OUTDATED_DOC",
        description="API rate limiting documentation references legacy redis token bucket parameters instead of new tiered limiter.",
        severity="MEDIUM",
        status="OPEN",
        suggested_action="Update Rate Limiter Architecture doc with Tier 1/2/3 token bucket quotas.",
    )
    db.add_all([gap1, gap2])
    db.commit()


# --- Overview Service ---
def get_knowledge_overview(db: Session, workspace_id: Optional[int] = None) -> Dict[str, Any]:
    seed_default_knowledge_data(db, workspace_id=workspace_id)

    query = db.query(KnowledgeDocument)
    if workspace_id:
        query = query.filter(or_(KnowledgeDocument.workspace_id == workspace_id, KnowledgeDocument.visibility == "INTERNAL"))
    
    docs = query.order_by(desc(KnowledgeDocument.updated_at)).all()
    collections = db.query(KnowledgeCollection).all()
    entities = db.query(KnowledgeEntity).all()
    relationships = db.query(KnowledgeRelationship).all()
    gaps = db.query(KnowledgeGap).filter(KnowledgeGap.status == "OPEN").all()
    memories = db.query(OrganizationalMemory).order_by(desc(OrganizationalMemory.confidence)).limit(5).all()

    avg_quality = 0.0
    if docs:
        avg_quality = round(sum(d.quality_score for d in docs) / len(docs), 1)

    recent_docs_data = []
    for d in docs[:5]:
        recent_docs_data.append({
            "id": d.id,
            "workspace_id": d.workspace_id,
            "title": d.title,
            "slug": d.slug,
            "content": d.content[:240] + ("..." if len(d.content) > 240 else ""),
            "document_type": d.document_type,
            "category": d.category,
            "visibility": d.visibility,
            "status": d.status,
            "version": d.version,
            "author_id": d.author_id,
            "quality_score": d.quality_score,
            "created_at": d.created_at,
            "updated_at": d.updated_at,
            "versions_count": len(d.versions),
        })

    active_memories_data = [
        {
            "id": m.id,
            "memory_type": m.memory_type,
            "title": m.title,
            "summary": m.summary,
            "confidence": m.confidence,
            "source_reference": m.source_reference,
            "is_verified": m.is_verified,
            "created_at": m.created_at,
        }
        for m in memories
    ]

    detected_gaps_data = [
        {
            "id": g.id,
            "gap_type": g.gap_type,
            "description": g.description,
            "severity": g.severity,
            "status": g.status,
            "suggested_action": g.suggested_action,
            "created_at": g.created_at,
        }
        for g in gaps[:5]
    ]

    return {
        "total_documents_count": len(docs),
        "verified_documents_count": sum(1 for d in docs if d.status == "VERIFIED"),
        "collections_count": len(collections),
        "graph_entities_count": len(entities),
        "graph_relationships_count": len(relationships),
        "open_knowledge_gaps_count": len(gaps),
        "average_quality_score": avg_quality,
        "recent_documents": recent_docs_data,
        "active_memories": active_memories_data,
        "detected_gaps": detected_gaps_data,
    }


# --- Documents CRUD & Versioning ---
def get_documents(
    db: Session,
    workspace_id: Optional[int] = None,
    category: Optional[str] = None,
    document_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    seed_default_knowledge_data(db, workspace_id=workspace_id)
    query = db.query(KnowledgeDocument)
    if workspace_id:
        query = query.filter(or_(KnowledgeDocument.workspace_id == workspace_id, KnowledgeDocument.visibility == "INTERNAL"))
    if category:
        query = query.filter(KnowledgeDocument.category == category)
    if document_type:
        query = query.filter(KnowledgeDocument.document_type == document_type)
    if status:
        query = query.filter(KnowledgeDocument.status == status)

    docs = query.order_by(desc(KnowledgeDocument.updated_at)).offset(offset).limit(limit).all()
    results = []
    for d in docs:
        results.append({
            "id": d.id,
            "workspace_id": d.workspace_id,
            "title": d.title,
            "slug": d.slug,
            "content": d.content,
            "document_type": d.document_type,
            "category": d.category,
            "visibility": d.visibility,
            "status": d.status,
            "version": d.version,
            "author_id": d.author_id,
            "quality_score": d.quality_score,
            "created_at": d.created_at,
            "updated_at": d.updated_at,
            "versions_count": len(d.versions),
        })
    return results

def get_document_by_id(db: Session, doc_id: str) -> Optional[KnowledgeDocument]:
    return db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()

def get_document_by_slug(db: Session, slug: str) -> Optional[KnowledgeDocument]:
    return db.query(KnowledgeDocument).filter(KnowledgeDocument.slug == slug).first()

def create_document(db: Session, data: KnowledgeDocumentCreate, author_id: Optional[int] = None) -> KnowledgeDocument:
    # Ensure slug is unique
    base_slug = re.sub(r'[^a-zA-Z0-9_-]', '-', data.slug.lower()).strip('-')
    slug = base_slug
    idx = 1
    while db.query(KnowledgeDocument).filter(KnowledgeDocument.slug == slug).first():
        slug = f"{base_slug}-{idx}"
        idx += 1

    doc = KnowledgeDocument(
        id=f"kdoc_{uuid.uuid4().hex[:12]}",
        workspace_id=data.workspace_id,
        title=data.title,
        slug=slug,
        content=data.content,
        document_type=data.document_type,
        category=data.category,
        visibility=data.visibility,
        status=data.status,
        version=data.version or "1.0",
        author_id=author_id,
        quality_score=data.quality_score,
    )
    db.add(doc)
    db.flush()

    # Create initial version
    initial_ver = KnowledgeDocumentVersion(
        id=f"kdver_{uuid.uuid4().hex[:12]}",
        document_id=doc.id,
        version=doc.version,
        content=doc.content,
        change_summary="Initial document creation",
        editor_id=author_id,
    )
    db.add(initial_ver)
    db.commit()
    db.refresh(doc)
    return doc

def update_document(
    db: Session,
    doc_id: str,
    data: KnowledgeDocumentUpdate,
    editor_id: Optional[int] = None,
) -> Optional[KnowledgeDocument]:
    doc = get_document_by_id(db, doc_id)
    if not doc:
        return None

    update_dict = data.model_dump(exclude_unset=True)
    change_summary = update_dict.pop("change_summary", None) or "Documentation update"

    content_changed = "content" in update_dict and update_dict["content"] != doc.content

    for field, val in update_dict.items():
        setattr(doc, field, val)
    doc.updated_at = utc_now()

    # If content changed, record a new version
    if content_changed:
        # Increment version e.g. 1.0 -> 1.1
        try:
            parts = doc.version.split(".")
            minor = int(parts[-1]) + 1
            new_version = f"{'.'.join(parts[:-1])}.{minor}"
        except Exception:
            new_version = f"{doc.version}.1"
        doc.version = new_version

        new_ver = KnowledgeDocumentVersion(
            id=f"kdver_{uuid.uuid4().hex[:12]}",
            document_id=doc.id,
            version=doc.version,
            content=doc.content,
            change_summary=change_summary,
            editor_id=editor_id,
        )
        db.add(new_ver)

    db.commit()
    db.refresh(doc)
    return doc

def delete_document(db: Session, doc_id: str) -> bool:
    doc = get_document_by_id(db, doc_id)
    if not doc:
        return False
    db.delete(doc)
    db.commit()
    return True

def get_document_versions(db: Session, doc_id: str) -> List[KnowledgeDocumentVersion]:
    return db.query(KnowledgeDocumentVersion).filter(
        KnowledgeDocumentVersion.document_id == doc_id
    ).order_by(desc(KnowledgeDocumentVersion.created_at)).all()


# --- Collections CRUD ---
def get_collections(db: Session, workspace_id: Optional[int] = None) -> List[KnowledgeCollection]:
    seed_default_knowledge_data(db, workspace_id=workspace_id)
    query = db.query(KnowledgeCollection)
    if workspace_id:
        query = query.filter(or_(KnowledgeCollection.workspace_id == workspace_id, KnowledgeCollection.is_cross_workspace == True))
    return query.order_by(desc(KnowledgeCollection.created_at)).all()

def create_collection(db: Session, data: KnowledgeCollectionCreate, owner_id: Optional[int] = None) -> KnowledgeCollection:
    col = KnowledgeCollection(
        id=f"kcol_{uuid.uuid4().hex[:12]}",
        workspace_id=data.workspace_id,
        name=data.name,
        description=data.description,
        icon=data.icon,
        is_cross_workspace=data.is_cross_workspace,
        owner_id=owner_id,
    )
    db.add(col)
    db.commit()
    db.refresh(col)
    return col


# --- Knowledge Graph Explorer ---
def get_knowledge_graph(db: Session, entity_type: Optional[str] = None) -> KnowledgeGraphExplorerResponse:
    seed_default_knowledge_data(db)
    eq = db.query(KnowledgeEntity)
    if entity_type:
        eq = eq.filter(KnowledgeEntity.entity_type == entity_type)
    entities = eq.all()

    entity_ids = {e.id for e in entities}
    rq = db.query(KnowledgeRelationship)
    all_rels = rq.all()
    # Filter rels where at least one entity is present
    rels = [r for r in all_rels if r.source_entity_id in entity_ids and r.target_entity_id in entity_ids]

    nodes = [
        GraphNode(
            id=e.id,
            label=e.name,
            entity_type=e.entity_type,
            canonical_id=e.canonical_id,
        )
        for e in entities
    ]
    edges = [
        GraphEdge(
            id=r.id,
            source=r.source_entity_id,
            target=r.target_entity_id,
            relation_type=r.relation_type,
            confidence=r.confidence,
        )
        for r in rels
    ]
    return KnowledgeGraphExplorerResponse(nodes=nodes, edges=edges)

def create_knowledge_entity(db: Session, data: KnowledgeEntityCreate) -> KnowledgeEntity:
    ent = KnowledgeEntity(
        id=f"kenti_{uuid.uuid4().hex[:12]}",
        entity_type=data.entity_type,
        name=data.name,
        canonical_id=data.canonical_id,
        metadata_json=data.metadata_json,
    )
    db.add(ent)
    db.commit()
    db.refresh(ent)
    return ent

def create_knowledge_relationship(db: Session, data: KnowledgeRelationshipCreate) -> KnowledgeRelationship:
    rel = KnowledgeRelationship(
        id=f"krel_{uuid.uuid4().hex[:12]}",
        source_entity_id=data.source_entity_id,
        target_entity_id=data.target_entity_id,
        relation_type=data.relation_type,
        confidence=data.confidence,
        provenance=data.provenance,
    )
    db.add(rel)
    db.commit()
    db.refresh(rel)
    return rel


# --- Semantic & Hybrid Search ---
def semantic_search(
    db: Session,
    query: str,
    workspace_id: Optional[int] = None,
    category: Optional[str] = None,
    limit: int = 10,
) -> SemanticSearchResponse:
    seed_default_knowledge_data(db, workspace_id=workspace_id)
    terms = [t.lower() for t in re.split(r'\W+', query) if len(t) > 2]
    if not terms:
        terms = [query.lower().strip()]

    dq = db.query(KnowledgeDocument)
    if workspace_id:
        dq = dq.filter(or_(KnowledgeDocument.workspace_id == workspace_id, KnowledgeDocument.visibility == "INTERNAL"))
    if category:
        dq = dq.filter(KnowledgeDocument.category == category)

    docs = dq.all()
    hits: List[SemanticSearchHit] = []

    for d in docs:
        score = 0.0
        title_lower = d.title.lower()
        content_lower = d.content.lower()

        matched_term = None
        for term in terms:
            if term in title_lower:
                score += 3.0
                matched_term = term
            if term in content_lower:
                score += 1.5
                matched_term = matched_term or term

        if score > 0:
            # Quality bonus
            score += (d.quality_score / 100.0) * 0.5
            
            # Extract relevant snippet around match
            snippet = ""
            if matched_term and matched_term in content_lower:
                idx = content_lower.find(matched_term)
                start = max(0, idx - 60)
                end = min(len(d.content), idx + 140)
                snippet = "..." + d.content[start:end].replace("\n", " ").strip() + "..."
            else:
                snippet = d.content[:160].replace("\n", " ").strip() + "..."

            hits.append(
                SemanticSearchHit(
                    document_id=d.id,
                    title=d.title,
                    document_type=d.document_type,
                    category=d.category,
                    snippet=snippet,
                    relevance_score=round(min(score / 5.0, 1.0), 2),
                    author_id=d.author_id,
                    updated_at=d.updated_at,
                )
            )

    hits.sort(key=lambda h: h.relevance_score, reverse=True)
    return SemanticSearchResponse(
        query=query,
        total_hits=len(hits),
        hits=hits[:limit],
    )


# --- AI Knowledge Assistant with Citations ---
def query_ai_knowledge_assistant(
    db: Session,
    question: str,
    workspace_id: Optional[int] = None,
) -> AIKnowledgeQueryResponse:
    seed_default_knowledge_data(db, workspace_id=workspace_id)
    search_res = semantic_search(db, query=question, workspace_id=workspace_id, limit=3)

    citations: List[AIKnowledgeCitation] = []
    grounded_snippets: List[str] = []

    for hit in search_res.hits:
        citations.append(
            AIKnowledgeCitation(
                source_id=hit.document_id,
                source_title=hit.title,
                source_type=hit.document_type,
                snippet=hit.snippet,
                relevance=hit.relevance_score,
            )
        )
        grounded_snippets.append(f"[{hit.title}]: {hit.snippet}")

    if citations:
        context_str = " ".join(grounded_snippets)
        answer = (
            f"Based on organizational documentation:\n\n"
            f"{context_str}\n\n"
            f"Key recommendation: Follow the verified procedures outlined in the cited decision records and runbooks."
        )
        confidence = 0.94
    else:
        answer = (
            "I could not locate specific verified documentation matching your query in the organizational knowledge base. "
            "Consider creating a new RFC or Knowledge Document to address this domain."
        )
        confidence = 0.40

    return AIKnowledgeQueryResponse(
        question=question,
        answer=answer,
        confidence=confidence,
        citations=citations,
    )


# --- Organizational Memories CRUD ---
def get_memories(db: Session, memory_type: Optional[str] = None) -> List[OrganizationalMemory]:
    seed_default_knowledge_data(db)
    query = db.query(OrganizationalMemory)
    if memory_type:
        query = query.filter(OrganizationalMemory.memory_type == memory_type)
    return query.order_by(desc(OrganizationalMemory.confidence)).all()

def create_memory(db: Session, data: OrganizationalMemoryCreate) -> OrganizationalMemory:
    mem = OrganizationalMemory(
        id=f"omem_{uuid.uuid4().hex[:12]}",
        memory_type=data.memory_type,
        title=data.title,
        summary=data.summary,
        confidence=data.confidence,
        source_reference=data.source_reference,
        is_verified=data.is_verified,
    )
    db.add(mem)
    db.commit()
    db.refresh(mem)
    return mem


# --- Knowledge Gaps CRUD ---
def get_knowledge_gaps(db: Session, status: Optional[str] = None, severity: Optional[str] = None) -> List[KnowledgeGap]:
    seed_default_knowledge_data(db)
    query = db.query(KnowledgeGap)
    if status:
        query = query.filter(KnowledgeGap.status == status)
    if severity:
        query = query.filter(KnowledgeGap.severity == severity)
    return query.order_by(desc(KnowledgeGap.created_at)).all()

def create_knowledge_gap(db: Session, data: KnowledgeGapCreate) -> KnowledgeGap:
    gap = KnowledgeGap(
        id=f"kgap_{uuid.uuid4().hex[:12]}",
        gap_type=data.gap_type,
        description=data.description,
        severity=data.severity,
        status=data.status,
        suggested_action=data.suggested_action,
    )
    db.add(gap)
    db.commit()
    db.refresh(gap)
    return gap

def update_knowledge_gap(db: Session, gap_id: str, data: KnowledgeGapUpdate) -> Optional[KnowledgeGap]:
    gap = db.query(KnowledgeGap).filter(KnowledgeGap.id == gap_id).first()
    if not gap:
        return None
    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(gap, field, val)
    db.commit()
    db.refresh(gap)
    return gap
