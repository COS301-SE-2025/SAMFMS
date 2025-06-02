import os
import logging
import motor.motor_asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
from bson import ObjectId

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://localhost:27017/vehicles_db")
DATABASE_NAME = DATABASE_URL.split("/")[-1]
client = motor.motor_asyncio.AsyncIOMotorClient(DATABASE_URL)
db = client[DATABASE_NAME]

# Collections
vehicles_collection = db.vehicles
maintenance_records_collection = db.maintenance_records
vehicle_specifications_collection = db.vehicle_specifications
vehicle_documents_collection = db.vehicle_documents
vehicle_activity_log_collection = db.vehicle_activity_log

# Create indexes
async def create_indexes():
    """Create indexes for better query performance"""
    try:
        # Vehicle indexes
        await vehicles_collection.create_index([("make", 1), ("model", 1)])
        await vehicles_collection.create_index([("year", 1), ("is_active", 1)])
        await vehicles_collection.create_index([("fuel_type", 1)])
        
        # Maintenance records indexes
        await maintenance_records_collection.create_index([("vehicle_id", 1), ("service_date", 1)])
        await maintenance_records_collection.create_index([("maintenance_type", 1), ("service_date", 1)])
        await maintenance_records_collection.create_index([("next_service_date", 1)])
        
        # Vehicle specifications indexes
        await vehicle_specifications_collection.create_index([("vehicle_id", 1)])
        
        # Vehicle documents indexes
        await vehicle_documents_collection.create_index([("vehicle_id", 1), ("document_type", 1)])
        await vehicle_documents_collection.create_index([("expiry_date", 1), ("is_valid", 1)])
        
        logger.info("Database indexes initialized successfully")
    except Exception as e:
        logger.error(f"Failed to create database indexes: {e}")

def get_db():
    """Dependency to get database client"""
    return db

def init_database():
    """Initialize the database with tables and indexes"""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Create custom indexes for better performance
        with engine.connect() as conn:
            # Vehicle indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_vehicles_make_model 
                ON vehicles (make, model)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_vehicles_year_active 
                ON vehicles (year, is_active)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_vehicles_fuel_type 
                ON vehicles (fuel_type)
            """))
            
            # Maintenance records indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_maintenance_vehicle_date 
                ON maintenance_records (vehicle_id, service_date)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_maintenance_type_date 
                ON maintenance_records (maintenance_type, service_date)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_maintenance_next_service 
                ON maintenance_records (next_service_date)
            """))
            
            # Vehicle specifications indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_specs_vehicle_id 
                ON vehicle_specifications (vehicle_id)
            """))
            
            # Vehicle documents indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_documents_vehicle_type 
                ON vehicle_documents (vehicle_id, document_type)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_documents_expiry 
                ON vehicle_documents (expiry_date, is_valid)
            """))
            
            conn.commit()
            
        logger.info("Database initialized successfully with custom indexes")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

# Event listeners for automatic timestamp updates
@event.listens_for(Base, 'before_update', propagate=True)
def timestamp_before_update(mapper, connection, target):
    """Automatically update the updated_at timestamp"""
    if hasattr(target, 'updated_at'):
        target.updated_at = datetime.now(timezone.utc)

def create_vehicle_activity_log():
    """Create a table for vehicle activity logging"""
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS vehicle_activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehicle_id INTEGER NOT NULL,
                    activity_type VARCHAR(100) NOT NULL,
                    description TEXT,
                    details JSON,
                    user_id INTEGER,
                    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    source_service VARCHAR(50),
                    ip_address VARCHAR(45),
                    user_agent TEXT
                )
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_activity_vehicle_id 
                ON vehicle_activity_log (vehicle_id)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_activity_type_timestamp 
                ON vehicle_activity_log (activity_type, timestamp)
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_activity_user_timestamp 
                ON vehicle_activity_log (user_id, timestamp)
            """))
            
            conn.commit()
            
        logger.info("Vehicle activity log table created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create activity log table: {e}")

async def log_vehicle_activity(
    vehicle_id: int,
    activity_type: str,
    description: Optional[str] = None,
    details: Optional[dict] = None,
    user_id: Optional[int] = None,
    source_service: str = "vehicles_service",
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """Log vehicle-related activities"""
    try:
        db = SessionLocal()
        
        log_data = {
            'vehicle_id': vehicle_id,
            'activity_type': activity_type,
            'description': description,
            'details': details,
            'user_id': user_id,
            'timestamp': datetime.now(timezone.utc),
            'source_service': source_service,
            'ip_address': ip_address,
            'user_agent': user_agent
        }
        
        # Insert log entry
        db.execute(text("""
            INSERT INTO vehicle_activity_log 
            (vehicle_id, activity_type, description, details, user_id, timestamp, source_service, ip_address, user_agent)
            VALUES (:vehicle_id, :activity_type, :description, :details, :user_id, :timestamp, :source_service, :ip_address, :user_agent)
        """), log_data)
        
        db.commit()
        logger.info(f"Activity logged: {activity_type} for vehicle {vehicle_id}")
        
    except Exception as e:
        logger.error(f"Failed to log activity: {e}")
        if db:
            db.rollback()
    finally:
        if db:
            db.close()

def get_vehicle_statistics():
    """Get overall vehicle database statistics"""
    try:
        db = SessionLocal()
        
        stats = {}
        
        # Get vehicle count by status
        result = db.execute(text("""
            SELECT is_active, COUNT(*) as count 
            FROM vehicles 
            GROUP BY is_active
        """)).fetchall()
        
        stats['vehicles_by_status'] = {row[0]: row[1] for row in result}
        
        # Get vehicle count by fuel type
        result = db.execute(text("""
            SELECT fuel_type, COUNT(*) as count 
            FROM vehicles 
            WHERE fuel_type IS NOT NULL 
            GROUP BY fuel_type
        """)).fetchall()
        
        stats['vehicles_by_fuel_type'] = {row[0]: row[1] for row in result}
        
        # Get maintenance statistics
        result = db.execute(text("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT vehicle_id) as vehicles_with_maintenance,
                AVG(cost) as avg_cost
            FROM maintenance_records
        """)).fetchone()
        
        stats['maintenance_stats'] = {
            'total_records': result[0],
            'vehicles_with_maintenance': result[1],
            'average_cost': float(result[2]) if result[2] else 0.0
        }
        
        # Get recent activity count
        result = db.execute(text("""
            SELECT COUNT(*) as recent_activities
            FROM vehicle_activity_log 
            WHERE timestamp >= datetime('now', '-7 days')
        """)).fetchone()
        
        stats['recent_activity_count'] = result[0] if result else 0
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get vehicle statistics: {e}")
        return {}
    finally:
        if db:
            db.close()

def cleanup_old_activity_logs(days: int = 90):
    """Clean up old activity logs to maintain performance"""
    try:
        db = SessionLocal()
        
        result = db.execute(text("""
            DELETE FROM vehicle_activity_log 
            WHERE timestamp < datetime('now', '-{} days')
        """.format(days)))
        
        deleted_count = result.rowcount
        db.commit()
        
        logger.info(f"Cleaned up {deleted_count} old activity log entries")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Failed to cleanup activity logs: {e}")
        return 0
    finally:
        if db:
            db.close()

# Database health check
def check_database_health():
    """Check database connectivity and basic functionality"""
    try:
        db = SessionLocal()
        
        # Test basic query
        db.execute(text("SELECT 1"))
        
        # Test table existence
        tables = ['vehicles', 'maintenance_records', 'vehicle_specifications', 'vehicle_documents']
        for table in tables:
            result = db.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()
            if result is None:
                raise Exception(f"Table {table} not accessible")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
