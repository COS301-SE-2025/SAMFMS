# User Invitation System

This document describes the OTP-based user invitation system implemented in SAMFMS.

## Overview

The invitation system allows administrators and fleet managers to invite users to join the system through a secure OTP-based registration process.

### Flow

1. **Admin/Fleet Manager sends invitation** → User receives email with OTP
2. **User opens activation link** → Enters email and OTP to verify
3. **User completes registration** → Creates username and password
4. **User account activated** → Can log in normally

## Components

### Backend Services

#### Core Service (`/auth` endpoints)

- `/auth/invite-user` - Send invitation (authenticated)
- `/auth/invitations` - Get pending invitations (authenticated)
- `/auth/resend-invitation` - Resend OTP (authenticated)
- `/auth/verify-otp` - Verify OTP (public)
- `/auth/complete-registration` - Complete registration (public)

#### Security Service (`/admin` endpoints)

- `/admin/invite-user` - Process invitation
- `/admin/pending-invitations` - List pending invitations
- `/admin/resend-invitation` - Resend OTP
- `/admin/verify-otp` - Verify OTP
- `/admin/complete-registration` - Complete user registration

### Frontend Components

#### UserManagement Component

- Updated to show invited users table
- Invitation form (no password required)
- Resend invitation functionality

#### UserActivation Component (`/activate` route)

- Step 1: Email and OTP verification
- Step 2: Username and password creation
- Handles registration completion

### Database Models

#### UserInvitation (Security Service)

```python
{
    "email": "user@example.com",
    "full_name": "User Name",
    "role": "driver",
    "phone_number": "+1234567890",
    "otp": "123456",  # 6-digit code
    "invited_by": "admin_user_id",
    "status": "invited",  # invited, activated, expired
    "created_at": "2025-01-01T00:00:00Z",
    "expires_at": "2025-01-02T00:00:00Z",  # 24 hours
    "activation_attempts": 0,
    "max_attempts": 3
}
```

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
```

### Docker Compose

The security service is configured with email environment variables:

```yaml
security_service:
  environment:
    - SMTP_SERVER=${SMTP_SERVER:-smtp.gmail.com}
    - SMTP_PORT=${SMTP_PORT:-587}
    - SMTP_USERNAME=${SMTP_USERNAME}
    - SMTP_PASSWORD=${SMTP_PASSWORD}
    - FROM_EMAIL=${FROM_EMAIL}
```

## Usage

### For Administrators

1. **Send Invitation**:

   - Go to User Management page
   - Click "Invite User"
   - Fill in user details (name, email, role, phone)
   - Click "Send Invitation"

2. **Manage Pending Invitations**:
   - View "Pending Invitations" table
   - See invitation status and expiry
   - Resend OTP if needed

### For Invited Users

1. **Receive Email**:

   - Check email for invitation with OTP
   - Note the 6-digit OTP code

2. **Activate Account**:

   - Visit: `http://your-app.com/activate`
   - Enter email and OTP
   - Choose username and password
   - Complete registration

3. **Login**:
   - Use normal login with email/username and password

## Permissions

### Admin Users

- Can invite: admin, fleet_manager, driver
- Can see all pending invitations
- Can resend any invitation

### Fleet Manager Users

- Can invite: driver only
- Can see their own sent invitations
- Can resend their own invitations

### Driver Users

- Cannot send invitations
- Cannot see pending invitations

## Security Features

- **OTP Expiry**: 24 hours from invitation
- **Attempt Limiting**: Max 3 verification attempts
- **Email Validation**: Prevents duplicate invitations
- **Role-based Access**: Fleet managers can only invite drivers
- **Secure Token Generation**: Cryptographically secure OTP

## Testing

Use the provided test script:

```bash
# Full test (requires admin credentials)
python test_invitation.py

# Test OTP verification
python test_invitation.py verify user@example.com 123456

# Test registration completion
python test_invitation.py complete user@example.com 123456 username password123
```

## API Examples

### Send Invitation

```bash
curl -X POST http://localhost:8000/auth/invite-user \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Doe",
    "email": "john@example.com",
    "role": "driver",
    "phoneNo": "+1234567890"
  }'
```

### Verify OTP

```bash
curl -X POST http://localhost:8000/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "otp": "123456"
  }'
```

### Complete Registration

```bash
curl -X POST http://localhost:8000/auth/complete-registration \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "otp": "123456",
    "username": "johndoe",
    "password": "securepassword123"
  }'
```

## Troubleshooting

### Common Issues

1. **Email not sending**: Check SMTP configuration
2. **OTP expired**: Resend invitation
3. **Invalid OTP**: Check email for correct code
4. **Permission denied**: Ensure user has invitation permissions

### Logs

Check service logs for detailed error information:

```bash
docker logs samfms-security_service-1
docker logs samfms-core_service-1
```

## Future Enhancements

- [ ] Email templates with HTML formatting
- [ ] SMS-based OTP option
- [ ] Bulk invitation import
- [ ] Custom invitation expiry times
- [ ] Invitation analytics and reporting
