"""add_user_library_progress_history_tables

Revision ID: c11248c9342e
Revises: 1ac8923e9648
Create Date: 2026-01-08 07:01:41.124925

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c11248c9342e'
down_revision: Union[str, None] = '1ac8923e9648'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_library_items table
    op.create_table(
        'user_library_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('title_id', sa.String(), nullable=False),
        sa.Column('status', sa.Enum('WATCHING', 'PLANNED', 'COMPLETED', 'DROPPED', name='librarystatus'), nullable=False),
        sa.Column('is_favorite', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_library_items_id'), 'user_library_items', ['id'], unique=False)
    op.create_index(op.f('ix_user_library_items_user_id'), 'user_library_items', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_library_items_provider'), 'user_library_items', ['provider'], unique=False)
    op.create_index(op.f('ix_user_library_items_title_id'), 'user_library_items', ['title_id'], unique=False)
    # Add unique constraint for user + provider + title
    op.create_unique_constraint('uq_user_library_provider_title', 'user_library_items', ['user_id', 'provider', 'title_id'])
    
    # Create user_progress table
    op.create_table(
        'user_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('title_id', sa.String(), nullable=False),
        sa.Column('episode_id', sa.String(), nullable=False),
        sa.Column('position_seconds', sa.Float(), nullable=False),
        sa.Column('duration_seconds', sa.Float(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_progress_id'), 'user_progress', ['id'], unique=False)
    op.create_index(op.f('ix_user_progress_user_id'), 'user_progress', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_progress_provider'), 'user_progress', ['provider'], unique=False)
    op.create_index(op.f('ix_user_progress_title_id'), 'user_progress', ['title_id'], unique=False)
    op.create_index(op.f('ix_user_progress_episode_id'), 'user_progress', ['episode_id'], unique=False)
    op.create_index(op.f('ix_user_progress_updated_at'), 'user_progress', ['updated_at'], unique=False)
    # Add unique constraint for user + provider + episode
    op.create_unique_constraint('uq_user_progress_provider_episode', 'user_progress', ['user_id', 'provider', 'episode_id'])
    
    # Create user_history table
    op.create_table(
        'user_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('title_id', sa.String(), nullable=False),
        sa.Column('episode_id', sa.String(), nullable=False),
        sa.Column('position_seconds', sa.Float(), nullable=True),
        sa.Column('watched_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_history_id'), 'user_history', ['id'], unique=False)
    op.create_index(op.f('ix_user_history_user_id'), 'user_history', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_history_provider'), 'user_history', ['provider'], unique=False)
    op.create_index(op.f('ix_user_history_title_id'), 'user_history', ['title_id'], unique=False)
    op.create_index(op.f('ix_user_history_episode_id'), 'user_history', ['episode_id'], unique=False)
    op.create_index(op.f('ix_user_history_watched_at'), 'user_history', ['watched_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_history_watched_at'), table_name='user_history')
    op.drop_index(op.f('ix_user_history_episode_id'), table_name='user_history')
    op.drop_index(op.f('ix_user_history_title_id'), table_name='user_history')
    op.drop_index(op.f('ix_user_history_provider'), table_name='user_history')
    op.drop_index(op.f('ix_user_history_user_id'), table_name='user_history')
    op.drop_index(op.f('ix_user_history_id'), table_name='user_history')
    op.drop_table('user_history')
    
    op.drop_index(op.f('ix_user_progress_updated_at'), table_name='user_progress')
    op.drop_index(op.f('ix_user_progress_episode_id'), table_name='user_progress')
    op.drop_index(op.f('ix_user_progress_title_id'), table_name='user_progress')
    op.drop_index(op.f('ix_user_progress_provider'), table_name='user_progress')
    op.drop_index(op.f('ix_user_progress_user_id'), table_name='user_progress')
    op.drop_index(op.f('ix_user_progress_id'), table_name='user_progress')
    op.drop_constraint('uq_user_progress_provider_episode', 'user_progress', type_='unique')
    op.drop_table('user_progress')
    
    op.drop_index(op.f('ix_user_library_items_title_id'), table_name='user_library_items')
    op.drop_index(op.f('ix_user_library_items_provider'), table_name='user_library_items')
    op.drop_index(op.f('ix_user_library_items_user_id'), table_name='user_library_items')
    op.drop_index(op.f('ix_user_library_items_id'), table_name='user_library_items')
    op.drop_constraint('uq_user_library_provider_title', 'user_library_items', type_='unique')
    op.drop_table('user_library_items')
    
    # Drop enum type
    sa.Enum(name='librarystatus').drop(op.get_bind(), checkfirst=True)
