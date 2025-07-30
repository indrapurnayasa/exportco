#!/bin/bash

echo "=== Fixing Migration File ==="

cd /opt/hackathon-service

# 1. Backup original migration file
echo "Backing up original migration file..."
cp alembic/versions/add_last_access_column.py alembic/versions/add_last_access_column.py.backup

# 2. Create safe migration file
echo "Creating safe migration file..."
cat > alembic/versions/add_last_access_column.py << 'EOF'
"""Add last_access column to users table

Revision ID: a674c07a20cd
Revises: 839fa1b9f9ce
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a674c07a20cd'
down_revision = '839fa1b9f9ce'
branch_labels = None
depends_on = None

def upgrade():
    # Check if column exists first
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'last_access' not in columns:
        op.add_column('users', sa.Column('last_access', sa.DateTime(timezone=True), nullable=True))
    else:
        print("Column 'last_access' already exists, skipping...")

def downgrade():
    # Check if column exists before dropping
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'last_access' in columns:
        op.drop_column('users', 'last_access')
EOF

echo "✅ Migration file fixed!"
echo "Now you can run: /opt/miniconda3/bin/conda run -n hackathon-env alembic upgrade head" 