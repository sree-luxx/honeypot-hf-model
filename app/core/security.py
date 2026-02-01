from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.config import API_KEY

api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if not API_KEY:
        # If API_KEY is not set in env, allow all (or block all, depending on policy).
        # Safe default: allow but log warning, or just block. 
        # Here we assume if it's set, we check it.
        return None
        
    if api_key_header == API_KEY:
        return api_key_header
        
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate credentials"
    )
