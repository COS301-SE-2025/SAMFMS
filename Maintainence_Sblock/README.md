# Maintenance Sblock

This is the Maintenance Sblock Django service.

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

1. Build the Docker image:
   ```powershell
   docker build -t maintenance-sblock .
   ```
2. Run the Docker container:
   ```powershell
   docker run -p 8002:8000 maintenance-sblock
   ```

The service will be available at [http://localhost:8002](http://localhost:8002)
