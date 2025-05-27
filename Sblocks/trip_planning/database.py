# Database configuration for Trip Planning Service
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import os

class TripPlanningDatabase:
    client: Optional[AsyncIOMotorClient] = None
    database = None

    @classmethod
    async def connect_to_mongo(cls):
        """Create database connection"""
        mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        cls.client = AsyncIOMotorClient(mongo_url)
        cls.database = cls.client.trip_planning_db
        
        # Test connection
        try:
            await cls.client.admin.command('ping')
            print("Successfully connected to MongoDB")
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")

    @classmethod
    async def close_mongo_connection(cls):
        """Close database connection"""
        if cls.client:
            cls.client.close()

    @classmethod
    def get_database(cls):
        """Get database instance"""
        return cls.database

    @classmethod
    def get_collection(cls, collection_name: str):
        """Get specific collection"""
        return cls.database[collection_name]

# Collections
def get_trips_collection():
    return TripPlanningDatabase.get_collection("trips")

def get_routes_collection():
    return TripPlanningDatabase.get_collection("routes")

def get_schedules_collection():
    return TripPlanningDatabase.get_collection("schedules")

def get_vehicles_collection():
    return TripPlanningDatabase.get_collection("vehicles")

def get_drivers_collection():
    return TripPlanningDatabase.get_collection("drivers")

def get_locations_collection():
    return TripPlanningDatabase.get_collection("locations")

def get_trip_templates_collection():
    return TripPlanningDatabase.get_collection("trip_templates")

# Initialization and cleanup functions
init_database = TripPlanningDatabase.connect_to_mongo
close_database = TripPlanningDatabase.close_mongo_connection
