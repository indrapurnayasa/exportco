#!/bin/bash

echo "=== Fixing Migration Error ==="

cd /opt/hackathon-service

# 1. Check if last_access column exists
echo "Checking if last_access column exists..."
COLUMN_EXISTS=$(PGPASSWORD=Hackathon2025 psql -h localhost -U maverick -d hackathondb -t -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'last_access';" | tr -d ' ')

echo "Column exists: $COLUMN_EXISTS"

# 2. If column exists, mark migration as completed
if [ "$COLUMN_EXISTS" -gt 0 ]; then
    echo "last_access column exists, marking migration as completed..."
    /opt/miniconda3/bin/conda run -n hackathon-env alembic stamp head
    echo "✅ Migration marked as completed"
else
    echo "last_access column does not exist, running migration..."
    /opt/miniconda3/bin/conda run -n hackathon-env alembic upgrade head
fi

# 3. Verify migration status
echo "Final migration status:"
/opt/miniconda3/bin/conda run -n hackathon-env alembic current

echo "Migration fix completed!" 