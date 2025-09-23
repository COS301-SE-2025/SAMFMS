#!/usr/bin/env python3
"""
Create Sample Violation Data
Generates sample violation records for driver behavior analytics
"""

import asyncio
import random
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
from bson import ObjectId

# Database configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://mongodb:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "samfms")

async def create_sample_violations():
    """Create sample violation data for analytics testing"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    print("🚀 Creating sample violation data...")
    
    # Sample driver IDs (you may need to adjust these based on your actual data)
    driver_ids = [
        "66e6c7bc8e1a2b3456789012",
        "66e6c7bc8e1a2b3456789013", 
        "66e6c7bc8e1a2b3456789014",
        "66e6c7bc8e1a2b3456789015",
        "66e6c7bc8e1a2b3456789016"
    ]
    
    # Generate date range for past 90 days
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=90)
    
    violations_created = 0
    
    # Create speed violations
    speed_violations = []
    for _ in range(30):
        violation_date = start_date + timedelta(
            days=random.randint(0, 90),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        speed_violations.append({
            "_id": ObjectId(),
            "driver_id": random.choice(driver_ids),
            "speed": random.randint(85, 140),  # Actual speed
            "speed_limit": random.randint(60, 100),  # Speed limit
            "location": {
                "latitude": -25.7461 + random.uniform(-0.1, 0.1),
                "longitude": 28.1881 + random.uniform(-0.1, 0.1),
                "address": f"Test Location {random.randint(1, 100)}"
            },
            "created_at": violation_date,
            "severity": random.uniform(0.3, 1.0)
        })
    
    if speed_violations:
        await db.speed_violations.insert_many(speed_violations)
        violations_created += len(speed_violations)
        print(f"✅ Created {len(speed_violations)} speed violations")
    
    # Create braking violations
    braking_violations = []
    for _ in range(15):
        violation_date = start_date + timedelta(
            days=random.randint(0, 90),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        braking_violations.append({
            "_id": ObjectId(),
            "driver_id": random.choice(driver_ids),
            "deceleration": random.uniform(6.0, 12.0),  # m/s²
            "threshold": random.uniform(4.0, 6.0),  # Threshold
            "location": {
                "latitude": -25.7461 + random.uniform(-0.1, 0.1),
                "longitude": 28.1881 + random.uniform(-0.1, 0.1),
                "address": f"Test Location {random.randint(1, 100)}"
            },
            "created_at": violation_date,
            "severity": random.uniform(0.4, 0.9)
        })
    
    if braking_violations:
        await db.excessive_braking_violations.insert_many(braking_violations)
        violations_created += len(braking_violations)
        print(f"✅ Created {len(braking_violations)} braking violations")
    
    # Create acceleration violations
    acceleration_violations = []
    for _ in range(12):
        violation_date = start_date + timedelta(
            days=random.randint(0, 90),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        acceleration_violations.append({
            "_id": ObjectId(),
            "driver_id": random.choice(driver_ids),
            "acceleration": random.uniform(3.0, 6.0),  # m/s²
            "threshold": random.uniform(2.0, 3.0),  # Threshold
            "location": {
                "latitude": -25.7461 + random.uniform(-0.1, 0.1),
                "longitude": 28.1881 + random.uniform(-0.1, 0.1),
                "address": f"Test Location {random.randint(1, 100)}"
            },
            "created_at": violation_date,
            "severity": random.uniform(0.3, 0.8)
        })
    
    if acceleration_violations:
        await db.excessive_acceleration_violations.insert_many(acceleration_violations)
        violations_created += len(acceleration_violations)
        print(f"✅ Created {len(acceleration_violations)} acceleration violations")
    
    # Create phone usage violations
    phone_violations = []
    for _ in range(8):
        violation_date = start_date + timedelta(
            days=random.randint(0, 90),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        duration = random.randint(30, 300)  # 30 seconds to 5 minutes
        
        phone_violations.append({
            "_id": ObjectId(),
            "driver_id": random.choice(driver_ids),
            "duration_seconds": duration,
            "start_time": violation_date,
            "end_time": violation_date + timedelta(seconds=duration),
            "start_location": {
                "latitude": -25.7461 + random.uniform(-0.1, 0.1),
                "longitude": 28.1881 + random.uniform(-0.1, 0.1),
                "address": f"Test Location {random.randint(1, 100)}"
            },
            "created_at": violation_date,
            "severity": random.uniform(0.5, 1.0)
        })
    
    if phone_violations:
        await db.phone_usage_violations.insert_many(phone_violations)
        violations_created += len(phone_violations)
        print(f"✅ Created {len(phone_violations)} phone usage violations")
    
    # Create some driver history records
    driver_history = []
    for driver_id in driver_ids:
        # Count violations for this driver
        speed_count = len([v for v in speed_violations if v["driver_id"] == driver_id])
        braking_count = len([v for v in braking_violations if v["driver_id"] == driver_id])
        acceleration_count = len([v for v in acceleration_violations if v["driver_id"] == driver_id])
        phone_count = len([v for v in phone_violations if v["driver_id"] == driver_id])
        total_violations = speed_count + braking_count + acceleration_count + phone_count
        
        # Calculate safety score (higher violations = lower score)
        base_score = 100
        penalty = total_violations * random.uniform(3, 8)
        safety_score = max(30, base_score - penalty)
        
        driver_history.append({
            "_id": ObjectId(),
            "driver_id": driver_id,
            "driver_name": f"Driver {driver_id[-4:]}",
            "safety_score": round(safety_score, 1),
            "driver_safety_score": round(safety_score, 1),
            "total_violations": total_violations,
            "total_trips": random.randint(50, 200),
            "completed_trips": random.randint(45, 190),
            "recent_violations": max(0, total_violations - random.randint(0, 5)),
            "historical_violations": total_violations + random.randint(0, 10),
            "trend": random.choice(["improving", "neutral", "declining"]),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
    
    if driver_history:
        await db.driver_history.insert_many(driver_history)
        print(f"✅ Created {len(driver_history)} driver history records")
    
    print(f"\n🎉 Successfully created {violations_created} total violations!")
    print(f"📊 Breakdown:")
    print(f"   🚗 Speed violations: {len(speed_violations)}")
    print(f"   🛑 Braking violations: {len(braking_violations)}")
    print(f"   🏃 Acceleration violations: {len(acceleration_violations)}")
    print(f"   📱 Phone usage violations: {len(phone_violations)}")
    print(f"   👥 Driver history records: {len(driver_history)}")
    
    # Close database connection
    client.close()
    
    return violations_created

if __name__ == "__main__":
    asyncio.run(create_sample_violations())