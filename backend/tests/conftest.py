import pytest
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
import os

# Set environment variables for testing before importing the app
os.environ["DATABASE_URL"] = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/budget_flow_test")
os.environ["JWT_SECRET"] = "test-secret-key-1234567890"
os.environ["ENVIRONMENT"] = "testing"

from app.main import app
from app.database import Base
from app.api.deps import get_db
from app.core.security import create_access_token
from app.models.user import User
from app.models.currency import Currency
import uuid

# Use the test database URl from environment
SQLALCHEMY_DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create and drop tables for the test session."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db() -> Generator[Session, None, None]:
    """Provide a clean database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    """Provide a TestClient that uses the test database."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user in the database."""
    from app.core.security import get_password_hash
    email = f"test-{uuid.uuid4()}@example.com"
    user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash=get_password_hash("testpassword123"),
        full_name="Test User",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def test_token(test_user: User) -> str:
    """Provide a valid JWT token for the test user."""
    return create_access_token(data={"sub": str(test_user.id)})

@pytest.fixture
def auth_headers(test_token: str) -> dict:
    """Provide Authorization headers with a valid JWT."""
    return {"Authorization": f"Bearer {test_token}"}

@pytest.fixture
def test_currency(db: Session, test_user: User) -> Currency:
    """Create a test currency for the user."""
    currency = Currency(
        id=uuid.uuid4(),
        user_id=test_user.id,
        ticker="USD",
        name="US Dollar",
        is_default=True
    )
    db.add(currency)
    db.commit()
    db.refresh(currency)
    return currency
