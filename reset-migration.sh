#!/bin/bash

echo "=== Resetting Migration History ==="

cd /opt/hackathon-service

# 1. Backup current data
echo "Backing up current data..."
PGPASSWORD=Hackathon2025 pg_dump -h localhost -U maverick -d hackathondb > backup_before_reset_$(date +%Y%m%d_%H%M%S).sql

# 2. Drop alembic_version table
echo "Dropping alembic_version table..."
PGPASSWORD=Hackathon2025 psql -h localhost -U maverick -d hackathondb -c "DROP TABLE IF EXISTS alembic_version;"

# 3. Mark as latest migration
echo "Marking as latest migration..."
/opt/miniconda3/bin/conda run -n hackathon-env alembic stamp head

# 4. Verify migration status
echo "Final migration status:"
/opt/miniconda3/bin/conda run -n hackathon-env alembic current

echo "Migration reset completed!" 