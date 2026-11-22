from datetime import datetime, timezone
import json
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    ForeignKey,
    Integer,
    Boolean,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.db.database import Base


class Board(Base):
    __tablename__ = "boards"

    id = Column(String(64), primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(150), nullable=False, index=True)
    description = Column(Text, nullable=True)
    board_type = Column(String(50), default="kanban", nullable=False)  # kanban, scrum, list, custom
    visibility = Column(String(50), default="workspace", nullable=False)  # private, workspace, project, organization
    settings_json = Column(Text, default="{}", nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False, index=True)
    archived_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id])
    workspace = relationship("Workspace", foreign_keys=[workspace_id])
    project = relationship("Project", foreign_keys=[project_id])
    columns = relationship(
        "BoardColumn",
        back_populates="board",
        cascade="all, delete-orphan",
        order_by="BoardColumn.position",
    )
    views = relationship(
        "BoardView",
        back_populates="board",
        cascade="all, delete-orphan",
    )

    @property
    def settings(self):
        try:
            return json.loads(self.settings_json) if self.settings_json else {}
        except Exception:
            return {}

    @settings.setter
    def settings(self, val):
        self.settings_json = json.dumps(val) if val is not None else "{}"

    __table_args__ = (
        Index("ix_boards_ws_archived", "workspace_id", "is_archived"),
        Index("ix_boards_proj_archived", "project_id", "is_archived"),
    )


class BoardColumn(Base):
    __tablename__ = "board_columns"

    id = Column(String(64), primary_key=True, index=True)
    board_id = Column(String(64), ForeignKey("boards.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    status_value = Column(String(50), nullable=False, index=True)  # Maps to Task.status (e.g. "Todo", "In Progress", "Completed")
    position = Column(Integer, default=0, nullable=False)
    color = Column(String(32), default="#6366f1", nullable=False)
    description = Column(Text, nullable=True)
    wip_limit = Column(Integer, nullable=True)  # Work-In-Progress limit (max tasks in column)
    is_visible = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    board = relationship("Board", back_populates="columns")

    __table_args__ = (
        Index("ix_board_cols_order", "board_id", "position"),
    )


class BoardView(Base):
    __tablename__ = "board_views"

    id = Column(String(64), primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    board_id = Column(String(64), ForeignKey("boards.id", ondelete="CASCADE"), nullable=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(150), nullable=False, index=True)
    view_type = Column(String(50), default="kanban", nullable=False)  # kanban, list, calendar, timeline, table
    visibility = Column(String(50), default="workspace", nullable=False)  # private, workspace, project, organization
    
    # Configuration JSON objects
    filters_json = Column(Text, default="{}", nullable=False)
    sort_json = Column(Text, default="[]", nullable=False)
    group_json = Column(Text, default="{}", nullable=False)
    column_config_json = Column(Text, default="[]", nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    owner = relationship("User", foreign_keys=[owner_id])
    board = relationship("Board", back_populates="views")

    @property
    def filters(self):
        try:
            return json.loads(self.filters_json) if self.filters_json else {}
        except Exception:
            return {}

    @filters.setter
    def filters(self, val):
        self.filters_json = json.dumps(val) if val is not None else "{}"

    @property
    def sort_config(self):
        try:
            return json.loads(self.sort_json) if self.sort_json else []
        except Exception:
            return []

    @sort_config.setter
    def sort_config(self, val):
        self.sort_json = json.dumps(val) if val is not None else "[]"

    @property
    def group_config(self):
        try:
            return json.loads(self.group_json) if self.group_json else {}
        except Exception:
            return {}

    @group_config.setter
    def group_config(self, val):
        self.group_json = json.dumps(val) if val is not None else "{}"

    @property
    def column_config(self):
        try:
            return json.loads(self.column_config_json) if self.column_config_json else []
        except Exception:
            return []

    @column_config.setter
    def column_config(self, val):
        self.column_config_json = json.dumps(val) if val is not None else "[]"

    __table_args__ = (
        Index("ix_board_views_ws_type", "workspace_id", "view_type"),
        Index("ix_board_views_proj_type", "project_id", "view_type"),
    )


class SavedFilter(Base):
    __tablename__ = "saved_filters"

    id = Column(String(64), primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(150), nullable=False, index=True)
    description = Column(Text, nullable=True)
    filter_type = Column(String(50), default="task", nullable=False)
    query_json = Column(Text, default="{}", nullable=False)
    is_shared = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User", foreign_keys=[user_id])

    @property
    def query_config(self):
        try:
            return json.loads(self.query_json) if self.query_json else {}
        except Exception:
            return {}

    @query_config.setter
    def query_config(self, val):
        self.query_json = json.dumps(val) if val is not None else "{}"
