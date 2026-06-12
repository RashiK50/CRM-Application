"""initial_schema

Revision ID: 001
Revises: 
Create Date: 2026-06-12 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # 1. Create Threads Table
    op.create_table('threads',
        sa.Column('thread_id', sa.String(), nullable=False),
        sa.Column('subject', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('assigned_to', sa.String(), nullable=True),
        sa.Column('last_updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('thread_id')
    )
    
    # 2. Create Emails Table
    op.create_table('emails',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.String(), nullable=True),
        sa.Column('thread_id', sa.String(), nullable=True),
        sa.Column('sender', sa.String(), nullable=True),
        sa.Column('subject', sa.String(), nullable=True),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('urgency', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('requires_human', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['thread_id'], ['threads.thread_id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. Create Actions Table (with JSON field)
    op.create_table('actions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email_id', sa.Integer(), nullable=True),
        sa.Column('agent_reasoning_log', sa.JSON(), nullable=True),
        sa.Column('action_type', sa.String(), nullable=True),
        sa.Column('proposed_content', sa.Text(), nullable=True),
        sa.Column('executed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['email_id'], ['emails.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('actions')
    op.drop_table('emails')
    op.drop_table('threads')