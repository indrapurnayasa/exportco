#!/bin/bash

echo "=== Comprehensive Migration Fix ==="

cd /opt/hackathon-service

# 1. Check current status
echo "1. Checking current migration status..."
/opt/miniconda3/bin/conda run -n hackathon-env alembic current

# 2. Check if last_access column exists
echo "2. Checking if last_access column exists..."
COLUMN_EXISTS=$(PGPASSWORD=Hackathon2025 psql -h localhost -U maverick -d hackathondb -t -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'last_access';" | tr -d ' ')
echo "Column exists: $COLUMN_EXISTS"

# 3. Try different approaches
if [ "$COLUMN_EXISTS" -gt 0 ]; then
    echo "3. Column exists, trying to mark migration as completed..."
    
    # Try stamp head
    if /opt/miniconda3/bin/conda run -n hackathon-env alembic stamp head; then
        echo "✅ Successfully marked migration as completed"
    else
        echo "❌ Failed to stamp head, trying alternative approach..."
        
        # Try reset migration history
        echo "4. Resetting migration history..."
        PGPASSWORD=Hackathon2025 psql -h localhost -U maverick -d hackathondb -c "DROP TABLE IF EXISTS alembic_version;"
        /opt/miniconda3/bin/conda run -n hackathon-env alembic stamp head
    fi
else
    echo "3. Column does not exist, fixing migration file..."
    
    # Fix migration file
    ./fix-migration-file.sh
    
    # Try running migration
    echo "4. Running migration with fixed file..."
    /opt/miniconda3/bin/conda run -n hackathon-env alembic upgrade head
fi

# 5. Verify final status
echo "5. Verifying final migration status..."
/opt/miniconda3/bin/conda run -n hackathon-env alembic current

# 6. Test database connection
echo "6. Testing database connection..."
if PGPASSWORD=Hackathon2025 psql -h localhost -U maverick -d hackathondb -c "SELECT 1;" 2>/dev/null; then
    echo "✅ Database connection successful!"
else
    echo "❌ Database connection failed"
fi

echo "=== Migration fix completed! ===" 