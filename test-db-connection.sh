#!/bin/bash

echo "🧪 Testing Database Connection"
echo "=============================="

# Check if PostgreSQL container is running
echo "1. Checking PostgreSQL container status..."
if docker ps | grep -q hackathon-bi; then
    echo "✅ PostgreSQL container 'hackathon-bi' is running"
else
    echo "❌ PostgreSQL container 'hackathon-bi' is not running!"
    exit 1
fi

# Get container details
echo ""
echo "2. PostgreSQL container details:"
docker ps | grep hackathon-bi

# Get IP address
echo ""
echo "3. Getting IP address..."
PG_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' hackathon-bi)
echo "📍 IP Address: $PG_IP"

# Test connection with IP
echo ""
echo "4. Testing connection with IP address..."
if docker run --rm --network bridge postgres:15 psql -h $PG_IP -U maverick -d hackathondb -c "SELECT version();" 2>/dev/null; then
    echo "✅ Connection with IP successful"
else
    echo "❌ Connection with IP failed"
fi

# Test connection with container name
echo ""
echo "5. Testing connection with container name..."
if docker run --rm --network bridge postgres:15 psql -h hackathon-bi -U maverick -d hackathondb -c "SELECT version();" 2>/dev/null; then
    echo "✅ Connection with container name successful"
else
    echo "❌ Connection with container name failed"
fi

# Test with psycopg2 (same as your app)
echo ""
echo "6. Testing with psycopg2 (Python)..."
docker run --rm --network bridge python:3.10-slim bash -c "
pip install psycopg2-binary
python -c \"
import psycopg2
try:
    conn = psycopg2.connect('postgresql://maverick:1946%40Maverick@hackathon-bi:5432/hackathondb')
    print('✅ psycopg2 connection successful')
    conn.close()
except Exception as e:
    print(f'❌ psycopg2 connection failed: {e}')
\"
"

echo ""
echo "🎯 Connection test complete!" 