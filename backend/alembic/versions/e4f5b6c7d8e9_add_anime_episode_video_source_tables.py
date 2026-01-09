"""add_anime_episode_video_source_tables

Revision ID: e4f5b6c7d8e9
Revises: cd5d2fb44aad
Create Date: 2026-01-08 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e4f5b6c7d8e9'
down_revision = 'cd5d2fb44aad'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create anime status enum only if it does not exist (idempotent)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'animestatus') THEN
                CREATE TYPE animestatus AS ENUM ('ongoing', 'completed', 'upcoming');
            END IF;
        END
        $$;
        """
    )
    anime_status_enum = postgresql.ENUM(
        'ongoing', 'completed', 'upcoming',
        name='animestatus',
        create_type=False,
    )
    
    # Create anime table
    op.create_table('anime',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('status', anime_status_enum, nullable=True),
        sa.Column('poster', sa.String(), nullable=True),
        sa.Column('source_name', sa.String(), nullable=False),
        sa.Column('source_id', sa.String(), nullable=False),
        sa.Column('genres', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('alternative_titles', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_name', 'source_id', name='uq_anime_source'),
    )
    op.create_index(op.f('ix_anime_id'), 'anime', ['id'], unique=False)
    op.create_index(op.f('ix_anime_is_active'), 'anime', ['is_active'], unique=False)
    op.create_index(op.f('ix_anime_slug'), 'anime', ['slug'], unique=True)
    op.create_index(op.f('ix_anime_source_id'), 'anime', ['source_id'], unique=False)
    op.create_index(op.f('ix_anime_source_name'), 'anime', ['source_name'], unique=False)
    op.create_index(op.f('ix_anime_status'), 'anime', ['status'], unique=False)
    op.create_index(op.f('ix_anime_title'), 'anime', ['title'], unique=False)
    op.create_index(op.f('ix_anime_year'), 'anime', ['year'], unique=False)
    op.create_index('idx_anime_active_title', 'anime', ['is_active', 'title'], unique=False)

    # Create episodes table
    op.create_table('episodes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('anime_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('source_episode_id', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['anime_id'], ['anime.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('anime_id', 'source_episode_id', name='uq_episode_source'),
    )
    op.create_index(op.f('ix_episodes_anime_id'), 'episodes', ['anime_id'], unique=False)
    op.create_index(op.f('ix_episodes_id'), 'episodes', ['id'], unique=False)
    op.create_index(op.f('ix_episodes_is_active'), 'episodes', ['is_active'], unique=False)
    op.create_index(op.f('ix_episodes_number'), 'episodes', ['number'], unique=False)
    op.create_index(op.f('ix_episodes_source_episode_id'), 'episodes', ['source_episode_id'], unique=False)
    op.create_index('idx_episode_anime_number', 'episodes', ['anime_id', 'number'], unique=False)

    # Create video_sources table
    op.create_table('video_sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('episode_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('source_name', sa.String(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['episode_id'], ['episodes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_video_sources_episode_id'), 'video_sources', ['episode_id'], unique=False)
    op.create_index(op.f('ix_video_sources_id'), 'video_sources', ['id'], unique=False)
    op.create_index(op.f('ix_video_sources_is_active'), 'video_sources', ['is_active'], unique=False)
    op.create_index(op.f('ix_video_sources_priority'), 'video_sources', ['priority'], unique=False)
    op.create_index(op.f('ix_video_sources_source_name'), 'video_sources', ['source_name'], unique=False)
    op.create_index('idx_video_source_episode_priority', 'video_sources', ['episode_id', 'priority'], unique=False)


def downgrade() -> None:
    # Drop video_sources table
    op.drop_index('idx_video_source_episode_priority', table_name='video_sources')
    op.drop_index(op.f('ix_video_sources_source_name'), table_name='video_sources')
    op.drop_index(op.f('ix_video_sources_priority'), table_name='video_sources')
    op.drop_index(op.f('ix_video_sources_is_active'), table_name='video_sources')
    op.drop_index(op.f('ix_video_sources_id'), table_name='video_sources')
    op.drop_index(op.f('ix_video_sources_episode_id'), table_name='video_sources')
    op.drop_table('video_sources')

    # Drop episodes table
    op.drop_index('idx_episode_anime_number', table_name='episodes')
    op.drop_index(op.f('ix_episodes_source_episode_id'), table_name='episodes')
    op.drop_index(op.f('ix_episodes_number'), table_name='episodes')
    op.drop_index(op.f('ix_episodes_is_active'), table_name='episodes')
    op.drop_index(op.f('ix_episodes_id'), table_name='episodes')
    op.drop_index(op.f('ix_episodes_anime_id'), table_name='episodes')
    op.drop_table('episodes')

    # Drop anime table
    op.drop_index('idx_anime_active_title', table_name='anime')
    op.drop_index(op.f('ix_anime_year'), table_name='anime')
    op.drop_index(op.f('ix_anime_title'), table_name='anime')
    op.drop_index(op.f('ix_anime_status'), table_name='anime')
    op.drop_index(op.f('ix_anime_source_name'), table_name='anime')
    op.drop_index(op.f('ix_anime_source_id'), table_name='anime')
    op.drop_index(op.f('ix_anime_slug'), table_name='anime')
    op.drop_index(op.f('ix_anime_is_active'), table_name='anime')
    op.drop_index(op.f('ix_anime_id'), table_name='anime')
    op.drop_table('anime')
    
    # Drop anime status enum
    op.execute("DROP TYPE IF EXISTS animestatus CASCADE;")
