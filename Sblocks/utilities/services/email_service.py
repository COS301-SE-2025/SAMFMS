"""
Email Service for SAMFMS
Handles sending emails using SMTP and provides email templates
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
import os
from typing import List, Dict, Optional, Union

logger = logging.getLogger(__name__)

# Email configuration from environment variables with defaults
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "samfms.notifications@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_SENDER_NAME = os.getenv("EMAIL_SENDER_NAME", "SAMFMS System")

# Email Templates
TEMPLATES = {
    "welcome": {
        "subject": "Welcome to SAMFMS",
        "html": """
        <html>
            <body>
                <h2>Welcome to SAMFMS!</h2>
                <p>Hello {full_name},</p>
                <p>Your account has been created successfully.</p>
                <p>You can log in with your email address: <strong>{email}</strong></p>
                <p>Your role is: <strong>{role}</strong></p>
                <p>If you have any questions, please contact your administrator.</p>
                <p>Best regards,<br>The SAMFMS Team</p>
            </body>
        </html>
        """,
        "plain": """
Welcome to SAMFMS!

Hello {full_name},

Your account has been created successfully.
You can log in with your email address: {email}
Your role is: {role}

If you have any questions, please contact your administrator.

Best regards,
The SAMFMS Team
        """
    },
    "password_reset": {
        "subject": "Password Reset Request",
        "html": """
        <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>Hello {full_name},</p>
                <p>We received a request to reset your password.</p>
                <p>Please click <a href="{reset_link}">here</a> to reset your password, or copy and paste the following link:</p>
                <p>{reset_link}</p>
                <p>This link will expire in 24 hours.</p>
                <p>If you did not request this change, please ignore this email or contact support.</p>
                <p>Best regards,<br>The SAMFMS Team</p>
            </body>
        </html>
        """,
        "plain": """
Password Reset Request

Hello {full_name},

We received a request to reset your password.
Please use the following link to reset your password:
{reset_link}

This link will expire in 24 hours.

If you did not request this change, please ignore this email or contact support.

Best regards,
The SAMFMS Team
        """
    },
    "trip_assignment": {
        "subject": "New Trip Assignment",
        "html": """
        <html>
            <body>
                <h2>New Trip Assignment</h2>
                <p>Hello {full_name},</p>
                <p>You have been assigned to a new trip:</p>
                <ul>
                    <li><strong>Trip ID:</strong> {trip_id}</li>
                    <li><strong>Vehicle:</strong> {vehicle}</li>
                    <li><strong>Departure:</strong> {departure_time}</li>
                    <li><strong>From:</strong> {origin}</li>
                    <li><strong>To:</strong> {destination}</li>
                </ul>
                <p>Please log in to the system for full trip details.</p>
                <p>Best regards,<br>The SAMFMS Team</p>
            </body>
        </html>
        """,
        "plain": """
New Trip Assignment

Hello {full_name},

You have been assigned to a new trip:
- Trip ID: {trip_id}
- Vehicle: {vehicle}
- Departure: {departure_time}
- From: {origin}
- To: {destination}

Please log in to the system for full trip details.

Best regards,
The SAMFMS Team
        """
    },
    "vehicle_maintenance": {
        "subject": "Vehicle Maintenance Alert",
        "html": """
        <html>
            <body>
                <h2>Vehicle Maintenance Alert</h2>
                <p>Hello {full_name},</p>
                <p>This is a notification that vehicle {vehicle} is due for maintenance:</p>
                <ul>
                    <li><strong>Vehicle:</strong> {vehicle}</li>
                    <li><strong>Maintenance Type:</strong> {maintenance_type}</li>
                    <li><strong>Due Date:</strong> {due_date}</li>
                </ul>
                <p>Please ensure this maintenance is scheduled as soon as possible.</p>
                <p>Best regards,<br>The SAMFMS Team</p>
            </body>
        </html>
        """,
        "plain": """
Vehicle Maintenance Alert

Hello {full_name},

This is a notification that vehicle {vehicle} is due for maintenance:
- Vehicle: {vehicle}
- Maintenance Type: {maintenance_type}
- Due Date: {due_date}

Please ensure this maintenance is scheduled as soon as possible.

Best regards,
The SAMFMS Team
        """
    },
    "alert_notification": {
        "subject": "{alert_type} Alert",
        "html": """
        <html>
            <body>
                <h2>{alert_type} Alert</h2>
                <p>Hello {full_name},</p>
                <p><strong>Alert Details:</strong></p>
                <p>{alert_message}</p>
                <p>Time: {alert_time}</p>
                <p>Please check the system for more details.</p>
                <p>Best regards,<br>The SAMFMS Team</p>
            </body>
        </html>
        """,
        "plain": """
{alert_type} Alert

Hello {full_name},

Alert Details:
{alert_message}

Time: {alert_time}

Please check the system for more details.

Best regards,
The SAMFMS Team
        """
    },
    "custom": {
        "subject": "{subject}",
        "html": """
        <html>
            <body>
                <h2>{subject}</h2>
                <p>Hello {full_name},</p>
                <p>{message}</p>
                <p>Best regards,<br>The SAMFMS Team</p>
            </body>
        </html>
        """,
        "plain": """
{subject}

Hello {full_name},

{message}

Best regards,
The SAMFMS Team
        """
    }
}


class EmailService:
    """Service for sending emails via SMTP"""
    
    @staticmethod
    def send_email(
        to_email: Union[str, List[str]],
        template_name: str,
        template_data: Dict,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[Dict]] = None
    ) -> bool:
        """
        Send an email using a template
        
        Args:
            to_email: Recipient email or list of emails
            template_name: Name of the template to use
            template_data: Dictionary containing data to fill the template
            cc: List of CC recipients
            bcc: List of BCC recipients
            attachments: List of dictionaries with attachment info
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if not EMAIL_PASSWORD:
            logger.error("Email password not configured. Email not sent.")
            return False
            
        try:
            # Get template
            template = TEMPLATES.get(template_name, TEMPLATES["custom"])
            
            # Format subject
            subject = template["subject"].format(**template_data)
            
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{EMAIL_SENDER_NAME} <{EMAIL_ADDRESS}>"
            
            # Handle multiple recipients
            if isinstance(to_email, list):
                msg["To"] = ", ".join(to_email)
            else:
                msg["To"] = to_email
                
            # Handle CC
            if cc:
                msg["Cc"] = ", ".join(cc)
                
            # Format body
            plain_text = template["plain"].format(**template_data)
            html_text = template["html"].format(**template_data)
            
            # Attach parts
            part1 = MIMEText(plain_text, "plain")
            part2 = MIMEText(html_text, "html")
            msg.attach(part1)
            msg.attach(part2)
            
            # TODO: Implement attachment handling if needed
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls(context=context)
                server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                
                # Get all recipients
                all_recipients = []
                if isinstance(to_email, list):
                    all_recipients.extend(to_email)
                else:
                    all_recipients.append(to_email)
                if cc:
                    all_recipients.extend(cc)
                if bcc:
                    all_recipients.extend(bcc)
                    
                server.sendmail(EMAIL_ADDRESS, all_recipients, msg.as_string())
                
            logger.info(f"Email sent successfully to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    @staticmethod
    def send_welcome_email(to_email: str, full_name: str, email: str, role: str) -> bool:
        """Send a welcome email to a new user"""
        template_data = {
            "full_name": full_name,
            "email": email,
            "role": role
        }
        return EmailService.send_email(to_email, "welcome", template_data)
    
    @staticmethod
    def send_password_reset(to_email: str, full_name: str, reset_link: str) -> bool:
        """Send a password reset email"""
        template_data = {
            "full_name": full_name,
            "reset_link": reset_link
        }
        return EmailService.send_email(to_email, "password_reset", template_data)

    @staticmethod
    def send_trip_assignment(to_email: str, full_name: str, trip_data: Dict) -> bool:
        """Send trip assignment notification"""
        return EmailService.send_email(to_email, "trip_assignment", {
            "full_name": full_name,
            **trip_data
        })
    
    @staticmethod
    def send_maintenance_alert(to_email: str, full_name: str, maintenance_data: Dict) -> bool:
        """Send vehicle maintenance alert"""
        return EmailService.send_email(to_email, "vehicle_maintenance", {
            "full_name": full_name,
            **maintenance_data
        })
    
    @staticmethod
    def send_alert_notification(to_email: str, full_name: str, alert_data: Dict) -> bool:
        """Send general alert notification"""
        alert_data["alert_time"] = alert_data.get("alert_time", 
                                                datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return EmailService.send_email(to_email, "alert_notification", {
            "full_name": full_name,
            **alert_data
        })
    
    @staticmethod
    def send_custom_email(to_email: str, full_name: str, subject: str, message: str) -> bool:
        """Send a custom email"""
        template_data = {
            "full_name": full_name,
            "subject": subject,
            "message": message
        }
        return EmailService.send_email(to_email, "custom", template_data)
