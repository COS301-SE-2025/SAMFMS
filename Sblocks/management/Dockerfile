FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 21010

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "21010"]
