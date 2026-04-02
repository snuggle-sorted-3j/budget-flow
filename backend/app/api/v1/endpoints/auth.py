"""Authentication endpoints for user registration, login, and profile."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import create_access_token
from app.crud.user import authenticate_user, create_user, get_user_by_email
from app.models.user import User
from app.models.account import Account
from app.models.calculation_period import CalculationPeriod
from app.models.currency import Currency
from app.schemas.auth import LoginRequest, SetupStatusResponse, TokenResponse, UserCreate, UserResponse

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
    
    # Auto-initialize currencies and categories
    from app.crud.currency import initialize_default_currencies
    from app.crud.expense_category import create_system_categories
    initialize_default_currencies(db, user.id)
    create_system_categories(db, user.id)
    
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


@router.get("/setup-status", response_model=SetupStatusResponse)
def get_setup_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SetupStatusResponse:
    """Return whether the user still needs to complete initial setup.

    Args:
        db: Database session.
        current_user: Authenticated user.

    Returns:
        SetupStatusResponse with needs_setup flag, list of missing items,
        and current counts for key entities.
    """
    missing = []

    has_accounts = db.query(Account).filter_by(user_id=current_user.id, is_active=True).first() is not None
    has_periods = db.query(CalculationPeriod).filter_by(user_id=current_user.id).first() is not None
    currencies_count = db.query(Currency).filter_by(user_id=current_user.id).count()

    if not has_accounts:
        missing.append("accounts")
    if not has_periods:
        missing.append("periods")

    return SetupStatusResponse(
        needs_setup=bool(missing),
        missing=missing,
        currencies_count=currencies_count,
    )



