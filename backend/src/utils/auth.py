"""
Supabase authentication utilities for FastAPI backend.
"""
import jwt
import os
from typing import Optional
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

# Initialize the HTTPBearer security scheme
security = HTTPBearer()

class User(BaseModel):
    """Authenticated user model."""
    id: str
    email: str
    role: Optional[str] = None
    full_name: Optional[str] = None

class SupabaseAuth:
    """Supabase authentication handler."""
    
    def __init__(self):
        self._jwt_secret = None
    
    @property
    def jwt_secret(self):
        """Lazy load JWT secret from environment or settings."""
        if self._jwt_secret is None:
            # Try environment variable first
            self._jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
            
            # Fallback to settings if available
            if not self._jwt_secret:
                try:
                    from .config import settings
                    self._jwt_secret = settings.supabase_jwt_secret
                except:
                    pass
            
            if not self._jwt_secret:
                raise ValueError("SUPABASE_JWT_SECRET environment variable is required")
        
        return self._jwt_secret
    
    def verify_token(self, token: str) -> dict:
        """Verify and decode Supabase JWT token."""
        try:
            # First try to decode without verification to check the issuer
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            actual_issuer = unverified_payload.get("iss")
            logger.info(f"JWT token issuer: {actual_issuer}")
            
            # Decode JWT token with proper issuer
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
                issuer=actual_issuer  # Use the actual issuer from the token
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    def get_user_from_token(self, token: str) -> User:
        """Extract user information from JWT token."""
        payload = self.verify_token(token)
        
        # Extract user data from JWT payload
        user_id = payload.get("sub")
        email = payload.get("email")
        
        if not user_id or not email:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Extract custom user metadata if available
        user_metadata = payload.get("user_metadata", {})
        app_metadata = payload.get("app_metadata", {})
        
        return User(
            id=user_id,
            email=email,
            role=user_metadata.get("role") or app_metadata.get("role"),
            full_name=user_metadata.get("full_name") or user_metadata.get("fullName")
        )

# Initialize auth handler - lazy loading
_supabase_auth = None

def get_auth_handler():
    """Get or create the auth handler instance."""
    global _supabase_auth
    if _supabase_auth is None:
        _supabase_auth = SupabaseAuth()
    return _supabase_auth

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Dependency to get the current authenticated user.
    Use this in your FastAPI route functions that require authentication.
    
    Example:
        @app.get("/protected")
        async def protected_route(user: User = Depends(get_current_user)):
            return {"message": f"Hello {user.email}"}
    """
    try:
        token = credentials.credentials
        auth_handler = get_auth_handler()
        user = auth_handler.get_user_from_token(token)
        return user
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[User]:
    """
    Dependency to get the current user if authenticated, otherwise None.
    Use this for endpoints that work both with and without authentication.
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        auth_handler = get_auth_handler()
        user = auth_handler.get_user_from_token(token)
        return user
    except Exception:
        return None

def require_role(required_role: str):
    """
    Decorator factory to require specific user roles.
    
    Example:
        @app.get("/admin-only")
        async def admin_route(user: User = Depends(require_role("healthcare_provider"))):
            return {"message": "Admin access granted"}
    """
    async def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role != required_role:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required role: {required_role}"
            )
        return user
    
    return role_checker