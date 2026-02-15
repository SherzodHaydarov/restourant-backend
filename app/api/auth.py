import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.repositories.repository import UserRepository, RoleRepository
from app.services.service import AuthService
from app.schemas.schemas import (
    UserAuthSchema,
    UserLoginSchema,
    TokenSchema,
    TokenRefreshSchema,
    UserResponseSchema,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserAuthSchema, db: AsyncSession = Depends(get_db)):
    """Register new user"""
    try:
        user_repo = UserRepository(db)
        role_repo = RoleRepository(db)

        auth_service = AuthService(user_repo, role_repo)
        result = await auth_service.register_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            phone=user_data.phone,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
        )

        return {
            "status": "success",
            "message": "User registered successfully",
            "data": result,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.post("/login", response_model=dict)
async def login(credentials: UserLoginSchema, db: AsyncSession = Depends(get_db)):
    """Login user and return tokens"""
    try:
        user_repo = UserRepository(db)
        role_repo = RoleRepository(db)

        auth_service = AuthService(user_repo, role_repo)
        result = await auth_service.authenticate_user(
            credentials.username, credentials.password
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        return {
            "status": "success",
            "data": {
                "access_token": result["access_token"],
                "refresh_token": result["refresh_token"],
                "token_type": "bearer",
                "user": {
                    "id": result["user_id"],
                    "username": result["username"],
                    "email": result["email"],
                    "role": result["role"],
                },
            },
        }
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed",
        )


@router.post("/refresh", response_model=dict)
async def refresh_token(
    payload: TokenRefreshSchema, db: AsyncSession = Depends(get_db)
):
    """Refresh access token"""
    try:
        user_repo = UserRepository(db)
        role_repo = RoleRepository(db)

        auth_service = AuthService(user_repo, role_repo)
        access_token = await auth_service.refresh_access_token(payload.refresh_token)

        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        return {
            "status": "success",
            "data": {
                "access_token": access_token,
                "token_type": "bearer",
            },
        }
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed",
        )


@router.get("/me", response_model=dict)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user information"""
    try:
        user_repo = UserRepository(db)
        user = await user_repo.get_user_by_id(current_user["user_id"])

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return {
            "status": "success",
            "data": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "phone": user.phone,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.name,
                "is_verified": user.is_verified,
                "created_at": user.created_at,
            },
        }
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user info",
        )
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.api.auth:router", host="127.0.0.1", port=8000)