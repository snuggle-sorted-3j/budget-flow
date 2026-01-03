"""Authentication endpoints for user registration, login, and profile."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import create_access_token
from app.crud.user import authenticate_user, create_user, get_user_by_email
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserCreate, UserResponse

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db),
) -> UserResponse:
    """Register a new user.

    Args:
        user_in: User registration data.
        db: Database session.

    Returns:
        Created user data.

    Raises:
        HTTPException: If email already registered.
    """
    existing_user = get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    user = create_user(db, user_in)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate user and return JWT token.

    Uses OAuth2 password flow for compatibility with OpenAPI/Swagger UI.

    Args:
        form_data: OAuth2 form with username (email) and password.
        db: Database session.

    Returns:
        JWT access token.

    Raises:
        HTTPException: If credentials are invalid.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    access_token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(access_token=access_token)


@router.post("/login/json", response_model=TokenResponse)
def login_json(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate user and return JWT token (JSON body).

    Alternative login endpoint accepting JSON body instead of form data.

    Args:
        login_data: Login credentials as JSON.
        db: Database session.

    Returns:
        JWT access token.

    Raises:
        HTTPException: If credentials are invalid.
    """
    user = authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    access_token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Get current authenticated user information.

    Args:
        current_user: Authenticated user from JWT token.

    Returns:
        Current user data.
    """
    return UserResponse.model_validate(current_user)



