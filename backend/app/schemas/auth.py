from typing import Optional
from pydantic import BaseModel

# ── Outbound Response ─────────────────────────────────
class Token(BaseModel):
    """
    Standard OAuth2 response schema. 
    The frontend will save this access_token in Memory or LocalStorage.
    """
    access_token: str
    token_type: str = "bearer"

# ── Internal Payload ──────────────────────────────────
class TokenPayload(BaseModel):
    """
    Represents the data baked inside the JWT.
    Used during token decoding in dependencies.py to ensure type safety.
    """
    sub: Optional[str] = None