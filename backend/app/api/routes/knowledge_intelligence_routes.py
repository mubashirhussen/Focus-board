from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.knowledge_intelligence import (
    KnowledgeDocumentCreate,
    KnowledgeDocumentUpdate,
    KnowledgeDocumentResponse,
    KnowledgeDocumentVersionResponse,
    KnowledgeDocumentChunkResponse,
    KnowledgeDocumentLinkCreate,
    KnowledgeDocumentLinkResponse,
    DocumentUploadResponse,
    DocumentSummaryResponse,
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

@router.post("/documents/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    workspace_id: Optional[int] = Form(None),
    category: str = Form("Engineering"),
    document_type: str = Form("SPECIFICATION"),
    visibility: str = Form("INTERNAL"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a knowledge document file (.txt, .md, .csv, .json, .html, .docx, .pdf), extract text, and chunk embeddings."""
    content_bytes = await file.read()
    filename = file.filename or "uploaded_document.txt"
    mime_type = file.content_type

    doc, chunks_count, chars_count = knowledge_intelligence_service.upload_document(
        db,
        file_bytes=content_bytes,
        filename=filename,
        mime_type=mime_type,
        workspace_id=workspace_id,
        category=category,
        document_type=document_type,
        visibility=visibility,
        author_id=current_user.id,
    )

    doc_response = {
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
        "original_filename": doc.original_filename,
        "file_size": doc.file_size,
        "mime_type": doc.mime_type,
        "processing_status": doc.processing_status,
        "summary": doc.summary,
        "created_at": doc.created_at,
        "updated_at": doc.updated_at,
        "versions_count": len(doc.versions),
    }

    return {
        "document": doc_response,
        "chunks_count": chunks_count,
        "extracted_characters": chars_count,
    }

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
        "original_filename": doc.original_filename,
        "file_size": doc.file_size or 0,
        "mime_type": doc.mime_type,
        "processing_status": doc.processing_status or "COMPLETED",
        "summary": doc.summary,
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
        "original_filename": doc.original_filename,
        "file_size": doc.file_size or 0,
        "mime_type": doc.mime_type,
        "processing_status": doc.processing_status or "COMPLETED",
        "summary": doc.summary,
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
        "original_filename": doc.original_filename,
        "file_size": doc.file_size or 0,
        "mime_type": doc.mime_type,
        "processing_status": doc.processing_status or "COMPLETED",
        "summary": doc.summary,
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

@router.get("/documents/{doc_id}/chunks", response_model=List[KnowledgeDocumentChunkResponse])
def get_document_chunks(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve indexed text chunks and metadata for a knowledge document."""
    return knowledge_intelligence_service.get_document_chunks(db, doc_id)

@router.post("/documents/{doc_id}/links", response_model=KnowledgeDocumentLinkResponse, status_code=status.HTTP_201_CREATED)
def link_document(
    doc_id: str,
    payload: KnowledgeDocumentLinkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Link a document to a task, project, workspace, or collection."""
    link = knowledge_intelligence_service.link_document_to_entity(
        db,
        doc_id=doc_id,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        user_id=current_user.id,
    )
    if not link:
        raise HTTPException(status_code=404, detail="Knowledge document not found")
    return link

@router.delete("/documents/{doc_id}/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def unlink_document(
    doc_id: str,
    link_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a link from a document."""
    success = knowledge_intelligence_service.unlink_document_entity(db, doc_id=doc_id, link_id=link_id)
    if not success:
        raise HTTPException(status_code=404, detail="Knowledge document link not found")
    return None

@router.get("/documents/{doc_id}/links", response_model=List[KnowledgeDocumentLinkResponse])
def get_document_links(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List entity links for a given document."""
    return knowledge_intelligence_service.get_document_links(db, doc_id)

@router.get("/documents/{doc_id}/summarize", response_model=DocumentSummaryResponse)
def summarize_document(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate structured summary with key takeaways for a document."""
    res = knowledge_intelligence_service.summarize_document(db, doc_id)
    if not res:
        raise HTTPException(status_code=404, detail="Knowledge document not found")
    return res

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
