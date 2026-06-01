from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.db.database import get_db
from app.schemas.auth import Token
from app.services.auth_service import authenticate_user

router = APIRouter(tags=["Authentication"])

@router.post("/login", response_model=Token)
def login_for_access_token(
    db: Session = Depends(get_db),
    # This dependency forces the endpoint to expect Form Data, not JSON.
    # It makes the Swagger UI 'Authorize' button work natively.
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """
    OAuth2 compatible token login.
    Note: The frontend must send data as `application/x-www-form-urlencoded`.
    Because of OAuth2 standards, map the 'email' input to the 'username' field.
    """
    user = authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Account suspended"
        )

    # Mint the JWT
    access_token = create_access_token(subject=user.id)
    
    return {
        "access_token": access_token, 
        "token_type": "bearer"
    }