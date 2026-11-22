from datetime import datetime, timezone
import json
from typing import Dict, Any, Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from app.db.database import Base

def utc_now() -> datetime:
    return datetime.utcnow()

class SearchHistory(Base):
    __tablename__ = "search_histories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    query = Column(String(255), nullable=False)
    normalized_query = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(32), default="ALL", nullable=False)
    filters_json = Column(Text, nullable=True)
    result_count = Column(Integer, default=0, nullable=False)
    last_searched_at = Column(DateTime, default=utc_now, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index("ix_search_history_user_last_searched", "user_id", "last_searched_at"),
    )

    @property
    def filters(self) -> Dict[str, Any]:
        try:
            return json.loads(self.filters_json or "{}")
        except Exception:
            return {}

    @filters.setter
    def filters(self, val: Dict[str, Any]):
        self.filters_json = json.dumps(val or {})


class SavedSearch(Base):
    __tablename__ = "saved_searches"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    entity_type = Column(String(32), default="TASK", nullable=False)  # TASK, PROJECT, GLOBAL, BOARD, TEAM, WORKSPACE
    query = Column(String(255), nullable=True)
    filter_definition_json = Column(Text, default="{}", nullable=False)
    sorting_config_json = Column(Text, default="{}", nullable=False)
    is_shared = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    organization = relationship("Organization", foreign_keys=[organization_id])

    __table_args__ = (
        Index("ix_saved_searches_user_entity", "user_id", "entity_type"),
        Index("ix_saved_searches_org_shared", "organization_id", "is_shared"),
    )

    @property
    def filter_definition(self) -> Dict[str, Any]:
        try:
            return json.loads(self.filter_definition_json or "{}")
        except Exception:
            return {}

    @filter_definition.setter
    def filter_definition(self, val: Dict[str, Any]):
        self.filter_definition_json = json.dumps(val or {})

    @property
    def sorting_config(self) -> Dict[str, Any]:
        try:
            return json.loads(self.sorting_config_json or "{}")
        except Exception:
            return {}

    @sorting_config.setter
    def sorting_config(self, val: Dict[str, Any]):
        self.sorting_config_json = json.dumps(val or {})
