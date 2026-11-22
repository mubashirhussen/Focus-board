import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(String(64), primary_key=True, default=lambda: f"kdoc_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    document_type = Column(String(64), default="SPECIFICATION", nullable=False, index=True)
    # SPECIFICATION, DECISION_RECORD, RUNBOOK, RESEARCH, MEETING_NOTE, POSTMORTEM, LESSON_LEARNED
    category = Column(String(64), default="Engineering", nullable=False, index=True)
    visibility = Column(String(32), default="INTERNAL", nullable=False)  # INTERNAL, CONFIDENTIAL, PUBLIC
    status = Column(String(32), default="VERIFIED", nullable=False, index=True)  # DRAFT, IN_REVIEW, VERIFIED, NEEDS_UPDATE, ARCHIVED
    version = Column(String(16), default="1.0", nullable=False)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    quality_score = Column(Float, default=92.0, nullable=False)  # 0 to 100
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    author = relationship("User", foreign_keys=[author_id])
    workspace = relationship("Workspace", foreign_keys=[workspace_id])
    versions = relationship("KnowledgeDocumentVersion", back_populates="document", cascade="all, delete-orphan")

class KnowledgeDocumentVersion(Base):
    __tablename__ = "knowledge_document_versions"

    id = Column(String(64), primary_key=True, default=lambda: f"kdver_{uuid.uuid4().hex[:12]}")
    document_id = Column(String(64), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(String(16), nullable=False)
    content = Column(Text, nullable=False)
    change_summary = Column(String(255), default="Incremental documentation refinement", nullable=False)
    editor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    document = relationship("KnowledgeDocument", back_populates="versions")
    editor = relationship("User", foreign_keys=[editor_id])

class KnowledgeCollection(Base):
    __tablename__ = "knowledge_collections"

    id = Column(String(64), primary_key=True, default=lambda: f"kcol_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    icon = Column(String(64), default="BookOpen", nullable=False)
    is_cross_workspace = Column(Boolean, default=False, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    owner = relationship("User", foreign_keys=[owner_id])
    workspace = relationship("Workspace", foreign_keys=[workspace_id])

class KnowledgeEntity(Base):
    __tablename__ = "knowledge_entities"

    id = Column(String(64), primary_key=True, default=lambda: f"kenti_{uuid.uuid4().hex[:12]}")
    entity_type = Column(String(64), nullable=False, index=True)
    # PROJECT, TASK, DECISION, PERSON, COMPETITOR, TECHNOLOGY, STRATEGY_GOAL, INNOVATION_IDEA
    name = Column(String(255), nullable=False, index=True)
    canonical_id = Column(String(128), nullable=True, index=True)  # e.g. task:12, project:2, idea:idea_01
    metadata_json = Column(Text, default="{}", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    outgoing_relationships = relationship(
        "KnowledgeRelationship",
        foreign_keys="KnowledgeRelationship.source_entity_id",
        back_populates="source_entity",
        cascade="all, delete-orphan",
    )
    incoming_relationships = relationship(
        "KnowledgeRelationship",
        foreign_keys="KnowledgeRelationship.target_entity_id",
        back_populates="target_entity",
        cascade="all, delete-orphan",
    )

class KnowledgeRelationship(Base):
    __tablename__ = "knowledge_relationships"

    id = Column(String(64), primary_key=True, default=lambda: f"krel_{uuid.uuid4().hex[:12]}")
    source_entity_id = Column(String(64), ForeignKey("knowledge_entities.id", ondelete="CASCADE"), nullable=False, index=True)
    target_entity_id = Column(String(64), ForeignKey("knowledge_entities.id", ondelete="CASCADE"), nullable=False, index=True)
    relation_type = Column(String(64), nullable=False, index=True)
    # RELATES_TO, DEPENDS_ON, IMPLEMENTS, INFORMED_BY, VALIDATES, SUPERSEDES, CONTRADICTS
    confidence = Column(Float, default=1.0, nullable=False)
    provenance = Column(String(64), default="EXPLICIT_LINK", nullable=False)  # EXPLICIT_LINK, AI_INFERRED, TASK_REFERENCE
    created_at = Column(DateTime, default=utc_now, nullable=False)

    source_entity = relationship("KnowledgeEntity", foreign_keys=[source_entity_id], back_populates="outgoing_relationships")
    target_entity = relationship("KnowledgeEntity", foreign_keys=[target_entity_id], back_populates="incoming_relationships")

class OrganizationalMemory(Base):
    __tablename__ = "organizational_memories"

    id = Column(String(64), primary_key=True, default=lambda: f"omem_{uuid.uuid4().hex[:12]}")
    memory_type = Column(String(64), nullable=False, index=True)
    # FACT, ARCHITECTURAL_DECISION, LESSON_LEARNED, CUSTOMER_INSIGHT
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    confidence = Column(Float, default=0.95, nullable=False)
    source_reference = Column(String(255), nullable=True)
    is_verified = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

class KnowledgeGap(Base):
    __tablename__ = "knowledge_gaps"

    id = Column(String(64), primary_key=True, default=lambda: f"kgap_{uuid.uuid4().hex[:12]}")
    gap_type = Column(String(64), nullable=False, index=True)  # OUTDATED_DOC, MISSING_DECISION, UNASSIGNED_OWNER, FAILED_SEARCH_QUERY
    description = Column(Text, nullable=False)
    severity = Column(String(32), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH
    status = Column(String(32), default="OPEN", nullable=False, index=True)  # OPEN, RESOLVED, DISMISSED
    suggested_action = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
