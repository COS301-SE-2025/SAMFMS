"""
Startup validation service for Core
Validates dependencies and configuration before starting the service
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, List, Optional
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient
import aio_pika
from utils.exceptions import ConfigurationError, DatabaseError, MessageQueueError

logger = logging.getLogger(__name__)

class StartupValidator:
    """Validates system dependencies and configuration on startup"""
    
    def __init__(self, config):
        self.config = config
        self.validation_results = {}
        
    async def validate_all(self) -> Dict[str, any]:
        """Run all validation checks"""
        logger.info("🔍 Starting comprehensive startup validation...")
        
        validation_tasks = [
            ("Database Connection", self._validate_database()),
            ("Message Queue", self._validate_rabbitmq()),
            ("Configuration", self._validate_configuration()),
            ("Dependencies", self._validate_dependencies()),
        ]
        
        start_time = time.time()
        
        # Run validations concurrently where possible
        results = await asyncio.gather(
            *[task[1] for task in validation_tasks],
            return_exceptions=True
        )
        
        # Process results
        for i, (name, _) in enumerate(validation_tasks):
            result = results[i]
            if isinstance(result, Exception):
                self.validation_results[name] = {
                    "status": "failed",
                    "error": str(result),
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                self.validation_results[name] = result
        
        total_time = time.time() - start_time
        
        # Check overall status
        failed_validations = [
            name for name, result in self.validation_results.items() 
            if result.get("status") == "failed"
        ]
        
        overall_status = {
            "status": "passed" if not failed_validations else "failed",
            "validation_time_seconds": total_time,
            "failed_checks": failed_validations,
            "details": self.validation_results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if failed_validations:
            logger.error(f"❌ Startup validation failed. Failed checks: {', '.join(failed_validations)}")
            raise ConfigurationError(f"Startup validation failed: {', '.join(failed_validations)}")
        else:
            logger.info(f"✅ All startup validations passed in {total_time:.2f} seconds")
        
        return overall_status
    
    async def _validate_database(self) -> Dict[str, any]:
        """Validate MongoDB connection"""
        try:
            start_time = time.time()
            
            # Test connection
            client = AsyncIOMotorClient(self.config.MONGODB_URL)
            
            # Test ping with timeout
            await asyncio.wait_for(client.admin.command('ping'), timeout=10.0)
            
            # Test database access
            db = client[self.config.DATABASE_NAME]
            collections = await db.list_collection_names()
            
            # Test write operation
            test_collection = db.validation_test
            test_doc = {"timestamp": datetime.utcnow().isoformat(), "test": True}
            result = await test_collection.insert_one(test_doc)
            
            # Clean up test document
            await test_collection.delete_one({"_id": result.inserted_id})
            
            client.close()
            
            connection_time = time.time() - start_time
            
            return {
                "status": "passed",
                "connection_time_seconds": connection_time,
                "database_name": self.config.DATABASE_NAME,
                "collections_count": len(collections),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except asyncio.TimeoutError:
            raise DatabaseError("Database connection timeout - check MongoDB availability")
        except Exception as e:
            raise DatabaseError(f"Database validation failed: {str(e)}")
    
    async def _validate_rabbitmq(self) -> Dict[str, any]:
        """Validate RabbitMQ connection"""
        try:
            start_time = time.time()
            
            logger.info(f"Testing RabbitMQ connection to: {self.config.RABBITMQ_URL}")
            
            # Test connection with more specific error handling
            try:
                connection = await asyncio.wait_for(
                    aio_pika.connect_robust(self.config.RABBITMQ_URL),
                    timeout=15.0
                )
                logger.info("✅ RabbitMQ connection established")
            except asyncio.TimeoutError:
                logger.error("❌ RabbitMQ connection timeout")
                raise MessageQueueError("RabbitMQ connection timeout - check if RabbitMQ is running and accessible")
            except Exception as conn_error:
                logger.error(f"❌ RabbitMQ connection failed: {conn_error}")
                raise MessageQueueError(f"RabbitMQ connection failed: {str(conn_error)}")
            
            try:
                # Test channel creation
                channel = await connection.channel()
                logger.debug("✅ RabbitMQ channel created")
                
                # Test exchange creation
                test_exchange_name = f"validation_test_{uuid.uuid4().hex[:8]}"
                test_exchange = await channel.declare_exchange(
                    test_exchange_name,
                    aio_pika.ExchangeType.TOPIC,
                    auto_delete=True
                )
                logger.debug("✅ RabbitMQ test exchange created")
                
                # Test queue creation
                test_queue_name = f"validation_test_queue_{uuid.uuid4().hex[:8]}"
                test_queue = await channel.declare_queue(
                    test_queue_name,
                    auto_delete=True
                )
                logger.debug("✅ RabbitMQ test queue created")
                
                # Bind queue to exchange
                await test_queue.bind(test_exchange, "test.validation")
                logger.debug("✅ RabbitMQ queue bound to exchange")
                
                # Test message publish and consume
                test_message = aio_pika.Message(b"validation test")
                await test_exchange.publish(test_message, routing_key="test.validation")
                logger.debug("✅ RabbitMQ test message published")
                
                # Consume the message to empty the queue before deletion
                try:
                    async with test_queue.iterator() as queue_iter:
                        async for message in queue_iter:
                            async with message.process():
                                logger.debug("✅ RabbitMQ test message consumed")
                                break  # Only consume one message
                except Exception as consume_error:
                    logger.debug(f"⚠️ Could not consume test message: {consume_error}")
                
                # Clean up - purge queue first to ensure it's empty
                try:
                    await test_queue.purge()
                    logger.debug("✅ RabbitMQ test queue purged")
                except Exception as purge_error:
                    logger.debug(f"⚠️ Could not purge test queue: {purge_error}")
                
                try:
                    await test_queue.delete()
                    logger.debug("✅ RabbitMQ test queue deleted")
                except Exception as delete_error:
                    logger.debug(f"⚠️ Could not delete test queue: {delete_error}")
                
                try:
                    await test_exchange.delete()
                    logger.debug("✅ RabbitMQ test exchange deleted")
                except Exception as delete_error:
                    logger.debug(f"⚠️ Could not delete test exchange: {delete_error}")
                
                logger.debug("✅ RabbitMQ test resources cleanup completed")
                
            except Exception as op_error:
                logger.error(f"❌ RabbitMQ operation failed: {op_error}")
                raise MessageQueueError(f"RabbitMQ operation failed: {str(op_error)}")
            finally:
                try:
                    await connection.close()
                    logger.debug("✅ RabbitMQ connection closed")
                except Exception as close_error:
                    logger.warning(f"⚠️ Error closing RabbitMQ connection: {close_error}")
            
            connection_time = time.time() - start_time
            logger.info(f"✅ RabbitMQ validation completed in {connection_time:.2f}s")
            
            return {
                "status": "passed",
                "connection_time_seconds": connection_time,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            if isinstance(e, MessageQueueError):
                raise
            logger.error(f"❌ Unexpected RabbitMQ validation error: {e}")
            raise MessageQueueError(f"RabbitMQ validation failed: {str(e)}")
    
    async def _validate_configuration(self) -> Dict[str, any]:
        """Validate configuration values"""
        try:
            validation_errors = []
            
            # Check required configuration
            required_configs = [
                ("MONGODB_URL", self.config.MONGODB_URL),
                ("RABBITMQ_URL", self.config.RABBITMQ_URL),
                ("SECURITY_URL", self.config.SECURITY_URL),
                ("JWT_SECRET_KEY", self.config.JWT_SECRET_KEY)
            ]
            
            for name, value in required_configs:
                if not value:
                    validation_errors.append(f"{name} is not set")
            
            # Check port ranges
            if not (1000 <= self.config.CORE_PORT <= 65535):
                validation_errors.append(f"CORE_PORT {self.config.CORE_PORT} is not in valid range (1000-65535)")
            
            # Check environment values
            if self.config.ENVIRONMENT not in ['development', 'production', 'testing']:
                validation_errors.append(f"ENVIRONMENT '{self.config.ENVIRONMENT}' is not valid")
            
            if validation_errors:
                raise ConfigurationError(f"Configuration validation failed: {'; '.join(validation_errors)}")
            
            return {
                "status": "passed",
                "environment": self.config.ENVIRONMENT,
                "core_port": self.config.CORE_PORT,
                "log_level": self.config.LOG_LEVEL,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            if isinstance(e, ConfigurationError):
                raise
            raise ConfigurationError(f"Configuration validation error: {str(e)}")
    
    async def _validate_dependencies(self) -> Dict[str, any]:
        """Validate required dependencies and imports"""
        try:
            missing_deps = []
            
            # Test critical imports individually to identify specific failures
            critical_imports = [
                ("fastapi", "fastapi"),
                ("motor", "motor"),
                ("aio_pika", "aio_pika"),
                ("jwt", "pyjwt"),  # pyjwt is imported as jwt
                ("uvicorn", "uvicorn")
            ]
            
            for import_name, package_name in critical_imports:
                try:
                    __import__(import_name)
                    logger.debug(f"✅ Successfully imported {import_name}")
                except ImportError as e:
                    error_msg = f"Missing critical dependency: {package_name} (import {import_name}): {str(e)}"
                    logger.error(error_msg)
                    missing_deps.append(error_msg)
            
            # Test optional imports
            optional_deps = []
            optional_imports = [
                ("docker", "docker"),
                ("requests", "requests")
            ]
            
            for import_name, package_name in optional_imports:
                try:
                    __import__(import_name)
                    logger.debug(f"✅ Successfully imported optional dependency {import_name}")
                except ImportError:
                    logger.debug(f"⚠️ Optional dependency {package_name} not available")
                    optional_deps.append(package_name)
            
            if missing_deps:
                raise ConfigurationError(f"Missing dependencies: {'; '.join(missing_deps)}")
            
            return {
                "status": "passed",
                "missing_optional_dependencies": optional_deps,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            if isinstance(e, ConfigurationError):
                raise
            raise ConfigurationError(f"Dependency validation error: {str(e)}")

# Global validator instance
startup_validator = None

def get_startup_validator(config):
    """Get or create startup validator instance"""
    global startup_validator
    if startup_validator is None:
        startup_validator = StartupValidator(config)
    return startup_validator
