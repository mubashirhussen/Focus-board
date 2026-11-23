import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, Index
from sqlalchemy.orm import relationship
from app.db.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(String(64), primary_key=True, default=lambda: f"dsrc_{uuid.uuid4().hex[:12]}")
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(150), nullable=False)
    source_type = Column(String(50), default="INTERNAL_DB", nullable=False, index=True)  # INTERNAL_DB, POSTGRESQL, SNOWFLAKE, BIGQUERY, API, CSV_UPLOAD
    connection_status = Column(String(30), default="CONNECTED", nullable=False)  # CONNECTED, DISCONNECTED, ERROR, TESTING
    config_json = Column(Text, default="{}", nullable=False)
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    workspace = relationship("Workspace")

class AnalyticsDataset(Base):
    __tablename__ = "analytics_datasets"

    id = Column(String(64), primary_key=True, default=lambda: f"ds_{uuid.uuid4().hex[:12]}")
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(120), nullable=False)
    slug = Column(String(120), unique=True, nullable=False)
    category = Column(String(60), default="PRODUCTIVITY", nullable=False)  # PRODUCTIVITY, PROJECT, AUTOMATION, FINANCIAL, AI, INTEGRATIONS, OPERATIONS, KNOWLEDGE
    description = Column(Text, nullable=False)
    data_source = Column(String(100), nullable=False)
    source_type = Column(String(64), default="DATABASE", nullable=False)
    classification = Column(String(32), default="INTERNAL", nullable=False)  # PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED
    freshness_status = Column(String(20), default="FRESH", nullable=False)  # FRESH, DELAYED, STALE
    record_count = Column(Integer, default=0, nullable=False)
    schema_json = Column(Text, default="[]", nullable=False)
    last_refreshed_at = Column(DateTime, default=utc_now, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    workspace = relationship("Workspace")

    __table_args__ = (
        Index("ix_analytics_datasets_category", "category"),
        Index("ix_analytics_datasets_freshness", "freshness_status"),
    )

class AnalyticsMetricDefinition(Base):
    __tablename__ = "analytics_metric_definitions"

    id = Column(String(64), primary_key=True, default=lambda: f"met_{uuid.uuid4().hex[:12]}")
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    identifier = Column(String(100), unique=True, nullable=False)
    name = Column(String(120), nullable=False)
    category = Column(String(60), nullable=False)
    description = Column(Text, nullable=False)
    calculation_method = Column(String(100), nullable=False)
    unit = Column(String(30), default="count", nullable=False)
    aggregation_method = Column(String(30), default="SUM", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index("ix_analytics_metric_definitions_cat", "category"),
    )

class AnalyticsDataPipeline(Base):
    __tablename__ = "analytics_data_pipelines"

    id = Column(String(64), primary_key=True, default=lambda: f"pipe_{uuid.uuid4().hex[:12]}")
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=False)
    source_dataset_slug = Column(String(120), nullable=False)
    target_model = Column(String(100), nullable=False)
    pipeline_config_json = Column(Text, default="{}", nullable=False)
    schedule_cron = Column(String(50), default="0 * * * *", nullable=False)
    status = Column(String(20), default="ACTIVE", nullable=False)  # ACTIVE, PAUSED
    last_run_at = Column(DateTime, nullable=True)
    last_run_status = Column(String(20), default="SUCCESS", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    workspace = relationship("Workspace")
    executions = relationship("AnalyticsPipelineExecution", back_populates="pipeline", cascade="all, delete-orphan")

class AnalyticsPipelineExecution(Base):
    __tablename__ = "analytics_pipeline_executions"

    id = Column(String(64), primary_key=True, default=lambda: f"pipe_exec_{uuid.uuid4().hex[:12]}")
    pipeline_id = Column(String(64), ForeignKey("analytics_data_pipelines.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), default="COMPLETED", nullable=False)  # QUEUED, RUNNING, COMPLETED, FAILED
    records_processed = Column(Integer, default=0, nullable=False)
    duration_ms = Column(Integer, default=0, nullable=False)
    logs_json = Column(Text, default="[]", nullable=False)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    pipeline = relationship("AnalyticsDataPipeline", back_populates="executions")

class AnalyticsDashboard(Base):
    __tablename__ = "analytics_dashboards"

    id = Column(String(64), primary_key=True, default=lambda: f"dash_{uuid.uuid4().hex[:12]}")
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    visibility = Column(String(20), default="WORKSPACE", nullable=False)  # PRIVATE, WORKSPACE, ORGANIZATION
    layout_json = Column(Text, default="[]", nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    workspace = relationship("Workspace")
    owner = relationship("User", foreign_keys=[owner_id])
    widgets = relationship("AnalyticsWidget", back_populates="dashboard", cascade="all, delete-orphan")

class AnalyticsWidget(Base):
    __tablename__ = "analytics_widgets"

    id = Column(String(64), primary_key=True, default=lambda: f"wid_{uuid.uuid4().hex[:12]}")
    dashboard_id = Column(String(64), ForeignKey("analytics_dashboards.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(150), nullable=False)
    widget_type = Column(String(30), default="KPI", nullable=False)  # KPI, LINE, BAR, TABLE, PIE
    metric_identifier = Column(String(100), nullable=False)
    config_json = Column(Text, default="{}", nullable=False)
    position_order = Column(Integer, default=0, nullable=False)

    dashboard = relationship("AnalyticsDashboard", back_populates="widgets")

class AnalyticsCustomReport(Base):
    __tablename__ = "analytics_custom_reports"

    id = Column(String(64), primary_key=True, default=lambda: f"rep_{uuid.uuid4().hex[:12]}")
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(150), nullable=False)
    category = Column(String(60), default="PRODUCTIVITY", nullable=False)
    query_config_json = Column(Text, default="{}", nullable=False)
    format = Column(String(20), default="CSV", nullable=False)  # CSV, JSON, SUMMARY
    schedule_cron = Column(String(50), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    last_run_at = Column(DateTime, nullable=True)

    workspace = relationship("Workspace")
    created_by = relationship("User", foreign_keys=[created_by_id])

class DataQualityRule(Base):
    __tablename__ = "data_quality_rules"

    id = Column(String(64), primary_key=True, default=lambda: f"dqr_{uuid.uuid4().hex[:12]}")
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    dataset_slug = Column(String(120), nullable=False)
    rule_name = Column(String(150), nullable=False)
    rule_type = Column(String(40), default="COMPLETENESS", nullable=False)  # COMPLETENESS, VALIDITY, FRESHNESS, CONSISTENCY, UNIQUENESS
    severity = Column(String(20), default="WARNING", nullable=False)  # INFO, WARNING, ERROR, CRITICAL
    status = Column(String(20), default="PASS", nullable=False)  # PASS, FAIL
    condition_expr = Column(String(255), nullable=False)
    last_evaluated_at = Column(DateTime, default=utc_now, nullable=False)

    issues = relationship("DataQualityIssue", back_populates="rule", cascade="all, delete-orphan")

class DataQualityIssue(Base):
    __tablename__ = "data_quality_issues"

    id = Column(String(64), primary_key=True, default=lambda: f"dqi_{uuid.uuid4().hex[:12]}")
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    rule_id = Column(String(64), ForeignKey("data_quality_rules.id", ondelete="CASCADE"), nullable=False)
    dataset_slug = Column(String(120), nullable=False)
    issue_summary = Column(String(255), nullable=False)
    severity = Column(String(20), default="WARNING", nullable=False)
    status = Column(String(20), default="OPEN", nullable=False)  # OPEN, RESOLVED
    detected_at = Column(DateTime, default=utc_now, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    rule = relationship("DataQualityRule", back_populates="issues")

class DataLineageNode(Base):
    __tablename__ = "data_lineage_nodes"

    id = Column(String(64), primary_key=True, default=lambda: f"lin_{uuid.uuid4().hex[:12]}")
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    source_asset_id = Column(String(64), nullable=False, index=True)
    target_asset_id = Column(String(64), nullable=False, index=True)
    lineage_type = Column(String(50), default="SOURCE_TO_DATASET", nullable=False)  # SOURCE_TO_DATASET, DATASET_TO_PIPELINE, PIPELINE_TO_REPORT, TRANSFORMATION
    transformation_details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

class DataInsight(Base):
    __tablename__ = "data_insights"

    id = Column(String(64), primary_key=True, default=lambda: f"ins_{uuid.uuid4().hex[:12]}")
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    insight_type = Column(String(50), default="TREND", nullable=False, index=True)  # ANOMALY, TREND, QUALITY_ALERT, OPTIMIZATION
    severity = Column(String(30), default="INFO", nullable=False)  # INFO, WARNING, CRITICAL
    confidence_score = Column(Float, default=0.9, nullable=False)
    supporting_data_json = Column(Text, default="{}", nullable=False)
    status = Column(String(30), default="ACTIVE", nullable=False)  # ACTIVE, RESOLVED, DISMISSED
    created_at = Column(DateTime, default=utc_now, nullable=False)
