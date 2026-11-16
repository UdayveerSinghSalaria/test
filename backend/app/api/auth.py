from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.auth import AuthService
from app.schemas.auth import UserRegister, UserLogin, Token, UserResponse
from app.dependencies import get_current_user
from app.models.email_account import EmailAccount
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Token)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new user with email credentials."""
    auth = AuthService(db)
    try:
        user = await auth.register(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    token = auth.create_token(user)
    
    # Get email account info for response
    email_account = await auth.get_user_email_account(user.id)
    
    return Token(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            email_provider=email_account.provider.value if email_account else None,
            email_address=email_account.email_address if email_account else None,
            has_email_configured=email_account is not None,
        )
    )


@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login with email and password."""
    auth = AuthService(db)
    user = await auth.login(data.email, data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = auth.create_token(user)
    
    email_account = await auth.get_user_email_account(user.id)
    
    return Token(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            email_provider=email_account.provider.value if email_account else None,
            email_address=email_account.email_address if email_account else None,
            has_email_configured=email_account is not None,
        )
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get current user profile with email account info."""
    auth = AuthService(db)
    email_account = await auth.get_user_email_account(current_user.id)
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        email_provider=email_account.provider.value if email_account else None,
        email_address=email_account.email_address if email_account else None,
        has_email_configured=email_account is not None,
    )


@router.post("/logout")
async def logout():
    """Logout (client-side token removal)."""
    return {"message": "Logged out successfully"}