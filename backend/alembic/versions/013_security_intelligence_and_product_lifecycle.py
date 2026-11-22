"""Add security intelligence, SOC, threat detection, and product lifecycle intelligence tables

Revision ID: 013_security_intelligence_and_product_lifecycle
Revises: 012_observability_and_data_intelligence
Create Date: 2026-11-22 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '013_security_intelligence_and_product_lifecycle'
down_revision = '012_observability_and_data_intelligence'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # --- PHASE 43: SECURITY INTELLIGENCE & ZERO TRUST SOC ---
    # 1. Security Events
    op.create_table(
        'security_events',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('severity', sa.String(length=32), server_default='INFO', nullable=False),
        sa.Column('actor_id', sa.Integer(), nullable=True),
        sa.Column('actor_email', sa.String(length=255), nullable=True),
        sa.Column('target_entity', sa.String(length=255), nullable=True),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(length=64), nullable=True),
        sa.Column('source', sa.String(length=64), server_default='SYSTEM', nullable=False),
        sa.Column('evidence_json', sa.Text(), server_default='{}', nullable=False),
        sa.Column('metadata_json', sa.Text(), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_security_events_event_type', 'security_events', ['event_type'])
    op.create_index('ix_security_events_severity', 'security_events', ['severity'])
    op.create_index('ix_security_events_created_at', 'security_events', ['created_at'])

    # 2. Security Detection Rules
    op.create_table(
        'security_detection_rules',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('rule_code', sa.String(length=64), unique=True, nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('condition_expression', sa.String(length=255), nullable=False),
        sa.Column('threshold_count', sa.Integer(), server_default='5', nullable=False),
        sa.Column('time_window_seconds', sa.Integer(), server_default='300', nullable=False),
        sa.Column('severity', sa.String(length=32), server_default='HIGH', nullable=False),
        sa.Column('is_enabled', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_security_detection_rules_rule_code', 'security_detection_rules', ['rule_code'])

    # 3. Security Detection Results
    op.create_table(
        'security_detection_results',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('rule_id', sa.String(length=64), nullable=False),
        sa.Column('rule_code', sa.String(length=64), nullable=False),
        sa.Column('severity', sa.String(length=32), server_default='HIGH', nullable=False),
        sa.Column('matched_count', sa.Integer(), server_default='1', nullable=False),
        sa.Column('target_entity', sa.String(length=255), nullable=True),
        sa.Column('evidence_summary', sa.Text(), nullable=False),
        sa.Column('detected_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['rule_id'], ['security_detection_rules.id'], ondelete='CASCADE'),
    )

    # 4. Security Alerts
    op.create_table(
        'security_alerts',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('alert_code', sa.String(length=64), unique=True, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=32), server_default='HIGH', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='OPEN', nullable=False),
        sa.Column('source', sa.String(length=64), server_default='THREAT_DETECTION', nullable=False),
        sa.Column('detection_rule_id', sa.String(length=64), nullable=True),
        sa.Column('assigned_to_id', sa.Integer(), nullable=True),
        sa.Column('actor_email', sa.String(length=255), nullable=True),
        sa.Column('target_entity', sa.String(length=255), nullable=True),
        sa.Column('evidence_json', sa.Text(), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['detection_rule_id'], ['security_detection_rules.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_security_alerts_status', 'security_alerts', ['status'])
    op.create_index('ix_security_alerts_severity', 'security_alerts', ['severity'])

    # 5. Identity Risk Records
    op.create_table(
        'identity_risk_records',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('risk_type', sa.String(length=64), nullable=False),
        sa.Column('severity', sa.String(length=32), server_default='MEDIUM', nullable=False),
        sa.Column('risk_score', sa.Integer(), server_default='50', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='ACTIVE', nullable=False),
        sa.Column('details', sa.Text(), nullable=False),
        sa.Column('detected_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_identity_risk_records_status', 'identity_risk_records', ['status'])

    # 6. Access Review Campaigns
    op.create_table(
        'access_review_campaigns',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('scope_type', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='PENDING', nullable=False),
        sa.Column('reviewer_id', sa.Integer(), nullable=True),
        sa.Column('deadline_date', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], ondelete='SET NULL'),
    )

    # 7. Access Review Records
    op.create_table(
        'access_review_records',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('campaign_id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_or_permission', sa.String(length=128), nullable=False),
        sa.Column('resource_name', sa.String(length=128), nullable=False),
        sa.Column('decision', sa.String(length=32), server_default='PENDING', nullable=False),
        sa.Column('justification', sa.Text(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['campaign_id'], ['access_review_campaigns.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by_id'], ['users.id'], ondelete='SET NULL'),
    )

    # 8. Vulnerability Records
    op.create_table(
        'vulnerability_records',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('cve_id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('component', sa.String(length=128), nullable=False),
        sa.Column('severity', sa.String(length=32), server_default='MEDIUM', nullable=False),
        sa.Column('source', sa.String(length=64), server_default='DEPENDENCY_SCAN', nullable=False),
        sa.Column('remediation_status', sa.String(length=32), server_default='OPEN', nullable=False),
        sa.Column('remediation_owner_id', sa.Integer(), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('detected_at', sa.DateTime(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['remediation_owner_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_vulnerability_records_cve_id', 'vulnerability_records', ['cve_id'])
    op.create_index('ix_vulnerability_records_remediation_status', 'vulnerability_records', ['remediation_status'])

    # 9. Security Posture Assessments
    op.create_table(
        'security_posture_assessments',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('assessment_date', sa.DateTime(), nullable=False),
        sa.Column('overall_score', sa.Integer(), server_default='85', nullable=False),
        sa.Column('category_scores_json', sa.Text(), server_default='{}', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='COMPLETED', nullable=False),
        sa.Column('assessed_by_id', sa.Integer(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['assessed_by_id'], ['users.id'], ondelete='SET NULL'),
    )

    # 10. Security Posture Findings
    op.create_table(
        'security_posture_findings',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('assessment_id', sa.String(length=64), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('severity', sa.String(length=32), server_default='MEDIUM', nullable=False),
        sa.Column('control_ref', sa.String(length=64), nullable=False),
        sa.Column('remediation_guidance', sa.Text(), nullable=False),
        sa.Column('is_resolved', sa.Boolean(), server_default='0', nullable=False),
        sa.ForeignKeyConstraint(['assessment_id'], ['security_posture_assessments.id'], ondelete='CASCADE'),
    )

    # 11. Security Remediations
    op.create_table(
        'security_remediations',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('finding_type', sa.String(length=64), nullable=False),
        sa.Column('finding_id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('priority', sa.String(length=32), server_default='MEDIUM', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='OPEN', nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_security_remediations_status', 'security_remediations', ['status'])

    # --- PHASE 45: PRODUCT LIFECYCLE INTELLIGENCE ---
    # 12. Product Discoveries
    op.create_table(
        'product_discoveries',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('problem_statement', sa.Text(), nullable=False),
        sa.Column('hypothesis', sa.Text(), nullable=False),
        sa.Column('target_users', sa.String(length=255), nullable=False),
        sa.Column('customer_segment', sa.String(length=64), server_default='ENTERPRISE', nullable=False),
        sa.Column('business_impact', sa.Text(), nullable=False),
        sa.Column('customer_impact', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='DISCOVERED', nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_product_discoveries_status', 'product_discoveries', ['status'])

    # 13. Product Ideas
    op.create_table(
        'product_ideas',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('discovery_id', sa.String(length=64), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('problem_statement', sa.Text(), nullable=False),
        sa.Column('proposed_solution', sa.Text(), nullable=False),
        sa.Column('product_area', sa.String(length=64), server_default='CORE_PLATFORM', nullable=False),
        sa.Column('category', sa.String(length=64), server_default='PRODUCTIVITY', nullable=False),
        sa.Column('priority', sa.String(length=32), server_default='MEDIUM', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='NEW', nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.Column('tags_json', sa.Text(), server_default='[]', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['discovery_id'], ['product_discoveries.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_product_ideas_status', 'product_ideas', ['status'])

    # 14. Product Feature Requests
    op.create_table(
        'product_feature_requests',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('customer_name', sa.String(length=128), nullable=False),
        sa.Column('customer_segment', sa.String(length=64), server_default='ENTERPRISE', nullable=False),
        sa.Column('source', sa.String(length=64), server_default='CUSTOMER_FEEDBACK', nullable=False),
        sa.Column('request_count', sa.Integer(), server_default='1', nullable=False),
        sa.Column('priority', sa.String(length=32), server_default='MEDIUM', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='NEW', nullable=False),
        sa.Column('business_impact', sa.Text(), nullable=True),
        sa.Column('revenue_impact', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('merged_into_id', sa.String(length=64), nullable=True),
        sa.Column('linked_idea_id', sa.String(length=64), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['merged_into_id'], ['product_feature_requests.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['linked_idea_id'], ['product_ideas.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_product_feature_requests_status', 'product_feature_requests', ['status'])

    # 15. Product Opportunities
    op.create_table(
        'product_opportunities',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('problem_statement', sa.Text(), nullable=False),
        sa.Column('customer_segment', sa.String(length=64), server_default='ALL', nullable=False),
        sa.Column('market_segment', sa.String(length=64), server_default='B2B_SAAS', nullable=False),
        sa.Column('product_area', sa.String(length=64), server_default='CORE_PLATFORM', nullable=False),
        sa.Column('business_impact', sa.Text(), nullable=False),
        sa.Column('customer_impact', sa.Text(), nullable=False),
        sa.Column('revenue_potential', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('effort_estimate', sa.String(length=32), server_default='MEDIUM', nullable=False),
        sa.Column('risk_level', sa.String(length=32), server_default='LOW', nullable=False),
        sa.Column('validation_status', sa.String(length=32), server_default='IDENTIFIED', nullable=False),
        sa.Column('priority', sa.String(length=32), server_default='MEDIUM', nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_product_opportunities_validation_status', 'product_opportunities', ['validation_status'])

    # 16. Product Prioritization Items
    op.create_table(
        'product_prioritization_items',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('item_type', sa.String(length=64), server_default='FEATURE_REQUEST', nullable=False),
        sa.Column('item_id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('reach', sa.Float(), server_default='100.0', nullable=False),
        sa.Column('impact', sa.Float(), server_default='3.0', nullable=False),
        sa.Column('confidence', sa.Float(), server_default='0.8', nullable=False),
        sa.Column('effort', sa.Float(), server_default='2.0', nullable=False),
        sa.Column('rice_score', sa.Float(), server_default='120.0', nullable=False),
        sa.Column('ease', sa.Float(), server_default='3.0', nullable=False),
        sa.Column('ice_score', sa.Float(), server_default='7.2', nullable=False),
        sa.Column('moscow_category', sa.String(length=32), server_default='SHOULD_HAVE', nullable=False),
        sa.Column('weighted_score', sa.Float(), server_default='75.0', nullable=False),
        sa.Column('priority_rank', sa.Integer(), server_default='1', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('evaluated_by_id', sa.Integer(), nullable=True),
        sa.Column('evaluated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['evaluated_by_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_product_prioritization_items_item_id', 'product_prioritization_items', ['item_id'])

    # 17. Product Initiatives
    op.create_table(
        'product_initiatives',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('strategic_objective', sa.String(length=255), nullable=False),
        sa.Column('priority', sa.String(length=32), server_default='HIGH', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='IN_PROGRESS', nullable=False),
        sa.Column('progress_pct', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('target_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_product_initiatives_status', 'product_initiatives', ['status'])

    # 18. Lifecycle Roadmap Items
    op.create_table(
        'lifecycle_roadmap_items',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('initiative_id', sa.String(length=64), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('product_area', sa.String(length=64), server_default='CORE_PLATFORM', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='PLANNED', nullable=False),
        sa.Column('priority', sa.String(length=32), server_default='MEDIUM', nullable=False),
        sa.Column('quarter', sa.String(length=16), server_default='Q1-2027', nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('target_date', sa.DateTime(), nullable=True),
        sa.Column('progress_pct', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['initiative_id'], ['product_initiatives.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_lifecycle_roadmap_items_status', 'lifecycle_roadmap_items', ['status'])

    # 19. Roadmap Dependencies
    op.create_table(
        'roadmap_dependencies',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('roadmap_item_id', sa.String(length=64), nullable=False),
        sa.Column('depends_on_item_id', sa.String(length=64), nullable=False),
        sa.Column('dependency_type', sa.String(length=32), server_default='BLOCKS', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='ACTIVE', nullable=False),
        sa.Column('risk_level', sa.String(length=32), server_default='MEDIUM', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['roadmap_item_id'], ['lifecycle_roadmap_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['depends_on_item_id'], ['lifecycle_roadmap_items.id'], ondelete='CASCADE'),
    )

    # 20. Product Validations
    op.create_table(
        'product_validations',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('discovery_id', sa.String(length=64), nullable=False),
        sa.Column('hypothesis', sa.Text(), nullable=False),
        sa.Column('method', sa.String(length=64), server_default='INTERVIEW', nullable=False),
        sa.Column('sample_size', sa.Integer(), server_default='10', nullable=False),
        sa.Column('results_summary', sa.Text(), nullable=False),
        sa.Column('outcome', sa.String(length=32), server_default='VALIDATED', nullable=False),
        sa.Column('confidence_pct', sa.Float(), server_default='85.0', nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.Column('validated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['discovery_id'], ['product_discoveries.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='SET NULL'),
    )

    # 21. Product Experiments
    op.create_table(
        'product_experiments',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('hypothesis', sa.Text(), nullable=False),
        sa.Column('experiment_type', sa.String(length=32), server_default='AB_TEST', nullable=False),
        sa.Column('primary_metric', sa.String(length=128), server_default='conversion_rate', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='RUNNING', nullable=False),
        sa.Column('audience_segment', sa.String(length=64), server_default='ALL_USERS', nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('total_sample_size', sa.Integer(), server_default='0', nullable=False),
        sa.Column('conclusion', sa.Text(), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_product_experiments_status', 'product_experiments', ['status'])

    # 22. Experiment Variants
    op.create_table(
        'experiment_variants',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('experiment_id', sa.String(length=64), nullable=False),
        sa.Column('variant_name', sa.String(length=128), nullable=False),
        sa.Column('variant_key', sa.String(length=32), nullable=False),
        sa.Column('allocation_pct', sa.Float(), server_default='50.0', nullable=False),
        sa.Column('config_json', sa.Text(), server_default='{}', nullable=False),
        sa.Column('impression_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('conversion_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('conversion_rate', sa.Float(), server_default='0.0', nullable=False),
        sa.ForeignKeyConstraint(['experiment_id'], ['product_experiments.id'], ondelete='CASCADE'),
    )

    # 23. Experiment Assignments
    op.create_table(
        'experiment_assignments',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('experiment_id', sa.String(length=64), nullable=False),
        sa.Column('variant_id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), nullable=False),
        sa.Column('context_json', sa.Text(), server_default='{}', nullable=False),
        sa.ForeignKeyConstraint(['experiment_id'], ['product_experiments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variant_id'], ['experiment_variants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # 24. Experiment Events
    op.create_table(
        'experiment_events',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('experiment_id', sa.String(length=64), nullable=False),
        sa.Column('variant_id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('event_name', sa.String(length=128), nullable=False),
        sa.Column('metric_value', sa.Float(), server_default='1.0', nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['experiment_id'], ['product_experiments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variant_id'], ['experiment_variants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # 25. Product Releases
    op.create_table(
        'product_releases',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('release_version', sa.String(length=32), unique=True, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='PLANNED', nullable=False),
        sa.Column('release_date', sa.DateTime(), nullable=True),
        sa.Column('rollout_percentage', sa.Float(), server_default='100.0', nullable=False),
        sa.Column('release_notes', sa.Text(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_product_releases_release_version', 'product_releases', ['release_version'])
    op.create_index('ix_product_releases_status', 'product_releases', ['status'])

    # 26. Product Retrospectives
    op.create_table(
        'product_retrospectives',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('release_id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('objective', sa.Text(), nullable=False),
        sa.Column('expected_vs_actual', sa.Text(), nullable=False),
        sa.Column('customer_impact_summary', sa.Text(), nullable=False),
        sa.Column('lessons_learned', sa.Text(), nullable=False),
        sa.Column('action_items_json', sa.Text(), server_default='[]', nullable=False),
        sa.Column('conductor_id', sa.Integer(), nullable=True),
        sa.Column('held_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['release_id'], ['product_releases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['conductor_id'], ['users.id'], ondelete='SET NULL'),
    )

    # 27. Product Event Records
    op.create_table(
        'product_event_records',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('event_name', sa.String(length=128), nullable=False),
        sa.Column('event_category', sa.String(length=64), server_default='USAGE', nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('workspace_id', sa.Integer(), nullable=True),
        sa.Column('product_area', sa.String(length=64), server_default='CORE_PLATFORM', nullable=False),
        sa.Column('metadata_json', sa.Text(), server_default='{}', nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_product_event_records_event_name', 'product_event_records', ['event_name'])
    op.create_index('ix_product_event_records_event_category', 'product_event_records', ['event_category'])
    op.create_index('ix_product_event_records_timestamp', 'product_event_records', ['timestamp'])

    # 28. Product Decisions
    op.create_table(
        'product_decisions',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('problem', sa.Text(), nullable=False),
        sa.Column('decision_summary', sa.Text(), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('alternatives_considered', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=32), server_default='APPROVED', nullable=False),
        sa.Column('decision_maker_id', sa.Integer(), nullable=True),
        sa.Column('decision_date', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['decision_maker_id'], ['users.id'], ondelete='SET NULL'),
    )

    # 29. Product Risk Records
    op.create_table(
        'product_risk_records',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=64), server_default='TECHNICAL', nullable=False),
        sa.Column('severity', sa.String(length=32), server_default='MEDIUM', nullable=False),
        sa.Column('likelihood', sa.String(length=32), server_default='MEDIUM', nullable=False),
        sa.Column('mitigation_plan', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='IDENTIFIED', nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_product_risk_records_status', 'product_risk_records', ['status'])

def downgrade() -> None:
    # Phase 45
    op.drop_table('product_risk_records')
    op.drop_table('product_decisions')
    op.drop_table('product_event_records')
    op.drop_table('product_retrospectives')
    op.drop_table('product_releases')
    op.drop_table('experiment_events')
    op.drop_table('experiment_assignments')
    op.drop_table('experiment_variants')
    op.drop_table('product_experiments')
    op.drop_table('product_validations')
    op.drop_table('roadmap_dependencies')
    op.drop_table('lifecycle_roadmap_items')
    op.drop_table('product_initiatives')
    op.drop_table('product_prioritization_items')
    op.drop_table('product_opportunities')
    op.drop_table('product_feature_requests')
    op.drop_table('product_ideas')
    op.drop_table('product_discoveries')

    # Phase 43
    op.drop_table('security_remediations')
    op.drop_table('security_posture_findings')
    op.drop_table('security_posture_assessments')
    op.drop_table('vulnerability_records')
    op.drop_table('access_review_records')
    op.drop_table('access_review_campaigns')
    op.drop_table('identity_risk_records')
    op.drop_table('security_alerts')
    op.drop_table('security_detection_results')
    op.drop_table('security_detection_rules')
    op.drop_table('security_events')
