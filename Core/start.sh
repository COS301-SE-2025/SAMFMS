#!/bin/sh
# Simple startup script without complex syntax

echo "Starting Core service..."

# Start MongoDB
mkdir -p /data/db
echo "Starting MongoDB..."
mongod --fork --logpath /var/log/mongodb.log --dbpath /data/db

# Simple wait for MongoDB to start
echo "Waiting for MongoDB to start..."
sleep 3

# Start Uvicorn
echo "Starting API server..."
uvicorn main:app --host 0.0.0.0 --port 8000
