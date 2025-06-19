#!/usr/bin/env python3
"""
Invitation cleanup scheduler
This script should be run periodically to clean up expired invitations
Can be added to cron or task scheduler
"""

import asyncio
import os
import sys
import logging
from datetime import datetime

# Add the security service path to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'Sblocks', 'security'))

try:
    from services.invitation_service import InvitationService
except ImportError:
    logging.error("Could not import InvitationService. Make sure you're running this from the correct directory.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('invitation_cleanup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def run_cleanup():
    """Run the invitation cleanup process"""
    try:
        logger.info("Starting invitation cleanup process...")
        await InvitationService.cleanup_expired_invitations()
        logger.info("✅ Cleanup process completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Cleanup process failed: {e}")
        raise

async def main():
    """Main function"""
    try:
        await run_cleanup()
        return 0
    except Exception as e:
        logger.error(f"Cleanup script failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
