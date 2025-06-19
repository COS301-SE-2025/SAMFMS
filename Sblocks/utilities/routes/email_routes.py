"""
API routes for email functionality
"""
from fastapi import APIRouter, Request, HTTPException, Depends, Body
from pydantic import BaseModel, EmailStr, Field
from typing import List, Dict, Any, Optional
import logging
from services.rabbitmq_service import rabbitmq_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/email", tags=["Email"])

# Models
class EmailRecipient(BaseModel):
    email: EmailStr
    name: str = Field(..., description="Recipient's full name")

class EmailAttachment(BaseModel):
    filename: str
    content: str = Field(..., description="Base64 encoded content")
    content_type: str = Field(default="application/octet-stream")

class EmailRequest(BaseModel):
    recipients: List[EmailRecipient]
    cc: Optional[List[EmailRecipient]] = None
    bcc: Optional[List[EmailRecipient]] = None
    subject: str
    body_html: str
    body_text: Optional[str] = None
    attachments: Optional[List[EmailAttachment]] = None
    template_id: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None

class EmailResponse(BaseModel):
    success: bool
    message: str
    email_id: Optional[str] = None

# Routes
@router.post("/send", response_model=EmailResponse)
async def send_email(email_request: EmailRequest):
    """
    Send an email using the email service
    """
    try:
        # Format the message for RabbitMQ
        primary_recipient = email_request.recipients[0]
        
        message = {
            "email_type": "custom",
            "to_email": [r.email for r in email_request.recipients],
            "full_name": primary_recipient.name,
            "subject": email_request.subject,
            "message": email_request.body_html,
            "cc": [r.email for r in email_request.cc] if email_request.cc else None,
            "bcc": [r.email for r in email_request.bcc] if email_request.bcc else None
        }
        
        # Use template if specified
        if email_request.template_id:
            message["email_type"] = email_request.template_id
            message.update(email_request.template_data or {})
        
        # Send to RabbitMQ
        success = rabbitmq_service.publish_email_request(message)
        
        if success:
            return {
                "success": True,
                "message": "Email queued successfully",
                "email_id": None  # No tracking ID in current implementation
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to queue email for delivery")
    
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise HTTPException(status_code=500, detail=f"Email service error: {str(e)}")

@router.post("/template/{template_id}", response_model=EmailResponse)
async def send_template_email(
    template_id: str,
    request: Request,
):
    """
    Send an email using a predefined template
    """
    try:
        # Get JSON data
        data = await request.json()
        
        # Validate required fields
        if "to_email" not in data or "full_name" not in data:
            raise HTTPException(status_code=400, detail="Missing required fields: to_email, full_name")
        
        # Create message with template
        message = {
            "email_type": template_id,
            "to_email": data["to_email"],
            "full_name": data["full_name"],
            **{k: v for k, v in data.items() if k not in ["email_type", "to_email", "full_name"]}
        }
        
        # Send to RabbitMQ
        success = rabbitmq_service.publish_email_request(message)
        
        if success:
            return {
                "success": True,
                "message": f"Template email '{template_id}' queued successfully",
                "email_id": None
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to queue email for delivery")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending template email: {e}")
        raise HTTPException(status_code=500, detail=f"Email service error: {str(e)}")

# List available email templates
@router.get("/templates", response_model=Dict[str, str])
async def list_templates():
    """
    Get a list of available email templates
    """
    try:
        from services.email_service import TEMPLATES
        
        # Return template IDs and descriptions
        return {
            template_id: template.get("description", template["subject"])
            for template_id, template in TEMPLATES.items()
        }
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list templates: {str(e)}")
