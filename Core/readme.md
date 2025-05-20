# Core Service

This is the Core Django service for SAMFMS.

## Running Locally (for development)

1. Create and activate a virtual environment (optional but recommended):
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate
   ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Run migrations:
   ```powershell
   python manage.py migrate
   ```
4. Start the development server:
   ```powershell
   python manage.py runserver
   ```

## Running in Docker

1. Build the Docker image (usually handled by `docker-compose`):
   ```powershell
   docker build -t mcore-service .
   ```
2. Run the Docker container (usually handled by `docker-compose`):
   ```powershell
   docker run -p 8000:8000 mcore-service
   ```

The service will be available at [http://localhost:8000](http://localhost:8000) when run via `docker-compose`.

## Linting

To check the code for style and errors, run:

```powershell
flake8 .
```
