# Alternative MongoDB client installation options for Core Dockerfile

## Option 1: No MongoDB client (CURRENT - RECOMMENDED)

# Your Core service only needs Python motor driver

RUN groupadd -f docker

## Option 2: Install MongoDB Shell (mongosh) from official MongoDB repository

RUN curl -fsSL https://pgp.mongodb.com/server-7.0.asc | gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor && \
 echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/debian bookworm/mongodb-org/7.0 main" \
 > /etc/apt/sources.list.d/mongodb-org-7.0.list && \
 apt-get update && \
 apt-get install -y --no-install-recommends mongodb-mongosh mongodb-database-tools && \
 rm -rf /var/lib/apt/lists/\* && \
 groupadd -f docker

## Option 3: Install minimal MongoDB tools (lightweight alternative)

RUN apt-get update && \
 apt-get install -y --no-install-recommends \
 apt-transport-https \
 ca-certificates \
 && curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-archive-keyring.gpg \
 && echo "deb [signed-by=/usr/share/keyrings/mongodb-archive-keyring.gpg] https://repo.mongodb.org/apt/debian bookworm/mongodb-org/7.0 main" > /etc/apt/sources.list.d/mongodb-org-7.0.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends mongodb-database-tools \
 && rm -rf /var/lib/apt/lists/\* \
 && groupadd -f docker

## Option 4: Add MongoDB tools to base stage for debugging (if really needed)

# In the base stage, add:

RUN apt-get update && \
 apt-get install -y --no-install-recommends \
 mongodb-clients \
 && rm -rf /var/lib/apt/lists/\*
