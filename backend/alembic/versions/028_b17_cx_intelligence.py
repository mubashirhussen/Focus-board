"""B17: Customer Experience Intelligence, Feedback Management, Surveys, Sentiment Analysis, Insights

Revision ID: 028_b17_cx_intelligence
Revises: 027_b16_integrations_sync_and_mappings
Create Date: 2026-11-23 09:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '028_b17_cx_intelligence'
down_revision = '027_b16_integrations_sync_and_mappings'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # 1. Update customer_feedbacks table with new enterprise CX fields using batch_alter_table for SQLite compatibility
    if 'customer_feedbacks' in existing_tables:
        existing_cols = {col['name'] for col in inspector.get_columns('customer_feedbacks')}
        new_columns = [
            ('title', sa.Column('title', sa.String(length=255), nullable=True)),
            ('organization_id', sa.Column('organization_id', sa.Integer(), nullable=True)),
            ('project_id', sa.Column('project_id', sa.Integer(), nullable=True)),
            ('source', sa.Column('source', sa.String(length=50), server_default='IN_APP', nullable=False)),
            ('feedback_type', sa.Column('feedback_type', sa.String(length=50), server_default='GENERAL', nullable=False)),
            ('sentiment', sa.Column('sentiment', sa.String(length=32), server_default='NEUTRAL', nullable=False)),
            ('sentiment_score', sa.Column('sentiment_score', sa.Float(), server_default='0.0', nullable=False)),
            ('sentiment_confidence', sa.Column('sentiment_confidence', sa.Float(), server_default='0.5', nullable=False)),
            ('priority', sa.Column('priority', sa.String(length=20), server_default='MEDIUM', nullable=False)),
            ('priority_score', sa.Column('priority_score', sa.Float(), server_default='50.0', nullable=False)),
            ('assigned_user_id', sa.Column('assigned_user_id', sa.Integer(), nullable=True)),
            ('tags_json', sa.Column('tags_json', sa.Text(), server_default='[]', nullable=False)),
            ('resolution_notes', sa.Column('resolution_notes', sa.Text(), nullable=True)),
            ('resolved_at', sa.Column('resolved_at', sa.DateTime(), nullable=True)),
            ('metadata_json', sa.Column('metadata_json', sa.Text(), server_default='{}', nullable=False)),
            ('language', sa.Column('language', sa.String(length=10), server_default='en', nullable=False)),
        ]
        with op.batch_alter_table('customer_feedbacks') as batch_op:
            for col_name, col_obj in new_columns:
                if col_name not in existing_cols:
                    batch_op.add_column(col_obj)

    # 2. cx_feedback_categories table
    if 'cx_feedback_categories' not in existing_tables:
        op.create_table(
            'cx_feedback_categories',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('slug', sa.String(length=100), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('parent_id', sa.Integer(), sa.ForeignKey('cx_feedback_categories.id', ondelete='SET NULL'), nullable=True),
            sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )

    # 3. cx_surveys table
    if 'cx_surveys' not in existing_tables:
        op.create_table(
            'cx_surveys',
            sa.Column('id', sa.String(length=64), primary_key=True),
            sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('survey_type', sa.String(length=50), server_default='CSAT', nullable=False),
            sa.Column('status', sa.String(length=30), server_default='ACTIVE', nullable=False),
            sa.Column('target_audience', sa.String(length=50), server_default='ALL', nullable=False),
            sa.Column('trigger_event', sa.String(length=100), nullable=True),
            sa.Column('settings_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )

    # 4. cx_survey_questions table
    if 'cx_survey_questions' not in existing_tables:
        op.create_table(
            'cx_survey_questions',
            sa.Column('id', sa.String(length=64), primary_key=True),
            sa.Column('survey_id', sa.String(length=64), sa.ForeignKey('cx_surveys.id', ondelete='CASCADE'), nullable=False),
            sa.Column('question_text', sa.Text(), nullable=False),
            sa.Column('question_type', sa.String(length=32), server_default='RATING_5', nullable=False),
            sa.Column('options_json', sa.Text(), server_default='[]', nullable=False),
            sa.Column('is_required', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('order_index', sa.Integer(), server_default='0', nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )

    # 5. cx_survey_responses table
    if 'cx_survey_responses' not in existing_tables:
        op.create_table(
            'cx_survey_responses',
            sa.Column('id', sa.String(length=64), primary_key=True),
            sa.Column('survey_id', sa.String(length=64), sa.ForeignKey('cx_surveys.id', ondelete='CASCADE'), nullable=False),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('respondent_reference', sa.String(length=100), nullable=True),
            sa.Column('score', sa.Float(), nullable=True),
            sa.Column('feedback_text', sa.Text(), nullable=True),
            sa.Column('answers_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('sentiment', sa.String(length=32), server_default='NEUTRAL', nullable=False),
            sa.Column('sentiment_score', sa.Float(), server_default='0.0', nullable=False),
            sa.Column('submitted_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )

    # 6. cx_insights table
    if 'cx_insights' not in existing_tables:
        op.create_table(
            'cx_insights',
            sa.Column('id', sa.String(length=64), primary_key=True),
            sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('insight_type', sa.String(length=50), server_default='TREND', nullable=False),
            sa.Column('severity', sa.String(length=20), server_default='MEDIUM', nullable=False),
            sa.Column('priority', sa.String(length=20), server_default='MEDIUM', nullable=False),
            sa.Column('confidence', sa.Float(), server_default='0.85', nullable=False),
            sa.Column('supporting_metrics_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('supporting_feedback_ids_json', sa.Text(), server_default='[]', nullable=False),
            sa.Column('recommended_action', sa.Text(), nullable=True),
            sa.Column('status', sa.String(length=30), server_default='ACTIVE', nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )

    # 7. cx_recommendations table
    if 'cx_recommendations' not in existing_tables:
        op.create_table(
            'cx_recommendations',
            sa.Column('id', sa.String(length=64), primary_key=True),
            sa.Column('insight_id', sa.String(length=64), sa.ForeignKey('cx_insights.id', ondelete='SET NULL'), nullable=True),
            sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('action_type', sa.String(length=50), server_default='TASK', nullable=False),
            sa.Column('status', sa.String(length=30), server_default='PENDING', nullable=False),
            sa.Column('task_id', sa.String(length=64), sa.ForeignKey('tasks.id', ondelete='SET NULL'), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('converted_at', sa.DateTime(), nullable=True),
        )

    # 8. cx_journey_events table
    if 'cx_journey_events' not in existing_tables:
        op.create_table(
            'cx_journey_events',
            sa.Column('id', sa.String(length=64), primary_key=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True),
            sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True),
            sa.Column('stage', sa.String(length=50), nullable=False),
            sa.Column('event_name', sa.String(length=100), nullable=False),
            sa.Column('sentiment', sa.String(length=32), server_default='NEUTRAL', nullable=False),
            sa.Column('metadata_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )

def downgrade() -> None:
    op.drop_table('cx_journey_events')
    op.drop_table('cx_recommendations')
    op.drop_table('cx_insights')
    op.drop_table('cx_survey_responses')
    op.drop_table('cx_survey_questions')
    op.drop_table('cx_surveys')
    op.drop_table('cx_feedback_categories')
