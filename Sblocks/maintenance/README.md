# Maintenance Service (Sblock)

The Maintenance Service is a microservice within the SAMFMS (South African Fleet Management System) that handles all maintenance-related operations for vehicles, including maintenance records, schedules, licenses, and analytics.

## Features

### Core Functionality

- **Maintenance Records Management**: Create, update, delete, and track vehicle maintenance records
- **Maintenance Schedules**: Plan and manage upcoming maintenance activities
- **License Management**: Track vehicle licenses, permits, and compliance documents
- **Vendor Management**: Manage maintenance service providers and their performance
- **Notification System**: Automated alerts for upcoming maintenance and license expirations

### Analytics & Reporting

- **Comprehensive Analytics**: Detailed insights into maintenance costs, patterns, and performance
- **Cost Analysis**: Track maintenance expenses across vehicles, types, and time periods
- **Performance Metrics**: KPIs for maintenance efficiency and compliance
- **Outlier Detection**: Identify unusual maintenance costs and patterns
- **Trend Analysis**: Historical data analysis and forecasting

## API Endpoints

### Maintenance Records

- `GET /api/v1/maintenance/records` - List maintenance records
- `POST /api/v1/maintenance/records` - Create new maintenance record
- `GET /api/v1/maintenance/records/{id}` - Get specific record
- `PUT /api/v1/maintenance/records/{id}` - Update record
- `DELETE /api/v1/maintenance/records/{id}` - Delete record

### Maintenance Schedules

- `GET /api/v1/maintenance/schedules` - List maintenance schedules
- `POST /api/v1/maintenance/schedules` - Create new schedule
- `GET /api/v1/maintenance/schedules/{id}` - Get specific schedule
- `PUT /api/v1/maintenance/schedules/{id}` - Update schedule
- `DELETE /api/v1/maintenance/schedules/{id}` - Delete schedule

### License Management

- `GET /api/v1/maintenance/licenses` - List licenses
- `POST /api/v1/maintenance/licenses` - Create new license
- `GET /api/v1/maintenance/licenses/{id}` - Get specific license
- `PUT /api/v1/maintenance/licenses/{id}` - Update license
- `DELETE /api/v1/maintenance/licenses/{id}` - Delete license

### Analytics Endpoints

#### Basic Analytics

- `GET /analytics/dashboard` - Maintenance dashboard overview
- `GET /analytics/costs` - Cost analytics with time grouping
- `GET /analytics/trends` - Maintenance trends analysis
- `GET /analytics/vendors` - Vendor performance analytics
- `GET /analytics/licenses` - License compliance analytics
- `GET /analytics/metrics/kpi` - Key performance indicators

#### Advanced Analytics (New)

- `GET /analytics/timeframe/total-cost` - Total cost within timeframe
- `GET /analytics/timeframe/records-count` - Records count within timeframe
- `GET /analytics/timeframe/vehicles-serviced` - Unique vehicles serviced count
- `GET /analytics/maintenance-by-type` - Records grouped by maintenance type
- `GET /analytics/cost-outliers` - Maintenance records with outlier costs
- `GET /analytics/timeframe/maintenance-per-vehicle` - Maintenance count per vehicle

#### Vehicle-Specific Analytics

- `GET /analytics/summary/vehicle/{vehicle_id}` - Comprehensive vehicle maintenance summary

## Quick Start

### Prerequisites

- Python 3.11+
- MongoDB
- RabbitMQ (for event messaging)
- Redis (for caching)

### Environment Variables

```env
# Database
MONGODB_URL=mongodb://localhost:27017/samfms_maintenance
REDIS_URL=redis://localhost:6379

# RabbitMQ
RABBITMQ_URL=amqp://localhost:5672
RABBITMQ_EXCHANGE=samfms.events

# Service Configuration
SERVICE_NAME=maintenance
SERVICE_VERSION=2.0.0
API_PREFIX=/api/v1/maintenance

# Security
JWT_SECRET_KEY=your-secret-key
API_KEY=your-api-key

# External Services
MANAGEMENT_SERVICE_URL=http://management-service:8000
NOTIFICATION_SERVICE_URL=http://notification-service:8000
```

### Installation

1. **Install Dependencies**

   ```bash
   cd Sblocks/maintenance
   pip install -r requirements.txt
   ```

2. **Start the Service**

   ```bash
   # Development
   python main.py

   # Production with Docker
   docker build -t samfms-maintenance .
   docker run -p 8002:8000 samfms-maintenance
   ```

3. **Start Background Services**

   ```bash
   # Event consumer
   python start_consumer.py

   # Background jobs
   python -m services.background_jobs
   ```

### Development Setup

1. **Database Setup**

   ```bash
   # Start MongoDB
   docker run -d -p 27017:27017 --name mongodb mongo:latest

   # Create indexes
   python -c "from repositories.database import db_manager; import asyncio; asyncio.run(db_manager.create_indexes())"
   ```

2. **Message Queue Setup**

   ```bash
   # Start RabbitMQ
   docker run -d -p 5672:5672 -p 15672:15672 --name rabbitmq rabbitmq:3-management
   ```

3. **Testing**

   ```bash
   # Run unit tests
   pytest tests/unit/

   # Run integration tests
   pytest tests/integration/

   # Run with coverage
   pytest --cov=. --cov-report=html
   ```

## Architecture

### Service Structure

```
maintenance/
├── api/                    # API routes and endpoints
│   ├── routes/            # Route handlers
│   └── dependencies.py    # Dependency injection
├── services/              # Business logic services
├── repositories/          # Data access layer
├── schemas/               # Pydantic models
├── events/                # Event handling (RabbitMQ)
├── middleware/            # Custom middleware
├── utils/                 # Utility functions
└── tests/                 # Test suite
```

### Key Components

- **FastAPI**: Web framework for API development
- **MongoDB**: Primary database for maintenance data
- **RabbitMQ**: Event messaging between services
- **Redis**: Caching and session storage
- **Celery**: Background task processing
- **Pydantic**: Data validation and serialization

### Event-Driven Architecture

The service participates in an event-driven architecture:

- **Publishes Events**: Vehicle maintenance status changes, license expirations
- **Consumes Events**: Vehicle updates, user notifications
- **Event Types**: `maintenance.record.created`, `maintenance.schedule.updated`, `license.expired`

## Analytics Features

The maintenance service provides comprehensive analytics capabilities:

### 1. **Cost Analytics**

- Total maintenance costs by time period
- Cost breakdown by maintenance type
- Cost per vehicle analysis
- Outlier detection for unusual expenses

### 2. **Performance Metrics**

- Maintenance frequency per vehicle
- Service completion rates
- Vendor performance comparisons
- Compliance tracking

### 3. **Predictive Insights**

- Maintenance trend analysis
- Cost forecasting
- Failure pattern identification
- Optimal maintenance scheduling

### 4. **Reporting**

- Executive dashboards
- Detailed maintenance reports
- License compliance reports
- Cost analysis reports

## Integration with Other Services

### Management Service

- Vehicle information retrieval
- Fleet hierarchy data
- User and role management

### Notification Service

- Maintenance reminders
- License expiration alerts
- Cost threshold notifications

### Security Service

- Authentication and authorization
- API key validation
- Audit logging

## Monitoring and Health Checks

### Health Endpoints

- `GET /health` - Service health status
- `GET /health/detailed` - Detailed component health
- `GET /metrics` - Prometheus metrics

### Logging

- Structured logging with correlation IDs
- Request/response logging
- Performance metrics
- Error tracking

### Monitoring

- Application performance monitoring (APM)
- Database query performance
- Event processing metrics
- Cache hit/miss rates

## Security

### Authentication & Authorization

- JWT-based authentication
- Role-based access control (RBAC)
- Permission-based endpoint access
- API key authentication for service-to-service calls

### Data Protection

- Input validation and sanitization
- SQL injection prevention
- XSS protection
- Rate limiting

### Compliance

- Audit logging for all operations
- Data retention policies
- GDPR compliance features
- Secure data deletion

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "main.py"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: maintenance-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: maintenance-service
  template:
    metadata:
      labels:
        app: maintenance-service
    spec:
      containers:
        - name: maintenance
          image: samfms/maintenance-service:latest
          ports:
            - containerPort: 8000
```

## Contributing

### Code Standards

- Follow PEP 8 for Python code style
- Use type hints for all functions
- Write comprehensive docstrings
- Maintain test coverage above 90%

### Development Workflow

1. Create feature branch from `main`
2. Implement changes with tests
3. Run linting and tests locally
4. Submit pull request
5. Code review and approval
6. Merge to main

### Testing Guidelines

- Unit tests for business logic
- Integration tests for database operations
- API tests for endpoint functionality
- Performance tests for analytics queries

## Documentation

- **API Documentation**: Available at `/docs` (Swagger UI)
- **Analytics API Guide**: See `ANALYTICS_API_README.md`
- **Architecture Diagrams**: See `docs/architecture/`
- **Database Schema**: See `docs/database/`

## Support

For questions, issues, or contributions:

- **Repository**: [SAMFMS GitHub Repository]
- **Issue Tracker**: GitHub Issues
- **Documentation**: `/docs` endpoint
- **Team Contact**: development@samfms.co.za

---

_Last Updated: August 2025_
_Service Version: 2.0.0_
