#!/usr/bin/env python3
"""
Database migration script for user invitation system improvements
This script creates indexes and ensures data integrity for the invitation system
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = "samfms"

async def create_invitation_indexes():
    """Create indexes for the invitations collection"""
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        invitations_collection = db.invitations
        
        logger.info("Creating indexes for invitations collection...")
        
        # Create indexes
        indexes = [
            # Unique index on email for pending invitations
            {
                "keys": [("email", 1), ("status", 1)],
                "name": "email_status_unique",
                "unique": True,
                "partialFilterExpression": {"status": "invited"}
            },
            # Index for finding invitations by email
            {
                "keys": [("email", 1)],
                "name": "email_index"
            },
            # Index for finding invitations by status
            {
                "keys": [("status", 1)],
                "name": "status_index"
            },
            # Index for finding expired invitations
            {
                "keys": [("expires_at", 1)],
                "name": "expires_at_index"
            },
            # Index for finding invitations by invited_by user
            {
                "keys": [("invited_by", 1)],
                "name": "invited_by_index"
            },
            # Compound index for fleet manager queries
            {
                "keys": [("invited_by", 1), ("role", 1), ("status", 1)],
                "name": "invited_by_role_status_index"
            },
            # Index for cleanup operations
            {
                "keys": [("created_at", 1), ("status", 1)],
                "name": "created_at_status_index"
            }
        ]
        
        for index in indexes:
            try:
                await invitations_collection.create_index(
                    index["keys"],
                    name=index["name"],
                    unique=index.get("unique", False),
                    partialFilterExpression=index.get("partialFilterExpression")
                )
                logger.info(f"✅ Created index: {index['name']}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info(f"⚠️  Index already exists: {index['name']}")
                else:
                    logger.error(f"❌ Failed to create index {index['name']}: {e}")
        
        # List all indexes
        logger.info("Current indexes in invitations collection:")
        async for index in invitations_collection.list_indexes():
            logger.info(f"  - {index['name']}: {index.get('key', 'N/A')}")
        
        client.close()
        logger.info("✅ Database migration completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Database migration failed: {e}")
        raise

async def cleanup_invalid_invitations():
    """Clean up any invalid invitations"""
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        invitations_collection = db.invitations
        
        logger.info("Cleaning up invalid invitations...")
        
        # Mark expired invitations
        now = datetime.utcnow()
        result = await invitations_collection.update_many(
            {
                "status": "invited",
                "expires_at": {"$lt": now}
            },
            {"$set": {"status": "expired"}}
        )
        logger.info(f"✅ Marked {result.modified_count} invitations as expired")
        
        # Add missing fields to existing invitations
        update_result = await invitations_collection.update_many(
            {"resend_count": {"$exists": False}},
            {
                "$set": {
                    "resend_count": 0,
                    "max_resends": 5,
                    "activation_attempts": 0,
                    "max_attempts": 3
                }
            }
        )
        logger.info(f"✅ Updated {update_result.modified_count} invitations with missing fields")
        
        # Convert email addresses to lowercase for consistency
        async for invitation in invitations_collection.find({}):
            if invitation.get("email"):
                email = invitation["email"]
                if email != email.lower():
                    await invitations_collection.update_one(
                        {"_id": invitation["_id"]},
                        {"$set": {"email": email.lower()}}
                    )
                    logger.info(f"✅ Normalized email case: {email} -> {email.lower()}")
        
        client.close()
        logger.info("✅ Cleanup completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")
        raise

async def main():
    """Run the database migration"""
    logger.info("Starting SAMFMS invitation system database migration...")
    
    try:
        await create_invitation_indexes()
        await cleanup_invalid_invitations()
        logger.info("🎉 Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"💥 Migration failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
