FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Copy startup script
COPY startup.py /startup.py

CMD ["python", "/startup.py"]
