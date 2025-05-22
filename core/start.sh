#!/bin/bash

# Start MongoDB
# Create directory for MongoDB data if it doesn't exist
mkdir -p /data/db
mongod --fork --logpath /var/log/mongodb.log --dbpath /data/db

# Start Uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000
