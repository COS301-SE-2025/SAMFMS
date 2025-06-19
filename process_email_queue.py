#!/usr/bin/env python3
"""
Email Queue Processor for Invitation System
This script processes queued invitation emails that failed to send initially
Can be run as a scheduled task or cron job
"""

import asyncio
import os
import sys
import logging
from datetime import datetime, timedelta

# Add the security service path to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'Sblocks', 'security'))

try:
    from services.invitation_service import InvitationService
    from config.database import get_database
except ImportError:
    logging.error("Could not import required modules. Make sure you're running this from the correct directory.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_queue_processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def process_email_queue():
    """Process emails in the retry queue"""
    try:
        logger.info("Starting email queue processing...")
        db = get_database()
        invitations_collection = db.invitations
        
        # Find invitations that need retry
        now = datetime.utcnow()
        pending_emails = await invitations_collection.find({
            "email_status": "pending_retry",
            "next_retry": {"$lte": now},
            "retry_count": {"$lt": 10}  # Max 10 retries
        }).to_list(100)  # Process up to 100 at a time
        
        logger.info(f"Found {len(pending_emails)} emails to retry")
        
        for invitation_doc in pending_emails:
            try:
                # Create invitation object
                from models.database_models import UserInvitation
                invitation = UserInvitation(**invitation_doc)
                
                # Attempt to send
                logger.info(f"Retrying email for {invitation.email} (attempt {invitation.retry_count + 1})")
                
                email_sent = await InvitationService._send_invitation_email_with_retry(invitation)
                
                if email_sent:
                    # Mark as sent successfully
                    await invitations_collection.update_one(
                        {"_id": invitation.id},
                        {"$set": {"email_status": "sent", "last_error": None}}
                    )
                    logger.info(f"Successfully sent email to {invitation.email}")
                else:
                    # Increment retry count and set next retry time with exponential backoff
                    retry_count = invitation.retry_count + 1
                    backoff = min(60 * (2 ** retry_count), 60 * 24)  # Max 24 hours between retries
                    
                    await invitations_collection.update_one(
                        {"_id": invitation.id},
                        {"$set": {
                            "retry_count": retry_count,
                            "next_retry": now + timedelta(minutes=backoff),
                            "last_error": "Email retry failed"
                        }}
                    )
                    
                    # After max retries, mark as permanently failed
                    if retry_count >= 10:
                        await invitations_collection.update_one(
                            {"_id": invitation.id},
                            {"$set": {"email_status": "failed"}}
                        )
                        logger.warning(f"Email for {invitation.email} permanently failed after {retry_count} attempts")
                        
                    else:
                        logger.warning(f"Email retry {retry_count} failed for {invitation.email}")
                
                # Sleep briefly between sending emails to avoid overwhelming the server
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing email queue item: {str(e)}")
        
        logger.info("✅ Email queue processing completed")
        
    except Exception as e:
        logger.error(f"❌ Email queue processing failed: {e}")
        raise

async def main():
    """Main function"""
    try:
        await process_email_queue()
        return 0
    except Exception as e:
        logger.error(f"Email queue processor failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
