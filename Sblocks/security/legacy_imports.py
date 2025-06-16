# Backward compatibility imports
# This file maintains compatibility with existing imports while using the new structure

# Models - maintain old import paths
from models import *

# Auth utilities - maintain old import paths  
from utils.auth_utils import *

# Database functions - maintain old import paths
from config.database import (
    security_users_collection, sessions_collection, audit_logs_collection, 
    blacklisted_tokens_collection, test_database_connection, create_indexes, 
    cleanup_expired_sessions
)

# Legacy database functions that were in database.py
from repositories.audit_repository import AuditRepository, TokenRepository

async def log_security_event(user_id: str, action: str, details: dict = None):
    """Legacy function - redirects to new repository"""
    return await AuditRepository.log_security_event(user_id, action, details)

async def blacklist_token(token_hash: str, expires_at, user_id: str = None):
    """Legacy function - redirects to new repository"""
    return await TokenRepository.blacklist_token(token_hash, expires_at)

async def is_token_blacklisted(token_hash: str) -> bool:
    """Legacy function - redirects to new repository"""
    return await TokenRepository.is_token_blacklisted(token_hash)

async def blacklist_all_user_tokens(user_id: str):
    """Legacy function - redirects to new repository"""
    return await TokenRepository.blacklist_all_user_tokens(user_id)

async def get_security_metrics():
    """Legacy function - redirects to new repository"""
    return await AuditRepository.get_security_metrics()

# Additional legacy functions that might be needed
async def get_user_preferences(user_id: str):
    """Get user preferences - legacy function"""
    from repositories.user_repository import UserRepository
    user = await UserRepository.find_by_user_id(user_id)
    return user.get("preferences", {}) if user else {}

# Settings - maintain old import style
from config.settings import settings
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS
LOGIN_ATTEMPT_LIMIT = settings.LOGIN_ATTEMPT_LIMIT
DEFAULT_FIRST_USER_ROLE = settings.DEFAULT_FIRST_USER_ROLE
