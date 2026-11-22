from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# --- Knowledge Document ---
class KnowledgeDocumentBase(BaseModel):
    title: str
    slug: str
    content: str
    document_type: str = Field(default="SPECIFICATION", description="SPECIFICATION, DECISION_RECORD, RUNBOOK, RESEARCH, MEETING_NOTE, POSTMORTEM, LESSON_LEARNED")
    category: str = Field(default="Engineering")
    visibility: str = Field(default="INTERNAL", description="INTERNAL, CONFIDENTIAL, PUBLIC")
    status: str = Field(default="VERIFIED", description="DRAFT, IN_REVIEW, VERIFIED, NEEDS_UPDATE, ARCHIVED")
    version: str = "1.0"
    quality_score: float = 92.0
    original_filename: Optional[str] = None
    file_size: int = 0
    mime_type: Optional[str] = None
    processing_status: str = "COMPLETED"
    summary: Optional[str] = None

class KnowledgeDocumentCreate(KnowledgeDocumentBase):
    workspace_id: Optional[int] = None

class KnowledgeDocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    document_type: Optional[str] = None
    category: Optional[str] = None
    visibility: Optional[str] = None
    status: Optional[str] = None
    version: Optional[str] = None
    quality_score: Optional[float] = None
    change_summary: Optional[str] = None

class KnowledgeDocumentResponse(KnowledgeDocumentBase):
    id: str
    workspace_id: Optional[int] = None
    author_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    versions_count: int = 1

    model_config = ConfigDict(from_attributes=True)

# --- Version ---
class KnowledgeDocumentVersionResponse(BaseModel):
    id: str
    document_id: str
    version: str
    content: str
    change_summary: str
    editor_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Chunks & Embeddings ---
class KnowledgeDocumentChunkResponse(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    content: str
    heading: Optional[str] = None
    page_number: Optional[int] = None
    token_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Document Links ---
class KnowledgeDocumentLinkCreate(BaseModel):
    entity_type: str = Field(..., description="TASK, PROJECT, WORKSPACE, COLLECTION")
    entity_id: str

class KnowledgeDocumentLinkResponse(BaseModel):
    id: str
    document_id: str
    entity_type: str
    entity_id: str
    created_by: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DocumentUploadResponse(BaseModel):
    document: KnowledgeDocumentResponse
    chunks_count: int
    extracted_characters: int

class DocumentSummaryResponse(BaseModel):
    document_id: str
    title: str
    summary: str
    key_points: List[str]

# --- Knowledge Collection ---
class KnowledgeCollectionBase(BaseModel):
    name: str
    description: str
    icon: str = "BookOpen"
    is_cross_workspace: bool = False

class KnowledgeCollectionCreate(KnowledgeCollectionBase):
    workspace_id: Optional[int] = None

class KnowledgeCollectionResponse(KnowledgeCollectionBase):
    id: str
    workspace_id: Optional[int] = None
    owner_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Knowledge Entity & Relationship (Knowledge Graph) ---
class KnowledgeEntityBase(BaseModel):
    entity_type: str = Field(..., description="PROJECT, TASK, DECISION, PERSON, COMPETITOR, TECHNOLOGY, STRATEGY_GOAL, INNOVATION_IDEA")
    name: str
    canonical_id: Optional[str] = None
    metadata_json: str = "{}"

class KnowledgeEntityCreate(KnowledgeEntityBase):
    pass

class KnowledgeEntityResponse(KnowledgeEntityBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class KnowledgeRelationshipBase(BaseModel):
    source_entity_id: str
    target_entity_id: str
    relation_type: str = Field(..., description="RELATES_TO, DEPENDS_ON, IMPLEMENTS, INFORMED_BY, VALIDATES, SUPERSEDES, CONTRADICTS")
    confidence: float = 1.0
    provenance: str = "EXPLICIT_LINK"

class KnowledgeRelationshipCreate(KnowledgeRelationshipBase):
    pass

class KnowledgeRelationshipResponse(KnowledgeRelationshipBase):
    id: str
    source_name: Optional[str] = None
    target_name: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Organizational Memory ---
class OrganizationalMemoryBase(BaseModel):
    memory_type: str = Field(..., description="FACT, ARCHITECTURAL_DECISION, LESSON_LEARNED, CUSTOMER_INSIGHT")
    title: str
    summary: str
    confidence: float = 0.95
    source_reference: Optional[str] = None
    is_verified: bool = True

class OrganizationalMemoryCreate(OrganizationalMemoryBase):
    pass

class OrganizationalMemoryResponse(OrganizationalMemoryBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Knowledge Gap ---
class KnowledgeGapBase(BaseModel):
    gap_type: str = Field(..., description="OUTDATED_DOC, MISSING_DECISION, UNASSIGNED_OWNER, FAILED_SEARCH_QUERY")
    description: str
    severity: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH")
    status: str = Field(default="OPEN", description="OPEN, RESOLVED, DISMISSED")
    suggested_action: str

class KnowledgeGapCreate(KnowledgeGapBase):
    pass

class KnowledgeGapUpdate(BaseModel):
    status: Optional[str] = None
    description: Optional[str] = None
    suggested_action: Optional[str] = None

class KnowledgeGapResponse(KnowledgeGapBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Semantic & Hybrid Search ---
class SemanticSearchRequest(BaseModel):
    query: str
    workspace_id: Optional[int] = None
    category: Optional[str] = None
    limit: int = 10

class SemanticSearchHit(BaseModel):
    document_id: str
    title: str
    document_type: str
    category: str
    snippet: str
    relevance_score: float
    author_id: Optional[int] = None
    updated_at: datetime

class SemanticSearchResponse(BaseModel):
    query: str
    total_hits: int
    hits: List[SemanticSearchHit]

# --- Graph Explorer ---
class GraphNode(BaseModel):
    id: str
    label: str
    entity_type: str
    canonical_id: Optional[str] = None

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relation_type: str
    confidence: float

class KnowledgeGraphExplorerResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

# --- AI Knowledge Assistant with Citations ---
class AIKnowledgeQueryRequest(BaseModel):
    question: str
    workspace_id: Optional[int] = None

class AIKnowledgeCitation(BaseModel):
    source_id: str
    source_title: str
    source_type: str
    snippet: str
    relevance: float
    chunk_id: Optional[str] = None
    heading: Optional[str] = None
    page_number: Optional[int] = None

class AIKnowledgeQueryResponse(BaseModel):
    question: str
    answer: str
    confidence: float
    citations: List[AIKnowledgeCitation]

# --- Overview Dashboard ---
class KnowledgeDashboardOverviewResponse(BaseModel):
    total_documents_count: int
    verified_documents_count: int
    collections_count: int
    graph_entities_count: int
    graph_relationships_count: int
    open_knowledge_gaps_count: int
    average_quality_score: float
    recent_documents: List[KnowledgeDocumentResponse] = []
    active_memories: List[OrganizationalMemoryResponse] = []
    detected_gaps: List[KnowledgeGapResponse] = []
