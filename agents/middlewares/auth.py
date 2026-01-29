"""
Authentication middleware for FastAPI.

Handles Supabase JWT token validation for protected routes.
"""

import httpx
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config.settings import settings
from utils.logger import logger

security = HTTPBearer(auto_error=False)


class SupabaseAuth:
    """
    Supabase authentication handler.
    
    Validates JWT tokens against Supabase to get user information.
    """
    
    def __init__(self):
        self.supabase_url = getattr(settings, 'SUPABASE_URL', None)
        self.supabase_key = getattr(settings, 'SUPABASE_KEY', None)
    
    async def get_user(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate token and get user info from Supabase.
        
        Args:
            token: JWT access token
            
        Returns:
            User dict with id, email, etc. or None if invalid
        """
        if not self.supabase_url:
            # Fallback: extract user from JWT without validation (dev mode)
            return self._decode_jwt_unsafe(token)
        
        try:
            async with httpx.AsyncClient(timeout=settings.AUTH_TIMEOUT) as client:
                response = await client.get(
                    f"{self.supabase_url}/auth/v1/user",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "apikey": self.supabase_key or ""
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                    
        except Exception as e:
            logger.error(f"Auth error: {e}")
        
        return None
    
    def _decode_jwt_unsafe(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decode JWT without verification (development only).
        
        WARNING: Only use this in development when Supabase URL is not configured.
        """
        import base64
        import json
        
        try:
            # JWT has 3 parts: header.payload.signature
            parts = token.split('.')
            if len(parts) != 3:
                return None
            
            # Decode payload (middle part)
            payload = parts[1]
            # Add padding if needed
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += '=' * padding
            
            decoded = base64.urlsafe_b64decode(payload)
            data = json.loads(decoded)
            
            # Extract user info
            return {
                "id": data.get("sub"),
                "email": data.get("email"),
                "role": data.get("role", "user"),
            }
            
        except Exception as e:
            logger.error(f"JWT decode error: {e}")
            return None


# Singleton instance
_auth = SupabaseAuth()


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency to get the current authenticated user.
    
    Raises:
        HTTPException: 401 if not authenticated
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user = await _auth.get_user(credentials.credentials)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    FastAPI dependency to optionally get the current user.
    
    Returns None if not authenticated instead of raising an exception.
    """
    if not credentials:
        return None
    
    return await _auth.get_user(credentials.credentials)
