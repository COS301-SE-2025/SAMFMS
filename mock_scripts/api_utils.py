"""
Utility functions for making API calls to SAMFMS services
"""

import aiohttp
import asyncio
import json
import logging
import getpass
from typing import Dict, Any, Optional, List
from datetime import datetime
import time

from config import (
    CORE_BASE_URL, 
    MAINTENANCE_BASE_URL,
    DEFAULT_HEADERS, 
    DELAY_BETWEEN_REQUESTS,
    LOGIN_EMAIL,
    LOGIN_PASSWORD
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AuthenticationManager:
    """Handles authentication and token management"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.token = None
        self.user_info = None
        
    async def login(self, email: str = None, password: str = None) -> bool:
        """Login and obtain authentication token"""
        try:
            # Use provided credentials or defaults
            login_email = email or LOGIN_EMAIL
            login_password = password or LOGIN_PASSWORD
            
            # Prompt for password if not provided
            if not login_password:
                login_password = getpass.getpass(f"Enter password for {login_email}: ")
            
            login_data = {
                "email": login_email,
                "password": login_password
            }
            
            logger.info(f"🔐 Attempting login for {login_email}...")
            
            async with aiohttp.ClientSession() as session:
                # Try login endpoint
                login_url = f"{self.base_url}/auth/login"
                
                async with session.post(login_url, json=login_data) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        try:
                            result = json.loads(response_text)
                            
                            # Extract token from response
                            if "token" in result:
                                self.token = result["token"]
                            elif "data" in result and "token" in result["data"]:
                                self.token = result["data"]["token"]
                            elif "access_token" in result:
                                self.token = result["access_token"]
                            else:
                                logger.error("No token found in login response")
                                return False
                            
                            # Extract user info if available
                            if "user" in result:
                                self.user_info = result["user"]
                            elif "data" in result and "user" in result["data"]:
                                self.user_info = result["data"]["user"]
                            
                            logger.info(f"✅ Login successful for {login_email}")
                            return True
                            
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON response from login: {response_text}")
                            return False
                    else:
                        logger.error(f"Login failed with status {response.status}: {response_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error during login: {e}")
            return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get headers with authentication token"""
        headers = DEFAULT_HEADERS.copy()
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers


# Global authentication manager instances
_core_auth = None
_maintenance_auth = None


async def get_authenticated_headers(service_url: str) -> Dict[str, str]:
    """Get authenticated headers for a service"""
    global _core_auth, _maintenance_auth
    
    if service_url == CORE_BASE_URL:
        if not _core_auth:
            _core_auth = AuthenticationManager(CORE_BASE_URL)
            success = await _core_auth.login()
            if not success:
                raise Exception("Failed to authenticate with Core service")
        return _core_auth.get_auth_headers()
    
    elif service_url == MAINTENANCE_BASE_URL:
        if not _maintenance_auth:
            _maintenance_auth = AuthenticationManager(MAINTENANCE_BASE_URL)
            success = await _maintenance_auth.login()
            if not success:
                raise Exception("Failed to authenticate with Maintenance service")
        return _maintenance_auth.get_auth_headers()
    
    else:
        return DEFAULT_HEADERS.copy()


class APIClient:
    """Async HTTP client for making API calls with rate limiting and authentication"""
    
    def __init__(self, base_url: str, headers: Dict[str, str] = None):
        self.base_url = base_url.rstrip('/')
        self.headers = headers or DEFAULT_HEADERS.copy()
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_time = 0
        self._authenticated = False
        
    async def __aenter__(self):
        """Async context manager entry"""
        # Get authenticated headers
        try:
            auth_headers = await get_authenticated_headers(self.base_url)
            self.headers.update(auth_headers)
            self._authenticated = True
            logger.debug(f"Authenticated headers obtained for {self.base_url}")
        except Exception as e:
            logger.warning(f"Authentication failed for {self.base_url}: {e}")
            # Continue without authentication for now
        
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
            
    async def _rate_limit(self):
        """Implement rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < DELAY_BETWEEN_REQUESTS:
            wait_time = DELAY_BETWEEN_REQUESTS - time_since_last
            logger.debug(f"Rate limiting: waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)
            
        self.last_request_time = time.time()
        
    async def request(self, method: str, endpoint: str, data: Dict[str, Any] = None, 
                     params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make an HTTP request with rate limiting and authentication"""
        await self._rate_limit()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            logger.info(f"Making {method} request to {url}")
            
            async with self.session.request(
                method=method,
                url=url,
                json=data,
                params=params
            ) as response:
                response_text = await response.text()
                
                if response.status == 401:
                    logger.warning(f"Authentication failed for {url}. Attempting to re-authenticate...")
                    
                    # Try to refresh authentication
                    global _core_auth, _maintenance_auth
                    if self.base_url == CORE_BASE_URL and _core_auth:
                        success = await _core_auth.login()
                        if success:
                            # Update headers and retry
                            self.headers.update(_core_auth.get_auth_headers())
                            logger.info("Re-authentication successful, retrying request...")
                            
                            # Retry the request with new token
                            async with self.session.request(
                                method=method,
                                url=url,
                                json=data,
                                params=params
                            ) as retry_response:
                                retry_text = await retry_response.text()
                                
                                if retry_response.status >= 400:
                                    logger.error(f"HTTP {retry_response.status} error after re-auth for {url}: {retry_text}")
                                    return {
                                        "error": True,
                                        "status_code": retry_response.status,
                                        "message": retry_text
                                    }
                                
                                try:
                                    result = json.loads(retry_text)
                                    logger.info(f"✅ {method} {url} - Success (after re-auth)")
                                    return result
                                except json.JSONDecodeError:
                                    return {"success": True, "data": retry_text}
                    
                    # If re-auth failed or not applicable, return error
                    return {
                        "error": True,
                        "status_code": response.status,
                        "message": "Authentication failed. Please check your credentials."
                    }
                elif response.status >= 400:
                    logger.error(f"HTTP {response.status} error for {url}: {response_text}")
                    return {
                        "error": True,
                        "status_code": response.status,
                        "message": response_text
                    }
                
                try:
                    result = json.loads(response_text)
                    logger.info(f"✅ {method} {url} - Success")
                    return result
                except json.JSONDecodeError:
                    logger.warning(f"Non-JSON response from {url}: {response_text}")
                    return {"success": True, "data": response_text}
                    
        except asyncio.TimeoutError:
            logger.error(f"Timeout for {method} {url}")
            return {"error": True, "message": "Request timeout"}
        except Exception as e:
            logger.error(f"Error making request to {url}: {e}")
            return {"error": True, "message": str(e)}
            
    async def get(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a GET request"""
        return await self.request("GET", endpoint, params=params)
        
    async def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a POST request"""
        return await self.request("POST", endpoint, data=data)
        
    async def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a PUT request"""
        return await self.request("PUT", endpoint, data=data)
        
    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make a DELETE request"""
        return await self.request("DELETE", endpoint)


class CoreServiceClient:
    """Client for Core service API calls"""
    
    def __init__(self):
        self.client = APIClient(CORE_BASE_URL)
        
    async def __aenter__(self):
        await self.client.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)
        
    # User management
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user"""
        return await self.client.post("/auth/create-user", user_data)
    
    async def create_driver(self, driver_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new driver using Management service endpoint (same as frontend)"""
        return await self.client.post("/management/drivers", driver_data)
        
    async def get_users(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get list of users"""
        return await self.client.get("/auth/users", params)

    # Vehicle management
    async def create_vehicle(self, vehicle_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new vehicle"""
        return await self.client.post("/management/vehicles", vehicle_data)
        
    async def get_vehicles(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get list of vehicles"""
        return await self.client.get("/management/vehicles", params)
        
    # Organization management
    async def create_organization(self, org_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new organization"""
        return await self.client.post("/organizations", org_data)
        
    async def get_organizations(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get list of organizations"""
        return await self.client.get("/organizations", params)


class MaintenanceServiceClient:
    """Client for Maintenance service API calls"""
    
    def __init__(self):
        self.client = APIClient(MAINTENANCE_BASE_URL)
        
    async def __aenter__(self):
        await self.client.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)
        
    # Maintenance records
    async def create_maintenance_record(self, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a maintenance record"""
        return await self.client.post("/maintenance/records", record_data)
        
    async def get_maintenance_records(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get maintenance records"""
        return await self.client.get("/maintenance/records", params)
        
    # License records
    async def create_license_record(self, license_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a license record"""
        return await self.client.post("/maintenance/licenses", license_data)
        
    async def get_license_records(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get license records"""
        return await self.client.get("/maintenance/licenses", params)
        
    # Maintenance schedules
    async def create_maintenance_schedule(self, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a maintenance schedule"""
        return await self.client.post("/maintenance/schedules", schedule_data)
        
    async def get_maintenance_schedules(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get maintenance schedules"""
        return await self.client.get("/maintenance/schedules", params)


async def batch_create_with_delay(client_method, data_list: List[Dict[str, Any]], 
                                 batch_size: int = 5) -> List[Dict[str, Any]]:
    """Create multiple records in batches with delays"""
    results = []
    
    for i in range(0, len(data_list), batch_size):
        batch = data_list[i:i + batch_size]
        batch_results = []
        
        logger.info(f"Processing batch {i//batch_size + 1}: {len(batch)} items")
        
        for item in batch:
            result = await client_method(item)
            batch_results.append(result)
            
        results.extend(batch_results)
        
        # Extra delay between batches to avoid token expiration
        if i + batch_size < len(data_list):
            logger.info(f"Batch complete. Waiting before next batch...")
            await asyncio.sleep(2.0)  # 2 second delay between batches
            
    return results


def extract_id_from_response(response: Dict[str, Any]) -> Optional[str]:
    """Extract ID from API response"""
    if response.get("error"):
        return None
        
    # Check for user_id at root level (Core service format)
    if "user_id" in response:
        return str(response["user_id"])
    
    # Check for id at root level
    if "id" in response:
        return str(response["id"])
    
    # Try different response formats in data object
    data = response.get("data", {})
    
    # Direct ID field in data
    if "id" in data:
        return str(data["id"])
        
    # user_id in data
    if "user_id" in data:
        return str(data["user_id"])
        
    # Nested in object
    for key in ["user", "vehicle", "organization", "maintenance_record", "license", "schedule"]:
        if key in data and "id" in data[key]:
            return str(data[key]["id"])
        if key in response and "id" in response[key]:
            return str(response[key]["id"])
            
    # MongoDB _id field
    if "_id" in data:
        return str(data["_id"])
    if "_id" in response:
        return str(response["_id"])
        
    return None


def log_creation_result(item_type: str, response: Dict[str, Any], item_name: str = ""):
    """Log the result of a creation operation"""
    if response.get("error"):
        logger.error(f"❌ Failed to create {item_type} {item_name}: {response.get('message', 'Unknown error')}")
    else:
        item_id = extract_id_from_response(response)
        if item_id:
            logger.info(f"✅ Created {item_type} {item_name} with ID: {item_id}")
        else:
            logger.info(f"✅ Created {item_type} {item_name}")
    return response
