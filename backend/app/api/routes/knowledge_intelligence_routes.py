from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.knowledge_intelligence import (
    KnowledgeDocumentCreate,
    KnowledgeDocumentUpdate,
    KnowledgeDocumentResponse,
    KnowledgeDocumentVersionResponse,
    KnowledgeCollectionCreate,
    KnowledgeCollectionResponse,
    KnowledgeEntityCreate,
    KnowledgeEntityResponse,
    KnowledgeRelationshipCreate,
    KnowledgeRelationshipResponse,
    OrganizationalMemoryCreate,
    OrganizationalMemoryResponse,
    KnowledgeGapCreate,
    KnowledgeGapUpdate,
    KnowledgeGapResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
    KnowledgeGraphExplorerResponse,
    AIKnowledgeQueryRequest,
    AIKnowledgeQueryResponse,
    KnowledgeDashboardOverviewResponse,
)
from app.services import knowledge_intelligence_service

router = APIRouter(prefix="/knowledge", tags=["FocusBoard SaaS Knowledge Intelligence"])

@router.get("/overview", response_model=KnowledgeDashboardOverviewResponse)
def get_knowledge_overview(
    workspace_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve Knowledge Hub overview: document counts, verified documents, quality scores, graph stats, and open gaps."""
    return knowledge_intelligence_service.get_knowledge_overview(db, workspace_id=workspace_id)

# --- Documents ---
@router.get("/documents", response_model=List[KnowledgeDocumentResponse])
def list_documents(
    workspace_id: Optional[int] = Query(None),
    category: Optional[str] = Query(None),
    document_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return knowledge_intelligence_service.get_documents(
        db,
        workspace_id=workspace_id,
        category=category,
        document_type=document_type,
        status=status,
        limit=limit,
        offset=offset,
    )

@router.get("/documents/{doc_id}", response_model=KnowledgeDocumentResponse)
def get_document(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = knowledge_intelligence_service.get_document_by_id(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Knowledge document not found")
    return {
        "id": doc.id,
        "workspace_id": doc.workspace_id,
        "title": doc.title,
        "slug": doc.slug,
        "content": doc.content,
        "document_type": doc.document_type,
        "category": doc.category,
        "visibility": doc.visibility,
        "status": doc.status,
        "version": doc.version,
        "author_id": doc.author_id,
        "quality_score": doc.quality_score,
        "created_at": doc.created_at,
        "updated_at": doc.updated_at,
        "versions_count": len(doc.versions),
    }

@router.post("/documents", response_model=KnowledgeDocumentResponse, status_code=status.HTTP_201_CREATED)
def create_document(
    data: KnowledgeDocumentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = knowledge_intelligence_service.create_document(db, data, author_id=current_user.id)
    return {
        "id": doc.id,
        "workspace_id": doc.workspace_id,
        "title": doc.title,
        "slug": doc.slug,
        "content": doc.content,
        "document_type": doc.document_type,
        "category": doc.category,
        "visibility": doc.visibility,
        "status": doc.status,
        "version": doc.version,
        "author_id": doc.author_id,
        "quality_score": doc.quality_score,
        "created_at": doc.created_at,
        "updated_at": doc.updated_at,
        "versions_count": 1,
    }

@router.patch("/documents/{doc_id}", response_model=KnowledgeDocumentResponse)
def update_document(
    doc_id: str,
    data: KnowledgeDocumentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = knowledge_intelligence_service.update_document(db, doc_id, data, editor_id=current_user.id)
    if not doc:
        raise HTTPException(status_code=404, detail="Knowledge document not found")
    return {
        "id": doc.id,
        "workspace_id": doc.workspace_id,
        "title": doc.title,
        "slug": doc.slug,
        "content": doc.content,
        "document_type": doc.document_type,
        "category": doc.category,
        "visibility": doc.visibility,
        "status": doc.status,
        "version": doc.version,
        "author_id": doc.author_id,
        "quality_score": doc.quality_score,
        "created_at": doc.created_at,
        "updated_at": doc.updated_at,
        "versions_count": len(doc.versions),
    }

@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    success = knowledge_intelligence_service.delete_document(db, doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Knowledge document not found")
    return None

@router.get("/documents/{doc_id}/versions", response_model=List[KnowledgeDocumentVersionResponse])
def get_document_versions(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return knowledge_intelligence_service.get_document_versions(db, doc_id)

# --- Collections ---
@router.get("/collections", response_model=List[KnowledgeCollectionResponse])
def list_collections(
    workspace_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return knowledge_intelligence_service.get_collections(db, workspace_id=workspace_id)

@router.post("/collections", response_model=KnowledgeCollectionResponse, status_code=status.HTTP_201_CREATED)
def create_collection(
    data: KnowledgeCollectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return knowledge_intelligence_service.create_collection(db, data, owner_id=current_user.id)

# --- Graph Explorer ---
@router.get("/graph", response_model=KnowledgeGraphExplorerResponse)
def get_knowledge_graph(
    entity_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return knowledge_intelligence_service.get_knowledge_graph(db, entity_type=entity_type)

@router.post("/graph/entities", response_model=KnowledgeEntityResponse, status_code=status.HTTP_201_CREATED)
def create_graph_entity(
    data: KnowledgeEntityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return knowledge_intelligence_service.create_knowledge_entity(db, data)

@router.post("/graph/relationships", response_model=KnowledgeRelationshipResponse, status_code=status.HTTP_201_CREATED)
def create_graph_relationship(
    data: KnowledgeRelationshipCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return knowledge_intelligence_service.create_knowledge_relationship(db, data)

# --- Semantic & Hybrid Search ---
@router.post("/search", response_model=SemanticSearchResponse)
def search_knowledge_base(
    payload: SemanticSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Execute hybrid semantic search across documents and knowledge nodes with permission isolation."""
    return knowledge_intelligence_service.semantic_search(
        db,
        query=payload.query,
        workspace_id=payload.workspace_id,
        category=payload.category,
        limit=payload.limit,
    )

# --- AI Knowledge Assistant ---
@router.post("/assistant/query", response_model=AIKnowledgeQueryResponse)
def query_ai_assistant(
    payload: AIKnowledgeQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Ask AI Knowledge Assistant questions with verified source attribution citations."""
    return knowledge_intelligence_service.query_ai_knowledge_assistant(
        db,
        question=payload.question,
        workspace_id=payload.workspace_id,
    )

# --- Organizational Memories ---
@router.get("/memories", response_model=List[OrganizationalMemoryResponse])
def list_memories(
    memory_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return knowledge_intelligence_service.get_memories(db, memory_type=memory_type)

@router.post("/memories", response_model=OrganizationalMemoryResponse, status_code=status.HTTP_201_CREATED)
def create_memory(
    data: OrganizationalMemoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return knowledge_intelligence_service.create_memory(db, data)

# --- Knowledge Gaps ---
@router.get("/gaps", response_model=List[KnowledgeGapResponse])
def list_knowledge_gaps(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return knowledge_intelligence_service.get_knowledge_gaps(db, status=status, severity=severity)

@router.post("/gaps", response_model=KnowledgeGapResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_gap(
    data: KnowledgeGapCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return knowledge_intelligence_service.create_knowledge_gap(db, data)

@router.patch("/gaps/{gap_id}", response_model=KnowledgeGapResponse)
def update_knowledge_gap(
    gap_id: str,
    data: KnowledgeGapUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    gap = knowledge_intelligence_service.update_knowledge_gap(db, gap_id, data)
    if not gap:
        raise HTTPException(status_code=404, detail="Knowledge gap not found")
    return gap
