FROM python:3.9-slim AS base
WORKDIR /app


COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

COPY . .


FROM base AS test
RUN pip install --no-cache-dir pytest pytest-xdist
CMD ["pytest", "--disable-warnings"]


FROM base AS runtime


RUN apt-get update && \
    apt-get install -y gnupg curl && \
    curl -fsSL https://pgp.mongodb.com/server-7.0.asc | gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor && \
    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/debian bookworm/mongodb-org/7.0 main" \
      > /etc/apt/sources.list.d/mongodb-org-7.0.list && \
    apt-get update && \
    apt-get install -y mongodb-org && \
    rm -rf /var/lib/apt/lists/*

EXPOSE 8000 27017
COPY start.sh /start.sh
RUN chmod +x /start.sh
CMD ["/start.sh"]
