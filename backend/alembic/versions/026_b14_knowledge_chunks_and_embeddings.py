"""B14: Knowledge Intelligence, Document Chunks, Embeddings & Links

Revision ID: 026_b14_knowledge_chunks_and_embeddings
Revises: 025_b13_ai_conversations_messages_and_usage
Create Date: 2026-11-22 23:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '026_b14_knowledge_chunks_and_embeddings'
down_revision = '025_b13_ai_conversations_messages_and_usage'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # 1. Update knowledge_documents with file upload and processing metadata columns
    if 'knowledge_documents' in existing_tables:
        existing_cols = {col['name'] for col in inspector.get_columns('knowledge_documents')}
        if 'original_filename' not in existing_cols:
            op.add_column('knowledge_documents', sa.Column('original_filename', sa.String(length=255), nullable=True))
        if 'file_size' not in existing_cols:
            op.add_column('knowledge_documents', sa.Column('file_size', sa.Integer(), server_default='0', nullable=False))
        if 'mime_type' not in existing_cols:
            op.add_column('knowledge_documents', sa.Column('mime_type', sa.String(length=128), nullable=True))
        if 'storage_path' not in existing_cols:
            op.add_column('knowledge_documents', sa.Column('storage_path', sa.String(length=512), nullable=True))
        if 'processing_status' not in existing_cols:
            op.add_column('knowledge_documents', sa.Column('processing_status', sa.String(length=32), server_default='COMPLETED', nullable=False))
        if 'summary' not in existing_cols:
            op.add_column('knowledge_documents', sa.Column('summary', sa.Text(), nullable=True))

    # 2. Knowledge Document Chunks
    if 'knowledge_document_chunks' not in existing_tables:
        op.create_table(
            'knowledge_document_chunks',
            sa.Column('id', sa.String(length=64), primary_key=True),
            sa.Column('document_id', sa.String(length=64), sa.ForeignKey('knowledge_documents.id', ondelete='CASCADE'), nullable=False),
            sa.Column('chunk_index', sa.Integer(), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('heading', sa.String(length=255), nullable=True),
            sa.Column('page_number', sa.Integer(), nullable=True),
            sa.Column('token_count', sa.Integer(), server_default='0', nullable=False),
            sa.Column('embedding_json', sa.Text(), nullable=True),
            sa.Column('metadata_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_knowledge_document_chunks_doc_id', 'knowledge_document_chunks', ['document_id'])
        op.create_index('ix_knowledge_document_chunks_chunk_index', 'knowledge_document_chunks', ['chunk_index'])

    # 3. Knowledge Document Links (to Tasks, Projects, etc.)
    if 'knowledge_document_links' not in existing_tables:
        op.create_table(
            'knowledge_document_links',
            sa.Column('id', sa.String(length=64), primary_key=True),
            sa.Column('document_id', sa.String(length=64), sa.ForeignKey('knowledge_documents.id', ondelete='CASCADE'), nullable=False),
            sa.Column('entity_type', sa.String(length=32), nullable=False),
            sa.Column('entity_id', sa.String(length=64), nullable=False),
            sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_kdoc_links_doc_id', 'knowledge_document_links', ['document_id'])
        op.create_index('ix_kdoc_links_entity', 'knowledge_document_links', ['entity_type', 'entity_id'])

def downgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    if 'knowledge_document_links' in existing_tables:
        op.drop_table('knowledge_document_links')
    if 'knowledge_document_chunks' in existing_tables:
        op.drop_table('knowledge_document_chunks')
