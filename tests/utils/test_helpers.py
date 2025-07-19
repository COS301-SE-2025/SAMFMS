"""
Test utilities and helpers for SAMFMS integration tests
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from unittest.mock import Mock, AsyncMock, patch
import httpx
import pytest
from faker import Faker
from motor.motor_asyncio import AsyncIOMotorClient
import aio_pika

from tests.config.test_config import get_test_config, get_test_fixtures

logger = logging.getLogger(__name__)
fake = Faker()


class TestDatabaseManager:
    """Test database management utilities"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None
    
    async def connect(self):
        """Connect to test database"""
        try:
            self.client = AsyncIOMotorClient(
                self.config["database"]["mongodb_url"],
                maxPoolSize=self.config["database"]["max_connections"],
                minPoolSize=self.config["database"]["min_connections"]
            )
            self.database = self.client[self.config["database"]["database_name"]]
            logger.info("Connected to test database")
        except Exception as e:
            logger.error(f"Failed to connect to test database: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from test database"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from test database")
    
    async def clean_database(self):
        """Clean test database"""
        if not self.database:
            return
        
        collections = await self.database.list_collection_names()
        for collection_name in collections:
            await self.database[collection_name].delete_many({})
        
        logger.info("Test database cleaned")
    
    async def seed_test_data(self):
        """Seed test database with fixtures"""
        if not self.database:
            return
        
        fixtures = get_test_fixtures()
        
        for collection_name, data in fixtures.items():
            if data:
                await self.database[collection_name].insert_many(data)
                logger.info(f"Seeded {len(data)} records to {collection_name}")
    
    async def get_collection(self, name: str):
        """Get database collection"""
        if not self.database:
            raise RuntimeError("Database not connected")
        return self.database[name]


class TestRabbitMQManager:
    """Test RabbitMQ management utilities"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchanges: Dict[str, aio_pika.Exchange] = {}
        self.queues: Dict[str, aio_pika.Queue] = {}
    
    async def connect(self):
        """Connect to test RabbitMQ"""
        try:
            rabbitmq_config = self.config["rabbitmq"]
            url = f"amqp://{rabbitmq_config['username']}:{rabbitmq_config['password']}@{rabbitmq_config['host']}:{rabbitmq_config['port']}{rabbitmq_config['virtual_host']}"
            
            self.connection = await aio_pika.connect_robust(url)
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=1)
            
            logger.info("Connected to test RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to test RabbitMQ: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from test RabbitMQ"""
        if self.connection:
            await self.connection.close()
            logger.info("Disconnected from test RabbitMQ")
    
    async def setup_exchanges_and_queues(self):
        """Set up test exchanges and queues"""
        if not self.channel:
            raise RuntimeError("RabbitMQ not connected")
        
        # Create exchange
        exchange_name = self.config["rabbitmq"]["exchange_name"]
        exchange = await self.channel.declare_exchange(
            exchange_name,
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )
        self.exchanges[exchange_name] = exchange
        
        # Create test queues
        test_queues = [
            "test_vehicle_events",
            "test_driver_events",
            "test_maintenance_events",
            "test_assignment_events"
        ]
        
        for queue_name in test_queues:
            queue = await self.channel.declare_queue(queue_name, durable=True)
            self.queues[queue_name] = queue
        
        logger.info("Set up test exchanges and queues")
    
    async def publish_test_message(self, routing_key: str, message: Dict[str, Any]):
        """Publish test message"""
        if not self.channel or not self.exchanges:
            raise RuntimeError("RabbitMQ not properly set up")
        
        exchange_name = self.config["rabbitmq"]["exchange_name"]
        exchange = self.exchanges[exchange_name]
        
        message_body = json.dumps(message).encode()
        await exchange.publish(
            aio_pika.Message(
                message_body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                headers={"timestamp": datetime.utcnow().isoformat()}
            ),
            routing_key=routing_key
        )
        
        logger.info(f"Published test message to {routing_key}")
    
    async def consume_test_messages(self, queue_name: str, callback: Callable):
        """Consume test messages"""
        if queue_name not in self.queues:
            raise RuntimeError(f"Queue {queue_name} not found")
        
        queue = self.queues[queue_name]
        await queue.consume(callback)
        
        logger.info(f"Started consuming messages from {queue_name}")
    
    async def clean_queues(self):
        """Clean test queues"""
        for queue in self.queues.values():
            await queue.purge()
        
        logger.info("Test queues cleaned")


class TestServiceManager:
    """Test service management utilities"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.services_health: Dict[str, bool] = {}
    
    async def wait_for_service(self, service_name: str, timeout: int = 30) -> bool:
        """Wait for service to be healthy"""
        service_config = self.config["services"][service_name]
        health_url = f"{service_config['base_url']}/health"
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(health_url, timeout=5)
                    if response.status_code == 200:
                        self.services_health[service_name] = True
                        logger.info(f"Service {service_name} is healthy")
                        return True
            except Exception as e:
                logger.debug(f"Service {service_name} not ready: {e}")
            
            await asyncio.sleep(1)
        
        self.services_health[service_name] = False
        logger.warning(f"Service {service_name} is not healthy after {timeout}s")
        return False
    
    async def wait_for_all_services(self, timeout: int = 60) -> bool:
        """Wait for all services to be healthy"""
        tasks = []
        for service_name in self.config["services"]:
            if service_name != "core":  # Core is the main service
                task = asyncio.create_task(self.wait_for_service(service_name, timeout))
                tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return all(result is True for result in results)
    
    def get_service_url(self, service_name: str, endpoint: str = "") -> str:
        """Get service URL"""
        service_config = self.config["services"][service_name]
        return f"{service_config['base_url']}{endpoint}"


class TestAuthManager:
    """Test authentication utilities"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.tokens: Dict[str, str] = {}
    
    async def get_test_token(self, user_type: str = "admin") -> str:
        """Get test authentication token"""
        if user_type in self.tokens:
            return self.tokens[user_type]
        
        # Mock token for testing
        test_token = f"test-token-{user_type}-{int(time.time())}"
        self.tokens[user_type] = test_token
        return test_token
    
    def get_auth_headers(self, token: str) -> Dict[str, str]:
        """Get authentication headers"""
        return {"Authorization": f"Bearer {token}"}
    
    async def authenticate_request(self, client: httpx.AsyncClient, user_type: str = "admin"):
        """Authenticate request with test token"""
        token = await self.get_test_token(user_type)
        client.headers.update(self.get_auth_headers(token))


class TestDataGenerator:
    """Test data generation utilities"""
    
    def __init__(self):
        self.fake = Faker()
    
    def generate_vehicle_data(self, **overrides) -> Dict[str, Any]:
        """Generate vehicle test data"""
        data = {
            "make": self.fake.company(),
            "model": self.fake.word().capitalize(),
            "year": self.fake.year(),
            "registration_number": f"{self.fake.lexify('???').upper()}-{self.fake.numerify('###')}-GP",
            "vin": self.fake.lexify('?????????????????'),
            "color": self.fake.color_name(),
            "fuel_type": self.fake.random_element(["Petrol", "Diesel", "Electric", "Hybrid"]),
            "engine_size": f"{self.fake.random_int(1, 5)}.{self.fake.random_int(0, 9)}L",
            "transmission": self.fake.random_element(["Manual", "Automatic"]),
            "status": "active"
        }
        data.update(overrides)
        return data
    
    def generate_driver_data(self, **overrides) -> Dict[str, Any]:
        """Generate driver test data"""
        data = {
            "first_name": self.fake.first_name(),
            "last_name": self.fake.last_name(),
            "email": self.fake.email(),
            "phone": self.fake.phone_number(),
            "license_number": f"DL-{self.fake.numerify('###')}-GP",
            "license_expiry": (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d"),
            "employee_id": f"EMP-{self.fake.numerify('###')}",
            "status": "active"
        }
        data.update(overrides)
        return data
    
    def generate_maintenance_data(self, vehicle_id: str, **overrides) -> Dict[str, Any]:
        """Generate maintenance test data"""
        data = {
            "vehicle_id": vehicle_id,
            "maintenance_type": self.fake.random_element([
                "oil_change", "tire_replacement", "brake_service", "engine_service", "transmission_service"
            ]),
            "description": self.fake.text(max_nb_chars=200),
            "scheduled_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "estimated_cost": float(self.fake.random_int(200, 2000)),
            "service_provider": self.fake.company(),
            "priority": self.fake.random_element(["low", "medium", "high"]),
            "status": "scheduled"
        }
        data.update(overrides)
        return data
    
    def generate_assignment_data(self, vehicle_id: str, driver_id: str, **overrides) -> Dict[str, Any]:
        """Generate assignment test data"""
        start_date = datetime.now() + timedelta(days=1)
        end_date = start_date + timedelta(days=7)
        
        data = {
            "vehicle_id": vehicle_id,
            "driver_id": driver_id,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "purpose": self.fake.random_element([
                "Security patrol", "Transport duty", "Maintenance run", "Emergency response"
            ]),
            "status": "active"
        }
        data.update(overrides)
        return data


class TestValidator:
    """Test validation utilities"""
    
    @staticmethod
    def validate_vehicle_data(data: Dict[str, Any]) -> bool:
        """Validate vehicle data structure"""
        required_fields = ["make", "model", "year", "registration_number", "status"]
        return all(field in data for field in required_fields)
    
    @staticmethod
    def validate_driver_data(data: Dict[str, Any]) -> bool:
        """Validate driver data structure"""
        required_fields = ["first_name", "last_name", "email", "license_number", "status"]
        return all(field in data for field in required_fields)
    
    @staticmethod
    def validate_maintenance_data(data: Dict[str, Any]) -> bool:
        """Validate maintenance data structure"""
        required_fields = ["vehicle_id", "maintenance_type", "scheduled_date", "status"]
        return all(field in data for field in required_fields)
    
    @staticmethod
    def validate_assignment_data(data: Dict[str, Any]) -> bool:
        """Validate assignment data structure"""
        required_fields = ["vehicle_id", "driver_id", "start_date", "status"]
        return all(field in data for field in required_fields)
    
    @staticmethod
    def validate_api_response(response: httpx.Response, expected_status: int = 200) -> bool:
        """Validate API response"""
        if response.status_code != expected_status:
            logger.error(f"Expected status {expected_status}, got {response.status_code}")
            return False
        
        try:
            data = response.json()
            return isinstance(data, dict)
        except json.JSONDecodeError:
            logger.error("Response is not valid JSON")
            return False


class TestFixtures:
    """Test fixtures and setup utilities"""
    
    def __init__(self):
        self.config = get_test_config()
        self.db_manager = TestDatabaseManager(self.config)
        self.rabbitmq_manager = TestRabbitMQManager(self.config)
        self.service_manager = TestServiceManager(self.config)
        self.auth_manager = TestAuthManager(self.config)
        self.data_generator = TestDataGenerator()
    
    async def setup_test_environment(self):
        """Set up complete test environment"""
        logger.info("Setting up test environment")
        
        # Connect to database
        await self.db_manager.connect()
        await self.db_manager.clean_database()
        await self.db_manager.seed_test_data()
        
        # Connect to RabbitMQ
        await self.rabbitmq_manager.connect()
        await self.rabbitmq_manager.setup_exchanges_and_queues()
        await self.rabbitmq_manager.clean_queues()
        
        # Wait for services
        await self.service_manager.wait_for_all_services()
        
        logger.info("Test environment setup complete")
    
    async def teardown_test_environment(self):
        """Tear down test environment"""
        logger.info("Tearing down test environment")
        
        # Clean up database
        await self.db_manager.clean_database()
        await self.db_manager.disconnect()
        
        # Clean up RabbitMQ
        await self.rabbitmq_manager.clean_queues()
        await self.rabbitmq_manager.disconnect()
        
        logger.info("Test environment teardown complete")


# Pytest fixtures
@pytest.fixture(scope="session")
async def test_config():
    """Test configuration fixture"""
    return get_test_config()


@pytest.fixture(scope="session")
async def test_fixtures():
    """Test fixtures fixture"""
    fixtures = TestFixtures()
    await fixtures.setup_test_environment()
    yield fixtures
    await fixtures.teardown_test_environment()


@pytest.fixture(scope="function")
async def test_client(test_config):
    """Test HTTP client fixture"""
    base_url = test_config["services"]["core"]["base_url"]
    async with httpx.AsyncClient(base_url=base_url) as client:
        yield client


@pytest.fixture(scope="function")
async def authenticated_client(test_fixtures, test_client):
    """Authenticated test client fixture"""
    await test_fixtures.auth_manager.authenticate_request(test_client)
    yield test_client


@pytest.fixture(scope="function")
def test_data_generator():
    """Test data generator fixture"""
    return TestDataGenerator()


@pytest.fixture(scope="function")
def test_validator():
    """Test validator fixture"""
    return TestValidator()


# Utility functions
def skip_if_service_unavailable(service_name: str):
    """Skip test if service is unavailable"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            config = get_test_config()
            manager = TestServiceManager(config)
            
            if not await manager.wait_for_service(service_name, timeout=5):
                pytest.skip(f"Service {service_name} is unavailable")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Retry test on failure"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (2 ** attempt))
            
            raise last_exception
        return wrapper
    return decorator


def measure_execution_time(func):
    """Measure test execution time"""
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        logger.info(f"Test {func.__name__} executed in {execution_time:.2f}s")
        
        return result
    return wrapper
