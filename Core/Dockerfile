FROM python:3.9-slim AS base

WORKDIR /app

# Install only the essential tools first
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl ca-certificates gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
# This layer is separated to leverage Docker build cache
COPY Core/requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Install Docker CLI - done after installing Python dependencies for better caching
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian bookworm stable" > /etc/apt/sources.list.d/docker.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends docker-ce-cli docker-compose-plugin && \
    rm -rf /var/lib/apt/lists/*

# Copy Core application files - keep this separate from the entire project copy
COPY Core/ .

FROM base AS test
RUN pip install --no-cache-dir pytest pytest-xdist
CMD ["pytest", "--disable-warnings"]

FROM base AS runtime

# Install MongoDB - combined into a single RUN command to reduce layers
RUN curl -fsSL https://pgp.mongodb.com/server-7.0.asc | gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor && \
    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/debian bookworm/mongodb-org/7.0 main" \
      > /etc/apt/sources.list.d/mongodb-org-7.0.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends mongodb-org && \
    rm -rf /var/lib/apt/lists/* && \
    # Create docker group in the same layer
    groupadd -f docker

# Copy only essential files needed for operations - leverage .dockerignore
# This is much more selective than copying everything
COPY --from=base /app /app
COPY Core/config/ /project/Core/config/
# Create a directory for docker-compose file but make it optional
RUN mkdir -p /project

EXPOSE 8000 27017

# Copy startup script with explicit line ending handling
COPY Core/start.sh /start.sh
# Convert Windows line endings (CRLF) to Unix (LF) and ensure script is executable
RUN sed -i 's/\r$//' /start.sh && \
    chmod +x /start.sh

CMD ["/bin/sh", "/start.sh"]
