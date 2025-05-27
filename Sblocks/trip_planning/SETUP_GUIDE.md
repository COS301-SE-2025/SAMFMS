# 🚀 How to Run the Trip Planning Service System

## Quick Start Guide

### Prerequisites Check

Before running the system, ensure you have the following installed:

1. **Python 3.9+**

   ```powershell
   python --version
   ```

2. **MongoDB** (or Docker for containerized setup)
3. **RabbitMQ** (or Docker for containerized setup)
4. **Git**

---

## 🐳 Option 1: Docker Compose (Recommended - Easiest)

This method starts all services automatically with a single command:

### 1. Navigate to the project directory

```powershell
cd "c:\Users\user\OneDrive\Documents\capstone\repo\SAMFMS\Sblocks\trip_planning"
```

### 2. Start all services

```powershell
docker-compose up -d
```

### 3. Check service status

```powershell
docker-compose ps
```

### 4. View logs

```powershell
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f trip-planning
```

### 5. Access the services

- **Trip Planning API**: http://localhost:8003
- **API Documentation**: http://localhost:8003/docs
- **MongoDB Express**: http://localhost:8081 (admin/admin123)
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)

### 6. Stop services

```powershell
docker-compose down
```

---

## 💻 Option 2: Local Development Setup

### Step 1: Prepare Dependencies

#### Install MongoDB

```powershell
# Option A: Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Option B: Download and install from https://www.mongodb.com/try/download/community
```

#### Install RabbitMQ

```powershell
# Option A: Using Docker
docker run -d -p 5672:5672 -p 15672:15672 --name rabbitmq rabbitmq:3-management

# Option B: Download and install from https://www.rabbitmq.com/download.html
```

#### Install Redis (Optional)

```powershell
# Using Docker
docker run -d -p 6379:6379 --name redis redis:latest
```

### Step 2: Setup the Application

#### 1. Navigate to project directory

```powershell
cd "c:\Users\user\OneDrive\Documents\capstone\repo\SAMFMS\Sblocks\trip_planning"
```

#### 2. Create virtual environment

```powershell
python -m venv venv
```

#### 3. Activate virtual environment

```powershell
.\venv\Scripts\Activate.ps1
```

#### 4. Install dependencies

```powershell
pip install -r requirements.txt
```

#### 5. Setup environment configuration

```powershell
# Copy environment template
Copy-Item .env.example .env

# Edit configuration (use notepad or your preferred editor)
notepad .env
```

#### 6. Verify database connections

```powershell
# Test MongoDB
python -c "import pymongo; client = pymongo.MongoClient('mongodb://localhost:27017'); print('MongoDB:', client.server_info()['version'])"

# Test RabbitMQ
python -c "import pika; conn = pika.BlockingConnection(pika.URLParameters('amqp://guest:guest@localhost:5672/')); print('RabbitMQ: Connected'); conn.close()"
```

### Step 3: Run the Service

#### Option A: Using PowerShell startup script

```powershell
.\start.ps1
```

#### Option B: Manual startup

```powershell
uvicorn main:app --host 0.0.0.0 --port 8003 --reload
```

#### Option C: Using Python directly

```powershell
python main.py
```

---

## 🔧 Verification & Testing

### 1. Check service health

```powershell
# Using PowerShell
Invoke-RestMethod -Uri "http://localhost:8003/health"

# Using curl (if available)
curl http://localhost:8003/health
```

### 2. Access API documentation

Open your browser and navigate to:

- **Swagger UI**: http://localhost:8003/docs
- **ReDoc**: http://localhost:8003/redoc

### 3. Test API endpoints

```powershell
# Get all trips
Invoke-RestMethod -Uri "http://localhost:8003/api/v1/trips"

# Get all vehicles
Invoke-RestMethod -Uri "http://localhost:8003/api/v1/vehicles"

# Get all drivers
Invoke-RestMethod -Uri "http://localhost:8003/api/v1/drivers"
```

### 4. Run automated tests

```powershell
# Activate virtual environment if not already active
.\venv\Scripts\Activate.ps1

# Run tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=. --cov-report=html
```

---

## 🌐 Integration with Frontend

The React frontend should be configured to connect to the Trip Planning Service:

### Frontend Configuration

In your React app's configuration, set the API base URL:

```javascript
// In your frontend environment config
REACT_APP_TRIP_PLANNING_API_URL=http://localhost:8003/api/v1
```

### MCore Integration

The service automatically publishes events to RabbitMQ for MCore consumption:

- Trip status updates
- Vehicle location updates
- Driver assignments
- Schedule changes

---

## 📊 Monitoring & Management

### Service URLs

- **Main API**: http://localhost:8003
- **Health Check**: http://localhost:8003/health
- **API Docs**: http://localhost:8003/docs

### Database Management

- **MongoDB Express**: http://localhost:8081
  - Username: admin
  - Password: admin123

### Message Queue Management

- **RabbitMQ Management**: http://localhost:15672
  - Username: guest
  - Password: guest

### Log Files

- Application logs: `logs/trip-planning.log`
- Docker logs: `docker-compose logs -f trip-planning`

---

## 🚨 Troubleshooting

### Common Issues & Solutions

#### 1. Port Already in Use

```powershell
# Check what's using port 8003
netstat -ano | findstr :8003

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or change port in .env file
# PORT=8004
```

#### 2. MongoDB Connection Failed

```powershell
# Check if MongoDB is running
docker ps | findstr mongodb

# Or check Windows service
Get-Service -Name "MongoDB"

# Restart MongoDB
docker restart mongodb
```

#### 3. RabbitMQ Connection Failed

```powershell
# Check if RabbitMQ is running
docker ps | findstr rabbitmq

# Restart RabbitMQ
docker restart rabbitmq
```

#### 4. Python Module Import Errors

```powershell
# Ensure virtual environment is activated
.\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### 5. Database Initialization Issues

```powershell
# Access MongoDB and initialize manually
docker exec -it mongodb mongosh

# Run initialization script
docker exec -it mongodb mongosh trip_planning_db /docker-entrypoint-initdb.d/mongo-init.js
```

### Debug Mode

Enable debug mode for detailed error information:

```powershell
# In .env file
DEBUG=true
LOG_LEVEL=DEBUG
```

### Getting Help

1. Check the service logs
2. Verify all dependencies are running
3. Test database connections
4. Check firewall settings
5. Review environment configuration

---

## 📈 Performance Tips

### For Development

- Use Docker Compose for consistent environment
- Enable debug mode for detailed logging
- Use MongoDB Express for database inspection
- Monitor RabbitMQ queues

### For Production

- Disable debug mode
- Use production database settings
- Implement proper logging
- Set up monitoring and alerts
- Use reverse proxy (nginx)
- Implement SSL/TLS

---

## 🔄 Next Steps

After successfully running the Trip Planning Service:

1. **Test all API endpoints** using the Swagger UI
2. **Create sample data** using the API or MongoDB Express
3. **Integrate with React frontend** by updating API endpoints
4. **Configure MCore** to consume RabbitMQ events
5. **Set up monitoring** and logging for production use

---

**🎉 You're now ready to use the Trip Planning Service!**

For additional help, refer to the comprehensive README.md file or check the API documentation at `/docs`.
