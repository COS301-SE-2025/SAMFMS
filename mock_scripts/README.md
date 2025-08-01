# SAMFMS Mock Data Generation Scripts

This directory contains scripts to generate realistic mock data for the SAMFMS (Smart Automated Fleet Management System) by making API calls to the Core and Maintenance services.

## 📋 Overview

The mock data scripts create:

- **Vehicles**: Cars, trucks, vans, buses with realistic specifications
- **Users**: Drivers and fleet managers with proper roles and permissions
- **Maintenance Records**: Historical and scheduled maintenance activities
- **License Records**: Vehicle registrations, driver licenses, certifications
- **Maintenance Schedules**: Recurring maintenance plans

## 🚀 Quick Start

### Prerequisites

1. **SAMFMS Services Running**: Ensure Core service (port 21004) and Maintenance service (port 21004) are running
2. **Python Environment**: Python 3.8+ with required packages
3. **Authentication**: Valid SAMFMS account credentials

### Authentication Setup

The scripts require authentication to access SAMFMS services. You can configure credentials in several ways:

#### Option 1: Environment Variables (Recommended)

```bash
export SAMFMS_LOGIN_EMAIL="mvanheerdentuks@gmail.com"
export SAMFMS_LOGIN_PASSWORD="your_password"
```

#### Option 2: Interactive Prompt (Default)

If no password is set, scripts will prompt you securely:

```
Enter password for mvanheerdentuks@gmail.com: [hidden input]
```

#### Option 3: Edit config.py

Modify the `LOGIN_EMAIL` in `config.py` if using a different account.

#### Test Authentication

Before running data generation, test your credentials:

```bash
python test_auth.py
```

### Install Dependencies

```bash
cd mock_scripts
pip install aiohttp
```

**Note**: `getpass` module (used for secure password input) is included in Python's standard library.

### Run All Scripts (Recommended)

Create a complete dataset with default values:

```bash
python create_all_mock_data.py
```

This will create:

- 50 vehicles
- 50 drivers
- 10 fleet managers
- 100 maintenance records
- 80 license records
- 60 maintenance schedules

**Note**: All mock users (drivers and managers) are created with the password `Password1!` for testing purposes.

### Quick Test

For testing purposes, create a smaller dataset:

```bash
python create_all_mock_data.py --quick
```

## 📝 Individual Scripts

### 1. Create Vehicles

```bash
python create_vehicles.py --count 50
```

Creates vehicles with:

- Realistic VINs and license plates
- Various makes, models, and years (2015-2024)
- Current mileage based on age
- Insurance information
- Location data
- Technical specifications

### 2. Create Users

```bash
python create_users.py --drivers 30 --managers 10
```

Creates:

- **Drivers**: With CDL licenses, experience levels, certifications
- **Fleet Managers**: With management permissions and responsibilities

### 3. Create Maintenance Data

```bash
python create_maintenance_data.py --records 100 --licenses 80 --schedules 60
```

Creates:

- **Maintenance Records**: Past, current, and future maintenance
- **License Records**: Vehicle registrations, driver licenses, permits
- **Maintenance Schedules**: Recurring maintenance plans

## ⚙️ Configuration

### Rate Limiting

Scripts are configured to avoid overloading services:

- **120 requests per minute** (0.5-second delays between requests)
- **Batch processing** with pauses between batches
- **Conservative retry logic**

### Service URLs

Configure in `config.py`:

```python
CORE_BASE_URL = "http://localhost:21004"
MAINTENANCE_BASE_URL = "http://localhost:21004"
```

### Data Volumes

Recommended volumes for different environments:

| Environment | Vehicles | Drivers | Managers | Records | Licenses | Schedules |
| ----------- | -------- | ------- | -------- | ------- | -------- | --------- |
| Development | 10       | 5       | 2        | 20      | 15       | 10        |
| Testing     | 50       | 50      | 10       | 100     | 80       | 60        |
| Demo        | 100      | 60      | 20       | 200     | 150      | 120       |

## 🔧 Customization

### Custom Data Volumes

```bash
python create_all_mock_data.py \
  --vehicles 100 \
  --drivers 60 \
  --managers 20 \
  --records 200 \
  --licenses 150 \
  --schedules 120
```

### Verbose Logging

Enable detailed logging for debugging:

```bash
python create_all_mock_data.py --verbose
```

### Environment Variables

Set custom service URLs:

```bash
export CORE_SERVICE_URL="http://your-core-service:21004"
export MAINTENANCE_SERVICE_URL="http://your-maintenance-service:21004"
python create_all_mock_data.py
```

## 📊 Data Characteristics

### Vehicles

- **Makes**: Toyota, Ford, Chevrolet, Honda, Nissan, Mercedes-Benz, BMW, Audi, VW, Hyundai
- **Types**: Sedan, SUV, truck, van, pickup truck, bus, motorcycle, delivery van, semi-truck
- **Years**: 2015-2024 with realistic mileage
- **Status**: 75% active, 20% maintenance, 5% inactive

### Users

- **Drivers**: Realistic licenses, experience levels, clean driving records (75%)
- **Fleet Managers**: Management permissions, team sizes, salary ranges
- **Locations**: 10 major US cities

### Maintenance Data

- **Records**: 60% completed (historical), 20% current, 20% future
- **Types**: Oil changes, inspections, brake work, transmission service, etc.
- **Costs**: Realistic pricing based on maintenance type
- **Schedules**: Mileage-based, time-based, and condition-based

### License Records

- **Vehicle Licenses**: Registration, inspection, insurance, emissions
- **Driver Licenses**: CDL classes, endorsements, restrictions
- **Compliance**: 95% compliant with realistic expiry dates

## 🐛 Troubleshooting

### Common Issues

1. **Connection Errors**

   - Verify services are running on correct ports
   - Check firewall settings
   - Ensure network connectivity

2. **Authentication Errors**

   - Check mock authentication tokens in `config.py`
   - Verify service authentication requirements

3. **Rate Limiting**

   - Scripts respect rate limits automatically
   - If you see timeouts, services may be overloaded

4. **Data Dependencies**
   - Run scripts in order: vehicles → users → maintenance data
   - Maintenance data requires existing vehicles and users

### Debug Mode

Enable verbose logging:

```bash
python create_all_mock_data.py --verbose
```

### Check Service Health

Verify services are responding:

```bash
curl http://localhost:21004/health
curl http://localhost:21004/health
```

## 📈 Performance

### Expected Runtime

| Data Volume | Estimated Time |
| ----------- | -------------- |
| Quick test  | 1-2 minutes    |
| Default     | 2-4 minutes    |
| Large demo  | 5-8 minutes    |

### Resource Usage

- **Memory**: ~50MB per script
- **Network**: ~1-2 MB total traffic
- **CPU**: Minimal (mostly I/O waiting)

## 🔍 Verification

After running scripts, verify data creation:

1. **Check Logs**: Review script output for success/failure rates
2. **API Calls**: Test endpoints to verify data exists
3. **Web Interface**: Browse created data in SAMFMS dashboard
4. **Database**: Query MongoDB collections directly if needed

### Sample Verification Commands

```bash
# Check vehicles
curl "http://localhost:21004/vehicles?limit=10"

# Check users
curl "http://localhost:21004/users?limit=10"

# Check maintenance records
curl "http://localhost:21004/maintenance/records?limit=10"

# Check licenses
curl "http://localhost:21004/maintenance/licenses?limit=10"
```

## 📚 File Structure

```
mock_scripts/
├── README.md                    # This file
├── config.py                    # Configuration and constants
├── api_utils.py                 # API client utilities
├── create_vehicles.py           # Vehicle creation script
├── create_users.py              # User creation script
├── create_maintenance_data.py   # Maintenance data script
└── create_all_mock_data.py      # Master orchestration script
```

## 🤝 Contributing

When adding new mock data scripts:

1. Follow the existing pattern in `api_utils.py`
2. Add rate limiting with `DELAY_BETWEEN_REQUESTS`
3. Include proper error handling and logging
4. Add batch processing for large datasets
5. Update this README with new capabilities

## 📄 License

These scripts are part of the SAMFMS project and follow the same license terms.
