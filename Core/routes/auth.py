from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from typing import Dict, List, Optional
from rabbitmq.producer import publish_message
import logging
import requests
import os
import aio_pika
from .service_routing import SERVICE_BLOCKS


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Define the URL for the Security Sblock
SECURITY_URL = os.getenv("SECURITY_URL", "http://security_service:8000")

# Models to mirror the ones in security service
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SignupRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: Optional[str] = None
    phoneNo: Optional[str] = None
    details: Dict = {}
    preferences: Dict = {}

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    role: str
    permissions: List[str]
    preferences: Dict = {}

class ProfileUpdateRequest(BaseModel):
    phoneNo: Optional[str] = None
    full_name: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class PreferencesUpdateRequest(BaseModel):
    preferences: Dict

class CreateUserRequest(BaseModel):
    """Admin can manually create users without invitation flow"""
    full_name: str 
    email: EmailStr
    role: str
    password: str
    phoneNo: Optional[str] = None
    details: Dict = {}

class RemoveUser(BaseModel):
    email: str = None

@router.post("/login", response_model=TokenResponse)
async def login(login_request: LoginRequest):
    """Proxy the login request to the Security service"""
    try:
        # Forward the request to the Security service
        response = requests.post(
            f"{SECURITY_URL}/auth/login",
            json=login_request.dict(),
            timeout=10
        )
        
        # Check if the request was successful
        if response.status_code == 200:
            # Return the response from the Security service
            return response.json()
        else:
            # Return the error from the Security service
            error_detail = response.json().get("detail", "Authentication failed")
            raise HTTPException(
                status_code=response.status_code,
                detail=error_detail
            )
    except requests.RequestException as e:
        logger.error(f"Error connecting to Security service: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Security service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Login error: {str(e)}"
        )

@router.post("/signup", response_model=TokenResponse)
async def signup(signup_request: SignupRequest):
    """Proxy the signup request to the Security service"""
    try:
        # Forward the request to the Security service
        response = requests.post(
            f"{SECURITY_URL}/auth/signup",
            json=signup_request.dict(),
            timeout=10
        )
        
        # Check if the request was successful
        if response.status_code == 200:
            # Return the response from the Security service
            return response.json()
        else:
            # Return the error from the Security service
            error_detail = response.json().get("detail", "Signup failed")
            raise HTTPException(
                status_code=response.status_code,
                detail=error_detail
            )
    except requests.RequestException as e:
        logger.error(f"Error connecting to Security service: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Security service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Signup error: {str(e)}"
        )

@router.post("/verify-token")
async def verify_token(request: Request):
    """Proxy the token verification request to the Security service"""
    try:
        # Get the Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=401,
                detail="Authorization header is missing"
            )
        
        # Forward the request to the Security service
        headers = {"Authorization": auth_header}
        response = requests.post(
            f"{SECURITY_URL}/auth/verify-token",
            headers=headers,
            timeout=10
        )
        
        # Return the response from the Security service
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error connecting to Security service: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Security service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )


@router.post("/logout", response_model=dict)
async def logout(request: Request):
    """Proxy the logout request to the Security service"""
    try:
        # Get the Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=401,
                detail="Authorization header is missing"
            )
        
        # Forward the request to the Security service
        headers = {"Authorization": auth_header}
        response = requests.post(
            f"{SECURITY_URL}/auth/logout",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            detail = response.json().get("detail", "Logout failed")
            raise HTTPException(status_code=response.status_code, detail=detail)
            
    except requests.RequestException as e:
        logger.error(f"Error connecting to Security service: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Security service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Logout error: {str(e)}"
        )


@router.post("/logout-all", response_model=dict)
async def logout_all(request: Request):
    """Proxy the logout-all request to the Security service"""
    try:
        # Get the Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=401,
                detail="Authorization header is missing"
            )
        
        # Forward the request to the Security service
        headers = {"Authorization": auth_header}
        response = requests.post(
            f"{SECURITY_URL}/auth/logout-all",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            detail = response.json().get("detail", "Logout from all devices failed")
            raise HTTPException(status_code=response.status_code, detail=detail)
            
    except requests.RequestException as e:
        logger.error(f"Error connecting to Security service: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Security service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Logout all error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Logout all error: {str(e)}"
        )


@router.post("/refresh", response_model=dict)
async def refresh_token(request: Request):
    """Proxy the token refresh request to the Security service"""
    try:
        # Get request body
        body = await request.body()
        
        # Forward the request to the Security service
        response = requests.post(
            f"{SECURITY_URL}/auth/refresh",
            data=body,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            detail = response.json().get("detail", "Token refresh failed")
            raise HTTPException(status_code=response.status_code, detail=detail)
            
    except requests.RequestException as e:
        logger.error(f"Error connecting to Security service: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Security service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Token refresh error: {str(e)}"
        )

@router.get("/health")
async def auth_health():
    """Check if the auth routes are working and if the Security service is reachable"""
    try:
        # Try to connect to the Security service
        response = requests.get(f"{SECURITY_URL}/health", timeout=5)
        security_status = "reachable" if response.status_code == 200 else f"error: {response.status_code}"
    except Exception as e:
        security_status = f"unreachable: {str(e)}"
    
    return {
        "auth_routes": "working",
        "security_service": security_status,
        "security_url": SECURITY_URL
    }

@router.get("/user-exists")
async def check_user_existence():
    """Check if any users exist in the system"""
    try:
        # Forward the request to the Security service
        response = requests.get(
            f"{SECURITY_URL}/auth/user-exists",
            timeout=5
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            # Endpoint doesn't exist, try the count endpoint
            logger.info("user-exists endpoint not found, trying users/count endpoint")
            count_response = requests.get(
                f"{SECURITY_URL}/auth/users/count",
                timeout=5
            )
            
            if count_response.status_code == 200:
                data = count_response.json()
                return {"userExists": data.get("count", 0) > 0}
            else:
                logger.warning(f"Both user-exists and users/count endpoints failed. Status: {count_response.status_code}")
                # Default to false for better UX when endpoints are missing
                return {"userExists": False}
        else:
            logger.warning(f"Security service returned unexpected status: {response.status_code}")
            # Default to false for better UX when there are errors
            return {"userExists": False}
                
    except requests.RequestException as e:
        logger.error(f"Error connecting to Security service when checking user existence: {e}")
        # Default to false if we can't connect to allow signup flow
        return {"userExists": False}
    except Exception as e:
        logger.error(f"Error checking user existence: {e}")
        return {"userExists": False}

@router.post("/update-profile")
async def update_profile(request: Request, data: ProfileUpdateRequest):
    """Update user profile information"""
    try:
        # Get the token from the request
        token = request.headers.get("Authorization")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Forward the request to the Security service
        response = requests.post(
            f"{SECURITY_URL}/auth/update-profile",
            headers={"Authorization": token},
            json=data.dict(exclude_none=True),
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            detail = response.json().get("detail", "Failed to update profile")
            raise HTTPException(status_code=response.status_code, detail=detail)
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/upload-profile-picture")
async def upload_profile_picture(request: Request, profile_picture: UploadFile = File(...)):
    """Upload and update user profile picture"""
    try:
        # Get the token from the request
        token = request.headers.get("Authorization")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Forward the request and file to the Security service
        files = {"profile_picture": (profile_picture.filename, profile_picture.file, profile_picture.content_type)}
        
        response = requests.post(
            f"{SECURITY_URL}/auth/upload-profile-picture",
            headers={"Authorization": token},
            files=files,
            timeout=30  # Longer timeout for file upload
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            detail = response.json().get("detail", "Failed to upload profile picture")
            raise HTTPException(status_code=response.status_code, detail=detail)
    except Exception as e:
        logger.error(f"Error uploading profile picture: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/update-preferences")
async def update_preferences(request: Request, data: PreferencesUpdateRequest):
    """Update user preferences"""
    try:
        # Get the token from the request
        token = request.headers.get("Authorization")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        logger.info(f"Forwarding preferences update to Security service: {SECURITY_URL}/auth/update-preferences")
        logger.info(f"Request data: {data.dict()}")
        
        # Forward the request to the Security service
        response = requests.post(
            f"{SECURITY_URL}/auth/update-preferences",
            headers={"Authorization": token},
            json=data.dict(),
            timeout=10
        )
        
        logger.info(f"Security service response status: {response.status_code}")
        
        if response.status_code == 200:
            # Return the full response including updated preferences
            result = response.json()
            logger.info(f"Security service response: {result}")
            return result
        else:
            error_response = response.json() if response.content else {"detail": "No response content"}
            logger.error(f"Security service error response: {error_response}")
            detail = error_response.get("detail", "Failed to update preferences")
            raise HTTPException(status_code=response.status_code, detail=detail)
    except requests.RequestException as e:
        logger.error(f"Error connecting to Security service: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Security service unavailable: {str(e)}")
    except Exception as e:
        logger.error(f"Error updating preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    

@router.post("/remove-user")
async def remove_user(request: Request, data: RemoveUser):
    """Remove user from system and store user in removed users"""
    try:
        # Get the token from the request
        token = request.headers.get("Authorization")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        logger.info(f"Forwarding remove user to Security service: {SECURITY_URL}/auth/remove-user")
        logger.info(f"Request data: {data.dict()}")
        
        # Forward the request to the Security service
        response = requests.post(
            f"{SECURITY_URL}/auth/remove-user",
            headers={"Authorization": token},
            json=data.dict(),
            timeout=10
        )
        
        logger.info(f"Security service response status: {response.status_code}")
        
        if response.status_code == 200:
            
            result = response.json()
            logger.info(f"Security service response: {result}")

            # Tell the rest of the system to remove the user
            message = ({
                "email": data.email
            })
            await publish_message(
                        exchange_name="removed_user",
                        exchange_type=aio_pika.ExchangeType.FANOUT,
                        message=message
                    )

            return result
        else:
            error_response = response.json() if response.content else {"detail": "No response content"}
            logger.error(f"Security service error response: {error_response}")
            detail = error_response.get("detail", "Failed to delete user")
            raise HTTPException(status_code=response.status_code, detail=detail)
    except requests.RequestException as e:
        logger.error(f"Error connecting to Security service: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Security service unavailable: {str(e)}")
    except Exception as e:
        logger.error(f"Error removing user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/change-password")
async def change_password(request: Request, data: ChangePasswordRequest):
    """Forward change password request to Security service"""
    try:
        # Get the token from the request
        token = request.headers.get("Authorization")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Forward the request to the Security service
        response = requests.post(
            f"{SECURITY_URL}/auth/change-password",
            headers={"Authorization": token},
            json=data.dict(),
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            detail = response.json().get("detail", "Failed to change password")
            raise HTTPException(status_code=response.status_code, detail=detail)
    except requests.RequestException as e:
        logger.error(f"Error connecting to Security service: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Security service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error changing password: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/me")
async def get_user_info(request: Request):
    """Get current user information"""
    try:
        # Get the token from the request
        token = request.headers.get("Authorization")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Forward the request to the Security service
        response = requests.get(
            f"{SECURITY_URL}/auth/me",
            headers={"Authorization": token},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            detail = response.json().get("detail", "Failed to get user information")
            raise HTTPException(status_code=response.status_code, detail=detail)
    except requests.RequestException as e:
        logger.error(f"Error connecting to Security service: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Security service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/users")
async def list_users(request: Request):
    """Get all users from Security service"""
    try:
        # Get the token from the request
        token = request.headers.get("Authorization")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        try:
            # First try /users endpoint (new path)
            response = None
            error_detail = None
            
            try:
                # Forward the request to the Security service
                response = requests.get(
                    f"{SECURITY_URL}/users",
                    headers={"Authorization": token},
                    timeout=10
                )
                
                if response.status_code == 200:
                    return response.json()
            except requests.RequestException:
                logger.warning("Failed to connect to /users endpoint, trying /auth/users")
                response = None
            
            # If first attempt failed, try the old endpoint path
            if not response or response.status_code != 200:
                try:
                    alt_response = requests.get(
                        f"{SECURITY_URL}/auth/users",
                        headers={"Authorization": token},
                        timeout=10
                    )
                    
                    if alt_response.status_code == 200:
                        return alt_response.json()
                    else:
                        try:
                            error_detail = alt_response.json().get("detail", "Failed to fetch users")
                        except:
                            error_detail = "Failed to fetch users"
                        
                        # Log the error but continue to the fallback approach
                        logger.warning(f"Failed to fetch users from /auth/users: {error_detail}")
                except requests.RequestException as e:
                    logger.warning(f"Failed to connect to /auth/users endpoint: {e}")
            
            # Try directly calling the user_routes endpoint as a last resort
            try:
                last_response = requests.get(
                    f"{SECURITY_URL}/users/",  # Note the trailing slash
                    headers={"Authorization": token},
                    timeout=10
                )
                
                if last_response.status_code == 200:
                    return last_response.json()
                else:
                    try:
                        error_detail = last_response.json().get("detail", "Failed to fetch users")
                    except:
                        error_detail = "Failed to fetch users"
                    
                    # Only raise an exception if all attempts have failed
                    raise HTTPException(
                        status_code=last_response.status_code, 
                        detail=error_detail
                    )
            except requests.RequestException as e:
                # All attempts failed - raise the exception
                raise HTTPException(
                    status_code=503,
                    detail=f"Security service unavailable: {str(e)}"
                )
            
        except requests.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from Security service: {e}")
            raise HTTPException(
                status_code=502,
                detail=f"Invalid response from Security service: {str(e)}"
            )
        
    except HTTPException:
        raise
    except requests.RequestException as e:
        logger.error(f"Error connecting to Security service: {e}")
        
        # Return empty list instead of failing - the UI should handle this gracefully
        logger.info("Returning empty users list due to connection error")
        return []
        
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/invite-user")
async def invite_user(request: Request):
    """Invite a new user"""
    try:
        # Get the token from the request
        token = request.headers.get("Authorization")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Get request body
        body = await request.json()
          # Forward the request to the Security service
        response = requests.post(
            f"{SECURITY_URL}/admin/invite-user",
            headers={"Authorization": token},
            json=body,
            timeout=15  # Increase timeout to 15 seconds
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400 and "email" in response.text.lower():
            # Special handling for email sending failures
            try:
                detail = response.json().get("detail", "Failed to send invitation email")
                logger.warning(f"Email sending failure: {detail}")
                # Return a more user-friendly error message
                raise HTTPException(status_code=503, 
                    detail="Email service is currently unavailable. Your invitation has been saved and emails will be sent when the service is restored.")
            except ValueError:
                # If we can't parse the JSON response
                raise HTTPException(status_code=503, detail="Email service is currently unavailable")
        else:
            try:
                detail = response.json().get("detail", "Failed to invite user")
            except ValueError:
                detail = "Failed to invite user"
            raise HTTPException(status_code=response.status_code, detail=detail)
    except requests.RequestException as e:
        logger.error(f"Error connecting to Security service: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Security service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error inviting user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/update-permissions")
async def update_permissions(request: Request):
    """Update user permissions"""
    try:
        # Get the token from the request
        token = request.headers.get("Authorization")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Get request body
        body = await request.json()
        
        # Extract user_id and role from the request
        user_id = body.get("user_id")
        role = body.get("role")
        
        if not user_id or not role:
            raise HTTPException(
                status_code=400, 
                detail="Missing required fields: user_id and role must be provided"
            )
        
        # Create the permissions request body
        permissions_data = {
            "role": role,
            "custom_permissions": body.get("custom_permissions", [])
        }
        
        # Forward the request to the Security service
        response = requests.put(
            f"{SECURITY_URL}/users/{user_id}/permissions",
            headers={"Authorization": token},
            json=permissions_data,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            detail = response.json().get("detail", "Failed to update user permissions")
            raise HTTPException(status_code=response.status_code, detail=detail)
    except requests.RequestException as e:
        logger.error(f"Error connecting to Security service: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Security service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error updating permissions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/roles")
async def get_roles(request: Request):
    """Get all available roles from Security service"""
    try:
        # Get the token from the request
        token = request.headers.get("Authorization")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        try:
            # Forward the request to the Security service
            response = requests.get(
                f"{SECURITY_URL}/roles",
                headers={"Authorization": token},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                # If the security service returns 404, try the auth/roles endpoint path
                alt_response = requests.get(
                    f"{SECURITY_URL}/auth/roles",
                    headers={"Authorization": token},
                    timeout=10
                )
                
                if alt_response.status_code == 200:
                    return alt_response.json()
                else:
                    try:
                        detail = alt_response.json().get("detail", "Failed to fetch roles")
                    except:
                        detail = "Failed to fetch roles"
                    raise HTTPException(status_code=alt_response.status_code, detail=detail)
            else:
                try:
                    detail = response.json().get("detail", "Failed to fetch roles")
                except:
                    detail = "Failed to fetch roles"
                raise HTTPException(status_code=response.status_code, detail=detail)
                
        except requests.JSONDecodeError:
            logger.error("Invalid JSON response from Security service")
            raise HTTPException(
                status_code=502,
                detail="Invalid response from Security service"
            )
        
    except requests.RequestException as e:
        logger.error(f"Error connecting to Security service: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Security service unavailable: {str(e)}"
        )
        
    except Exception as e:
        logger.error(f"Error fetching roles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/invitations")
async def get_pending_invitations(request: Request):
    """Get pending invitations"""
    try:
        # Get the token from the request
        token = request.headers.get("Authorization")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Forward the request to the Security service
        response = requests.get(
            f"{SECURITY_URL}/admin/pending-invitations",
            headers={"Authorization": token},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            detail = response.json().get("detail", "Failed to fetch invitations")
            raise HTTPException(status_code=response.status_code, detail=detail)
    except requests.RequestException as e:
        logger.error(f"Error connecting to Security service: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Security service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error fetching invitations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/resend-invitation")
async def resend_invitation(request: Request):
    """Resend invitation OTP"""
    try:
        # Get the token from the request
        token = request.headers.get("Authorization")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Get request body
        body = await request.json()
        
        # Forward the request to the Security service
        response = requests.post(
            f"{SECURITY_URL}/admin/resend-invitation",
            headers={"Authorization": token},
            json=body,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            detail = response.json().get("detail", "Failed to resend invitation")
            raise HTTPException(status_code=response.status_code, detail=detail)
    except requests.RequestException as e:
        logger.error(f"Error connecting to Security service: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Security service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error resending invitation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/verify-otp")
async def verify_otp(request: Request):
    """Verify OTP for invitation (public endpoint)"""
    try:
        # Get request body
        body = await request.json()
        
        # Forward the request to the Security service
        response = requests.post(
            f"{SECURITY_URL}/admin/verify-otp",
            json=body,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            detail = response.json().get("detail", "Failed to verify OTP")
            raise HTTPException(status_code=response.status_code, detail=detail)
    except requests.RequestException as e:
        logger.error(f"Error connecting to Security service: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Security service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error verifying OTP: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/complete-registration")
async def complete_registration(request: Request):
    """Complete user registration after OTP verification (public endpoint)"""
    try:
        # Get request body
        body = await request.json()
        
        # Forward the request to the Security service
        response = requests.post(
            f"{SECURITY_URL}/admin/complete-registration",
            json=body,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            detail = response.json().get("detail", "Failed to complete registration")
            raise HTTPException(status_code=response.status_code, detail=detail)
    except requests.RequestException as e:
        logger.error(f"Error connecting to Security service: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Security service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error completing registration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/create-user")
async def create_user_manually(user_data: CreateUserRequest, request: Request):
    """Admin can manually create a user without invitation flow"""
    # Log the incoming request data
    logger = logging.getLogger(__name__)
    logger.info(f"Received user creation request. User data model: {user_data}")
    try:
        # Get the token from the request
        token = request.headers.get("Authorization")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Convert to dict and log what's being sent
        user_data_dict = user_data.dict()
        logger.info(f"Sending user creation data to Security service: {user_data_dict}")
        
        if not user_data_dict:
            logger.error("User data dictionary is empty after conversion!")
            # Ensure we have the expected data structure
            user_data_dict = {
                "full_name": user_data.full_name,
                "email": user_data.email,
                "role": user_data.role,
                "password": user_data.password,
                "phoneNo": user_data.phoneNo if user_data.phoneNo else None,
                "details": user_data.details if hasattr(user_data, "details") else {}
            }
            logger.info(f"Reconstructed user data: {user_data_dict}")
        
        # Forward the request to the Security service
        response = requests.post(
            f"{SECURITY_URL}/admin/create-user",
            headers={"Authorization": token},
            json=user_data_dict,
            timeout=15
        )
        
        if response.status_code == 200:
            if user_data.role == "driver":
                import aio_pika
                from .service_routing import SERVICE_BLOCKS

                logger = logging.getLogger(__name__)
                management_config = SERVICE_BLOCKS["management"]
                new_user_id = response.json()["user_id"]

                message = {
                    "email": user_data.email,
                    "user_id": new_user_id
                }
                
                try:
                    # Publish the message to the management service
                    await publish_message(
                        exchange_name=management_config["exchange"],
                        exchange_type=aio_pika.ExchangeType.DIRECT,
                        message=message,
                        routing_key=management_config["user.created"]
                    )
                    logger.info(f"Notification sent to management service for driver addition")
                except Exception as e:
                    logger.error(f"Failed to send notification to management service: {str(e)}")

            return response.json()
        else:
            try:
                detail = response.json().get("detail", "Failed to create user")
            except ValueError:
                detail = "Failed to create user"
            raise HTTPException(status_code=response.status_code, detail=detail)
            
    except requests.RequestException as e:
        logger.error(f"Error connecting to Security service: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Security service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/forgot-password")
async def forgot_password(request: Request):
    """Proxy forgot password requests to Security service"""
    try:
        # Get request body
        body = await request.json()
        
        # Forward the request to the Security service
        response = requests.post(
            f"{SECURITY_URL}/auth/forgot-password",
            json=body,
            timeout=15
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            try:
                detail = response.json().get("detail", "Forgot password failed")
            except ValueError:
                detail = "Forgot password failed"
            raise HTTPException(status_code=response.status_code, detail=detail)
            
    except requests.RequestException as e:
        logger.error(f"Error connecting to Security service: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Security service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error with forgot password: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
