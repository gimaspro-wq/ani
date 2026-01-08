"""add_rbac_tables

Revision ID: cd5d2fb44aad
Revises: c11248c9342e
Create Date: 2026-01-08 16:40:02.194715

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cd5d2fb44aad'
down_revision: Union[str, None] = 'c11248c9342e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create roles table
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_roles_id'), 'roles', ['id'], unique=False)
    op.create_index(op.f('ix_roles_name'), 'roles', ['name'], unique=True)
    op.create_index(op.f('ix_roles_code'), 'roles', ['code'], unique=True)
    
    # Create permissions table
    op.create_table(
        'permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('resource', sa.String(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('resource', 'action', name='uq_permission_resource_action')
    )
    op.create_index(op.f('ix_permissions_id'), 'permissions', ['id'], unique=False)
    op.create_index(op.f('ix_permissions_name'), 'permissions', ['name'], unique=True)
    op.create_index(op.f('ix_permissions_code'), 'permissions', ['code'], unique=True)
    op.create_index(op.f('ix_permissions_resource'), 'permissions', ['resource'], unique=False)
    op.create_index(op.f('ix_permissions_action'), 'permissions', ['action'], unique=False)
    
    # Create user_roles association table
    op.create_table(
        'user_roles',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )
    
    # Create role_permissions association table
    op.create_table(
        'role_permissions',
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )
    
    # Insert default roles
    op.execute("""
        INSERT INTO roles (name, code, description, created_at, updated_at)
        VALUES 
            ('User', 'user', 'Standard user with basic permissions', NOW(), NOW()),
            ('Admin', 'admin', 'Administrator with full permissions', NOW(), NOW())
    """)
    
    # Insert default permissions
    op.execute("""
        INSERT INTO permissions (name, code, description, resource, action, created_at)
        VALUES
            ('Read Library', 'library:read', 'Read user library', 'library', 'read', NOW()),
            ('Write Library', 'library:write', 'Modify user library', 'library', 'write', NOW()),
            ('Delete Library', 'library:delete', 'Delete library items', 'library', 'delete', NOW()),
            ('Read User', 'user:read', 'Read user information', 'user', 'read', NOW()),
            ('Write User', 'user:write', 'Modify user information', 'user', 'write', NOW()),
            ('Admin Access', 'admin:access', 'Full administrative access', 'admin', 'access', NOW())
    """)
    
    # Assign permissions to roles
    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id, created_at)
        SELECT r.id, p.id, NOW()
        FROM roles r, permissions p
        WHERE r.code = 'user' AND p.code IN ('library:read', 'library:write', 'library:delete', 'user:read', 'user:write')
    """)
    
    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id, created_at)
        SELECT r.id, p.id, NOW()
        FROM roles r, permissions p
        WHERE r.code = 'admin'
    """)
    
    # Assign 'user' role to all existing users
    op.execute("""
        INSERT INTO user_roles (user_id, role_id, created_at)
        SELECT u.id, r.id, NOW()
        FROM users u, roles r
        WHERE r.code = 'user'
    """)


def downgrade() -> None:
    op.drop_table('role_permissions')
    op.drop_table('user_roles')
    op.drop_index(op.f('ix_permissions_action'), table_name='permissions')
    op.drop_index(op.f('ix_permissions_resource'), table_name='permissions')
    op.drop_index(op.f('ix_permissions_code'), table_name='permissions')
    op.drop_index(op.f('ix_permissions_name'), table_name='permissions')
    op.drop_index(op.f('ix_permissions_id'), table_name='permissions')
    op.drop_table('permissions')
    op.drop_index(op.f('ix_roles_code'), table_name='roles')
    op.drop_index(op.f('ix_roles_name'), table_name='roles')
    op.drop_index(op.f('ix_roles_id'), table_name='roles')
    op.drop_table('roles')

