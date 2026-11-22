"""Add organization_id tenant scoping to all product lifecycle intelligence tables

Revision ID: 014_product_lifecycle_hardening
Revises: 013_security_intelligence_and_product_lifecycle
Create Date: 2026-11-22 17:55:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '014_product_lifecycle_hardening'
down_revision = '013_security_intelligence_and_product_lifecycle'
branch_labels = None
depends_on = None

TABLES_TO_UPDATE = [
    'product_ideas',
    'product_feature_requests',
    'product_opportunities',
    'product_prioritization_items',
    'product_initiatives',
    'lifecycle_roadmap_items',
    'product_experiments',
    'product_releases',
    'product_decisions',
    'product_risk_records',
    'product_validations',
]

def upgrade() -> None:
    for table_name in TABLES_TO_UPDATE:
        with op.batch_alter_table(table_name, schema=None) as batch_op:
            batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
            batch_op.create_index(f'ix_{table_name}_organization_id', ['organization_id'])

def downgrade() -> None:
    for table_name in TABLES_TO_UPDATE:
        with op.batch_alter_table(table_name, schema=None) as batch_op:
            batch_op.drop_index(f'ix_{table_name}_organization_id')
            batch_op.drop_column('organization_id')
