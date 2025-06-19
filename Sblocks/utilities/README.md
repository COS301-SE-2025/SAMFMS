# Email Service Documentation

The SAMFMS Email Service provides a reliable way to send emails through the system using RabbitMQ messaging. This document explains how to integrate with and use the email service from other microservices.

## Overview

The Email Service is implemented as part of the Utilities Sblock and handles:

1. Sending transactional emails (welcome, password reset, notifications, etc.)
2. Supporting HTML and plain text formats
3. Using templates for consistent email formatting
4. Asynchronous email delivery via RabbitMQ

## Integration Methods

There are two ways to integrate with the Email Service:

### 1. Via the Email Client

The recommended approach is to use the provided Email Client library:

```python
from utilities.clients.email_client import email_client

# Connect to RabbitMQ
email_client.connect()

# Send a welcome email
email_client.send_welcome_email(
    to_email="user@example.com",
    full_name="John Doe",
    email="user@example.com",
    role="driver"
)

# Send a password reset email
email_client.send_password_reset(
    to_email="user@example.com",
    full_name="John Doe",
    reset_link="https://samfms.co.za/reset-password?token=abc123"
)

# Send a trip assignment notification
trip_data = {
    "trip_id": "T123456",
    "vehicle": "Toyota Hilux (ABC 123 GP)",
    "departure_time": "2025-06-18 09:00",
    "origin": "Johannesburg",
    "destination": "Pretoria"
}
email_client.send_trip_assignment(
    to_email="driver@example.com",
    full_name="Driver Name",
    trip_data=trip_data
)

# Send a custom email
email_client.send_custom_email(
    to_email="user@example.com",
    full_name="John Doe",
    subject="Important Notification",
    message="This is an important notification about your account."
)

# Close the connection when done
email_client.close()
```

### 2. Via Direct RabbitMQ Integration

For services that can't import the client library, you can send messages directly to RabbitMQ:

```python
import json
import pika

# Connect to RabbitMQ
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host="rabbitmq")
)
channel = connection.channel()

# Declare exchange
channel.exchange_declare(
    exchange="samfms_notifications",
    exchange_type="topic",
    durable=True
)

# Create message
message = {
    "email_type": "welcome",
    "to_email": "user@example.com",
    "full_name": "John Doe",
    "email": "user@example.com",
    "role": "driver"
}

# Publish message
channel.basic_publish(
    exchange="samfms_notifications",
    routing_key="email.send",
    body=json.dumps(message),
    properties=pika.BasicProperties(
        delivery_mode=2,  # make message persistent
        content_type="application/json"
    )
)

# Close connection
connection.close()
```

### 3. Via REST API

For services that don't have RabbitMQ access, you can use the REST API:

```python
import requests
import json

# Send a custom email
response = requests.post(
    "http://utilities_service:8000/api/email/send",
    json={
        "recipients": [
            {"email": "user@example.com", "name": "John Doe"}
        ],
        "subject": "Important Notification",
        "body_html": "<h1>Important Notice</h1><p>This is an important notification.</p>",
        "body_text": "Important Notice\n\nThis is an important notification."
    }
)

# Send a template email
response = requests.post(
    "http://utilities_service:8000/api/email/template/welcome",
    json={
        "to_email": "user@example.com",
        "full_name": "John Doe",
        "email": "user@example.com",
        "role": "driver"
    }
)
```

## Available Email Templates

The following email templates are available:

1. **welcome** - Welcome message for new users

   - Required fields: `to_email`, `full_name`, `email`, `role`

2. **password_reset** - Password reset instructions

   - Required fields: `to_email`, `full_name`, `reset_link`

3. **trip_assignment** - Trip assignment notification

   - Required fields: `to_email`, `full_name`, `trip_data` (object with trip_id, vehicle, departure_time, origin, destination)

4. **vehicle_maintenance** - Vehicle maintenance alerts

   - Required fields: `to_email`, `full_name`, `maintenance_data` (object with vehicle, maintenance_type, due_date)

5. **alert_notification** - General system alerts

   - Required fields: `to_email`, `full_name`, `alert_data` (object with alert_type, alert_message, alert_time)

6. **custom** - Generic email with custom subject and message
   - Required fields: `to_email`, `full_name`, `subject`, `message`

## Configuration

The Email Service requires the following environment variables to be set:

- `SMTP_SERVER` - SMTP server address (default: smtp.gmail.com)
- `SMTP_PORT` - SMTP server port (default: 587)
- `EMAIL_ADDRESS` - Sender email address
- `EMAIL_PASSWORD` - Sender email password
- `EMAIL_SENDER_NAME` - Sender name (default: "SAMFMS System")

These can be set in the docker-compose.yml file or passed as environment variables.

## Troubleshooting

If emails are not being sent, check the following:

1. Verify RabbitMQ is running and accessible
2. Check the email service logs for error messages
3. Ensure correct SMTP credentials are provided
4. Verify the RabbitMQ exchange and queues exist

For detailed logs, check the log files in the `logs` directory of the utilities service.
