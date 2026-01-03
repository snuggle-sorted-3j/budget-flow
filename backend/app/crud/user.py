"""CRUD operations for User model."""

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import UserCreate


def create_user(db: Session, user: UserCreate) -> User:
    """Create a new user with hashed password.

    Args:
        db: Database session.
        user: UserCreate schema with user data.

    Returns:
        Created User instance.
    """
    db_user = User(
        email=user.email,
        password_hash=get_password_hash(user.password),
        full_name=user.full_name,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_email(db: Session, email: str) -> User | None:
    """Get a user by email address.

    Args:
        db: Database session.
        email: Email address to search for.

    Returns:
        User instance if found, None otherwise.
    """
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: str) -> User | None:
    """Get a user by ID.

    Args:
        db: Database session.
        user_id: UUID of the user.

    Returns:
        User instance if found, None otherwise.
    """
    return db.query(User).filter(User.id == user_id).first()


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Authenticate a user by email and password.

    Args:
        db: Database session.
        email: Email address of the user.
        password: Plain text password to verify.

    Returns:
        User instance if authentication successful, None otherwise.
    """
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user



