FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TZ=Africa/Johannesburg

# Default to empty settings, these should be provided by docker-compose or environment
ENV SMTP_SERVER=smtp.gmail.com
ENV SMTP_PORT=587
ENV EMAIL_ADDRESS=""
ENV EMAIL_PASSWORD=""
ENV EMAIL_SENDER_NAME="SAMFMS System"

EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
