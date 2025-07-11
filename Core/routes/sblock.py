"""
Service Block (SBlock) management routes
Handles dynamic addition and removal of service blocks
"""

import logging
from fastapi import APIRouter, HTTPException
from rabbitmq.admin import addSblock, removeSblock

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sblock", tags=["SBlock Management"])

@router.get("/add/{sblock_ip}/{username}")
async def add_sblock_route(sblock_ip: str, username: str):
    """Add a new service block to the system"""
    try:
        await addSblock(username)
        logger.info(f"Successfully added SBlock {username} with IP {sblock_ip}")
        return {
            "status": "success", 
            "message": f"SBlock {username} added",
            "sblock_ip": sblock_ip,
            "username": username
        }
    except Exception as e:
        logger.error(f"Error adding SBlock {username}: {str(e)}")
        return {
            "status": "error", 
            "message": str(e),
            "sblock_ip": sblock_ip,
            "username": username
        }

@router.get("/remove/{sblock_ip}/{username}")
async def remove_sblock_route(sblock_ip: str, username: str):
    """Remove a service block from the system"""
    try:
        await removeSblock(username)
        logger.info(f"Successfully removed SBlock {username} with IP {sblock_ip}")
        return {
            "status": "success", 
            "message": f"SBlock {username} removed",
            "sblock_ip": sblock_ip,
            "username": username
        }
    except Exception as e:
        logger.error(f"Error removing SBlock {username}: {str(e)}")
        return {
            "status": "error", 
            "message": str(e),
            "sblock_ip": sblock_ip,
            "username": username
        }
