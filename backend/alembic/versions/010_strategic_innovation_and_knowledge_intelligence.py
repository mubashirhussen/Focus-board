"""Add strategic intelligence, innovation lab, and knowledge intelligence tables

Revision ID: 010_strategic_innovation_and_knowledge_intelligence
Revises: 009_security_compliance_and_financial_intelligence
Create Date: 2026-11-22 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '010_strategic_innovation_and_knowledge_intelligence'
down_revision = '009_security_compliance_and_financial_intelligence'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # --- PHASE 36: STRATEGIC INTELLIGENCE ---
    # 1. Strategic Plans
    op.create_table(
        'strategic_plans',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('organization_id', sa.String(length=64), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('vision', sa.Text(), nullable=False),
        sa.Column('mission', sa.Text(), nullable=False),
        sa.Column('strategic_themes_json', sa.Text(), server_default='[]', nullable=False),
        sa.Column('time_horizon', sa.String(length=32), server_default='ANNUAL', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='ACTIVE', nullable=False),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_strategic_plans_org', 'strategic_plans', ['organization_id'])
    op.create_index('ix_strategic_plans_status', 'strategic_plans', ['status'])

    # 2. Strategic Goals
    op.create_table(
        'strategic_goals',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('plan_id', sa.String(length=64), sa.ForeignKey('strategic_plans.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('target_metric', sa.String(length=128), nullable=False),
        sa.Column('baseline_value', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('target_value', sa.Float(), nullable=False),
        sa.Column('current_value', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('unit', sa.String(length=32), server_default='$', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='ACTIVE', nullable=False),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deadline', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_strategic_goals_plan_id', 'strategic_goals', ['plan_id'])
    op.create_index('ix_strategic_goals_status', 'strategic_goals', ['status'])

    # 3. Strategic Initiatives
    op.create_table(
        'strategic_initiatives',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('goal_id', sa.String(length=64), sa.ForeignKey('strategic_goals.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('priority', sa.String(length=32), server_default='P2_HIGH', nullable=False),
        sa.Column('budget_amount', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='IN_PROGRESS', nullable=False),
        sa.Column('progress_percentage', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_strategic_initiatives_goal_id', 'strategic_initiatives', ['goal_id'])

    # 4. Market Intelligence
    op.create_table(
        'market_intelligences',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('intelligence_type', sa.String(length=64), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('source_name', sa.String(length=255), nullable=False),
        sa.Column('source_url', sa.String(length=512), nullable=True),
        sa.Column('confidence_score', sa.Float(), server_default='0.9', nullable=False),
        sa.Column('impact_rating', sa.String(length=32), server_default='HIGH', nullable=False),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_market_intelligences_type', 'market_intelligences', ['intelligence_type'])

    # 5. Market Signals
    op.create_table(
        'market_signals',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('signal_type', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('observations', sa.Text(), nullable=False),
        sa.Column('trend_direction', sa.String(length=32), server_default='ACCELERATING', nullable=False),
        sa.Column('urgency', sa.String(length=32), server_default='NEAR_TERM', nullable=False),
        sa.Column('is_converted_to_opportunity', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_market_signals_type', 'market_signals', ['signal_type'])

    # 6. Competitors
    op.create_table(
        'competitors',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('name', sa.String(length=255), unique=True, nullable=False),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('market_position', sa.String(length=64), server_default='CHALLENGER', nullable=False),
        sa.Column('pricing_model', sa.String(length=64), server_default='PER_SEAT', nullable=False),
        sa.Column('strengths_json', sa.Text(), server_default='[]', nullable=False),
        sa.Column('weaknesses_json', sa.Text(), server_default='[]', nullable=False),
        sa.Column('features_diff_json', sa.Text(), server_default='{}', nullable=False),
        sa.Column('threat_level', sa.String(length=32), server_default='MEDIUM', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_competitors_name', 'competitors', ['name'])

    # 7. SWOT Entries
    op.create_table(
        'swot_entries',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('swot_type', sa.String(length=32), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('impact', sa.String(length=32), server_default='HIGH', nullable=False),
        sa.Column('evidence_text', sa.Text(), nullable=True),
        sa.Column('is_ai_generated', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_swot_entries_type', 'swot_entries', ['swot_type'])

    # 8. Market Sizing
    op.create_table(
        'market_sizings',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('market_name', sa.String(length=255), nullable=False),
        sa.Column('methodology', sa.String(length=64), server_default='BOTTOM_UP', nullable=False),
        sa.Column('tam_cents', sa.Integer(), nullable=False),
        sa.Column('sam_cents', sa.Integer(), nullable=False),
        sa.Column('som_cents', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=8), server_default='USD', nullable=False),
        sa.Column('assumptions_json', sa.Text(), server_default='{}', nullable=False),
        sa.Column('confidence_score', sa.Float(), server_default='0.85', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # 9. Strategic Opportunities
    op.create_table(
        'strategic_opportunities',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('customer_segment', sa.String(length=128), server_default='Enterprise B2B', nullable=False),
        sa.Column('estimated_value_cents', sa.Integer(), server_default='0', nullable=False),
        sa.Column('feasibility_score', sa.Float(), server_default='8.0', nullable=False),
        sa.Column('rice_reach', sa.Float(), server_default='1000.0', nullable=False),
        sa.Column('rice_impact', sa.Float(), server_default='3.0', nullable=False),
        sa.Column('rice_confidence', sa.Float(), server_default='0.8', nullable=False),
        sa.Column('rice_effort', sa.Float(), server_default='2.0', nullable=False),
        sa.Column('rice_score', sa.Float(), server_default='1200.0', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='EVALUATING', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_strategic_opportunities_status', 'strategic_opportunities', ['status'])

    # 10. Strategic Scenarios
    op.create_table(
        'strategic_scenarios',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('scenario_type', sa.String(length=32), server_default='BASE_CASE', nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('revenue_multiplier', sa.Float(), server_default='1.0', nullable=False),
        sa.Column('churn_rate_impact', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('assumptions_json', sa.Text(), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # 11. Strategic Decisions
    op.create_table(
        'strategic_decisions',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('context', sa.Text(), nullable=False),
        sa.Column('decision_outcome', sa.Text(), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('decision_maker_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('decision_date', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='APPROVED', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # --- PHASE 37: INNOVATION LAB ---
    # 12. Innovation Ideas
    op.create_table(
        'innovation_ideas',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('problem_statement', sa.Text(), nullable=False),
        sa.Column('proposed_solution', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=64), server_default='PRODUCT', nullable=False),
        sa.Column('stage', sa.String(length=32), server_default='CAPTURE', nullable=False),
        sa.Column('target_audience', sa.String(length=128), server_default='Enterprise Teams', nullable=False),
        sa.Column('estimated_effort', sa.String(length=32), server_default='MEDIUM', nullable=False),
        sa.Column('strategic_value', sa.String(length=32), server_default='SUBSTANTIAL', nullable=False),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('roadmap_item_id', sa.Integer(), sa.ForeignKey('product_roadmap_items.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_innovation_ideas_stage', 'innovation_ideas', ['stage'])
    op.create_index('ix_innovation_ideas_category', 'innovation_ideas', ['category'])

    # 13. Innovation Hypotheses
    op.create_table(
        'innovation_hypotheses',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('idea_id', sa.String(length=64), sa.ForeignKey('innovation_ideas.id', ondelete='CASCADE'), nullable=False),
        sa.Column('statement', sa.Text(), nullable=False),
        sa.Column('measurable_criterion', sa.String(length=255), nullable=False),
        sa.Column('confidence_score', sa.Float(), server_default='0.8', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='UNTESTED', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_innovation_hypotheses_idea_id', 'innovation_hypotheses', ['idea_id'])

    # 14. Innovation Experiments
    op.create_table(
        'innovation_experiments',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('idea_id', sa.String(length=64), sa.ForeignKey('innovation_ideas.id', ondelete='CASCADE'), nullable=False),
        sa.Column('hypothesis_id', sa.String(length=64), sa.ForeignKey('innovation_hypotheses.id', ondelete='SET NULL'), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('experiment_type', sa.String(length=64), server_default='CUSTOMER_INTERVIEW', nullable=False),
        sa.Column('methodology', sa.Text(), nullable=False),
        sa.Column('sample_size', sa.Integer(), server_default='25', nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=32), server_default='RUNNING', nullable=False),
        sa.Column('budget_spent', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_innovation_experiments_idea_id', 'innovation_experiments', ['idea_id'])

    # 15. Innovation Experiment Results
    op.create_table(
        'innovation_experiment_results',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('experiment_id', sa.String(length=64), sa.ForeignKey('innovation_experiments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('quantitative_summary', sa.Text(), nullable=False),
        sa.Column('qualitative_feedback', sa.Text(), nullable=False),
        sa.Column('success_criteria_met', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('evidence_attachment_url', sa.String(length=512), nullable=True),
        sa.Column('lessons_learned', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # 16. Innovation Prototypes
    op.create_table(
        'innovation_prototypes',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('idea_id', sa.String(length=64), sa.ForeignKey('innovation_ideas.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('prototype_type', sa.String(length=64), server_default='INTERACTIVE_MOCKUP', nullable=False),
        sa.Column('demo_url', sa.String(length=512), nullable=True),
        sa.Column('repository_url', sa.String(length=512), nullable=True),
        sa.Column('tech_stack', sa.String(length=255), server_default='React + FastAPI', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='BUILDING', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # 17. Innovation Validations
    op.create_table(
        'innovation_validations',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('idea_id', sa.String(length=64), sa.ForeignKey('innovation_ideas.id', ondelete='CASCADE'), nullable=False),
        sa.Column('dimension', sa.String(length=64), nullable=False),
        sa.Column('criteria', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='PASSED', nullable=False),
        sa.Column('reviewer_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('confidence', sa.Float(), server_default='0.9', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # 18. Innovation Portfolios
    op.create_table(
        'innovation_portfolios',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('focus_area', sa.String(length=128), nullable=False),
        sa.Column('budget_limit', sa.Float(), server_default='50000.0', nullable=False),
        sa.Column('allocated_spend', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('active_ideas_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # --- PHASE 38: KNOWLEDGE INTELLIGENCE ---
    # 19. Knowledge Documents
    op.create_table(
        'knowledge_documents',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), unique=True, nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('document_type', sa.String(length=64), server_default='SPECIFICATION', nullable=False),
        sa.Column('category', sa.String(length=64), server_default='Engineering', nullable=False),
        sa.Column('visibility', sa.String(length=32), server_default='INTERNAL', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='VERIFIED', nullable=False),
        sa.Column('version', sa.String(length=16), server_default='1.0', nullable=False),
        sa.Column('author_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('quality_score', sa.Float(), server_default='92.0', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_knowledge_documents_slug', 'knowledge_documents', ['slug'])
    op.create_index('ix_knowledge_documents_type', 'knowledge_documents', ['document_type'])

    # 20. Knowledge Document Versions
    op.create_table(
        'knowledge_document_versions',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('document_id', sa.String(length=64), sa.ForeignKey('knowledge_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.String(length=16), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('change_summary', sa.String(length=255), server_default='Refinement', nullable=False),
        sa.Column('editor_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_knowledge_document_versions_doc_id', 'knowledge_document_versions', ['document_id'])

    # 21. Knowledge Collections
    op.create_table(
        'knowledge_collections',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='SET NULL'), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('icon', sa.String(length=64), server_default='BookOpen', nullable=False),
        sa.Column('is_cross_workspace', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # 22. Knowledge Entities
    op.create_table(
        'knowledge_entities',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('entity_type', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('canonical_id', sa.String(length=128), nullable=True),
        sa.Column('metadata_json', sa.Text(), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_knowledge_entities_type', 'knowledge_entities', ['entity_type'])
    op.create_index('ix_knowledge_entities_name', 'knowledge_entities', ['name'])

    # 23. Knowledge Relationships
    op.create_table(
        'knowledge_relationships',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('source_entity_id', sa.String(length=64), sa.ForeignKey('knowledge_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_entity_id', sa.String(length=64), sa.ForeignKey('knowledge_entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('relation_type', sa.String(length=64), nullable=False),
        sa.Column('confidence', sa.Float(), server_default='1.0', nullable=False),
        sa.Column('provenance', sa.String(length=64), server_default='EXPLICIT_LINK', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_knowledge_relationships_source', 'knowledge_relationships', ['source_entity_id'])
    op.create_index('ix_knowledge_relationships_target', 'knowledge_relationships', ['target_entity_id'])

    # 24. Organizational Memories
    op.create_table(
        'organizational_memories',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('memory_type', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), server_default='0.95', nullable=False),
        sa.Column('source_reference', sa.String(length=255), nullable=True),
        sa.Column('is_verified', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_organizational_memories_type', 'organizational_memories', ['memory_type'])

    # 25. Knowledge Gaps
    op.create_table(
        'knowledge_gaps',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('gap_type', sa.String(length=64), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=32), server_default='MEDIUM', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='OPEN', nullable=False),
        sa.Column('suggested_action', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

def downgrade() -> None:
    pass
