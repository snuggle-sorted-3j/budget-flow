Perfect! Continuing with the next set of documents. I'll generate:
1. `PROJECT_STRUCTURE.md`
2. `.cursorrules`
3. `docker-compose.yml`
4. `.env.example`

Let me create these in pure markdown/proper format.

***

**📄 Document 1 of 4: PROJECT_STRUCTURE.md**

**COPY INSTRUCTIONS:** Copy everything from "# BudgetFlow - Project Structure" to "END OF PROJECT_STRUCTURE.md"

***

# BudgetFlow - Project Structure

**Version:** 1.0  
**Last Updated:** November 9, 2025  
**Purpose:** Complete folder organization and file structure for BudgetFlow

***

## Table of Contents

1. [Overview](#1-overview)
2. [Root Directory Structure](#2-root-directory-structure)
3. [Backend Structure](#3-backend-structure)
4. [Frontend Structure](#4-frontend-structure)
5. [Testing Structure](#5-testing-structure)
6. [Configuration Files](#6-configuration-files)
7. [File Naming Conventions](#7-file-naming-conventions)
8. [Import Patterns](#8-import-patterns)

***

## 1. Overview

### 1.1 Architecture

**Monorepo structure** with separate backend and frontend:
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
- **Frontend**: Plotly Dash
- **Development**: Docker Compose
- **Deployment**: AWS (ECS Fargate + RDS)

### 1.2 Design Principles

- **Separation of Concerns**: Backend API separate from frontend UI
- **Modular Design**: Each feature in its own module
- **Test Co-location**: Tests mirror source structure
- **Configuration as Code**: All settings in version control (except secrets)

---

## 2. Root Directory Structure

```
budget-flow/
├── .github/
│   └── workflows/
│       └── ci-cd.yml
├── backend/
├── frontend/
├── docs/                          # ← All comprehensive documentation here
│   ├── PRD.md                     # ← MOVED
│   ├── DATABASE_SCHEMA.md         # ← MOVED
│   ├── PROJECT_STRUCTURE.md       # ← MOVED
│   ├── API_SPECIFICATION.md
│   ├── DEPLOYMENT.md
│   ├── CI_CD_WORKFLOW.md          # ← MOVED (optional)
│   ├── SQL_TESTING_GUIDE.md       # ← MOVED
│   └── USER_GUIDE.md
├── scripts/
│   ├── setup.sh
│   ├── check-ci-status.sh
│   └── backup-db.sh
├── .cursorrules
├── .env.example
├── .gitignore
├── .flake8
├── .pre-commit-config.yaml
├── docker-compose.yml
├── README.md                      # ← STAYS in root
├── QUICKSTART.md                  # ← STAYS in root
├── GIT_WORKFLOW.md                # ← STAYS in root
├── CODE_QUALITY.md                # ← STAYS in root
└── SECURITY.md                    # ← STAYS in root
```

***

## 3. Backend Structure

### 3.1 Complete Backend Layout

```
backend/
├── alembic/
│   ├── versions/                  # Migration files
│   ├── env.py                     # Alembic environment
│   └── script.py.mako             # Migration template
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py            # Authentication endpoints
│   │   │   │   ├── periods.py         # Calculation periods
│   │   │   │   ├── accounts.py        # Bank accounts
│   │   │   │   ├── income.py          # Income entries
│   │   │   │   ├── expenses.py        # Expense items
│   │   │   │   ├── categories.py      # Expense categories
│   │   │   │   ├── suspended.py       # Suspended transactions
│   │   │   │   ├── installments.py    # Installment tracking
│   │   │   │   ├── conversions.py     # Currency conversions
│   │   │   │   ├── investments.py     # Investment tracking
│   │   │   │   ├── reconciliation.py  # Reconciliation logic
│   │   │   │   └── templates.py       # Template management
│   │   │   ├── __init__.py
│   │   │   └── api.py                 # API router aggregation
│   │   └── deps.py                    # Dependency injection
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                  # App configuration
│   │   ├── security.py                # JWT, password hashing
│   │   └── exceptions.py              # Custom exceptions
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                    # User model
│   │   ├── user_settings.py           # User settings model
│   │   ├── currency.py                # Currency model
│   │   ├── account.py                 # Account model
│   │   ├── calculation_period.py      # Period model
│   │   ├── balance_snapshot.py        # Balance snapshot model
│   │   ├── income_entry.py            # Income model
│   │   ├── expense_category.py        # Category model
│   │   ├── expense_item.py            # Expense model
│   │   ├── suspended_expense.py       # Suspended transaction model
│   │   ├── installment_item.py        # Installment model
│   │   ├── installment_payment.py     # Payment model
│   │   ├── currency_conversion.py     # Conversion model
│   │   ├── investment_account.py      # Investment account model
│   │   ├── investment.py              # Investment model
│   │   ├── investment_transfer.py     # Transfer model
│   │   ├── template.py                # Template model
│   │   └── custom_expense_type.py     # Custom type model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py                    # User Pydantic schemas
│   │   ├── auth.py                    # Auth schemas
│   │   ├── period.py                  # Period schemas
│   │   ├── account.py                 # Account schemas
│   │   ├── income.py                  # Income schemas
│   │   ├── expense.py                 # Expense schemas
│   │   ├── suspended.py               # Suspended schemas
│   │   ├── installment.py             # Installment schemas
│   │   ├── conversion.py              # Conversion schemas
│   │   ├── investment.py              # Investment schemas
│   │   ├── reconciliation.py          # Reconciliation schemas
│   │   └── template.py                # Template schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py            # Authentication logic
│   │   ├── period_service.py          # Period business logic
│   │   ├── reconciliation_service.py  # Reconciliation calculations
│   │   ├── currency_service.py        # Currency operations
│   │   └── template_service.py        # Template operations
│   ├── crud/
│   │   ├── __init__.py
│   │   ├── base.py                    # Base CRUD operations
│   │   ├── user.py                    # User CRUD
│   │   ├── period.py                  # Period CRUD
│   │   ├── account.py                 # Account CRUD
│   │   ├── income.py                  # Income CRUD
│   │   ├── expense.py                 # Expense CRUD
│   │   └── ...                        # Other CRUD modules
│   ├── database.py                    # Database connection
│   ├── main.py                        # FastAPI app entry point
│   └── __init__.py
├── tests/
│   ├── unit/
│   │   ├── test_reconciliation.py     # Reconciliation unit tests
│   │   ├── test_currency.py           # Currency unit tests
│   │   └── test_validation.py         # Validation unit tests
│   ├── integration/
│   │   ├── test_period_workflow.py    # Full period workflow
│   │   ├── test_database.py           # Database tests
│   │   └── test_api_endpoints.py      # API integration tests
│   ├── conftest.py                    # Pytest fixtures
│   └── __init__.py
├── Dockerfile                         # Backend Docker image
├── requirements.txt                   # Python dependencies
├── requirements-dev.txt               # Development dependencies
├── pyproject.toml                     # Black, Mypy, Bandit config
├── pytest.ini                         # Pytest configuration
└── alembic.ini                        # Alembic configuration
```

### 3.2 Key Backend Files

#### app/main.py
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings

app = FastAPI(
    title="BudgetFlow API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

#### app/core/config.py
```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "BudgetFlow"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str
    
    # Security
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:8050"]
    
    class Config:
        env_file = ".env"

settings = Settings()
```

***

## 4. Frontend Structure

### 4.1 Complete Frontend Layout

```
frontend/
├── app/
│   ├── layouts/
│   │   ├── __init__.py
│   │   ├── main_layout.py             # Main app layout
│   │   ├── sidebar.py                 # Navigation sidebar
│   │   └── header.py                  # Header component
│   ├── tabs/
│   │   ├── __init__.py
│   │   ├── tab1_period_setup.py       # Period creation tab
│   │   ├── tab2_income.py             # Income entry tab
│   │   ├── tab3_expenses.py           # Expense entry tab
│   │   ├── tab4_suspended.py          # Suspended transactions tab
│   │   ├── tab5_installments.py       # Installments tab
│   │   ├── tab6_conversions.py        # Currency conversions tab
│   │   ├── tab7_investments.py        # Investments tab
│   │   ├── tab8_reconciliation.py     # Reconciliation tab
│   │   ├── tab9_dashboards.py         # Analytics dashboards tab
│   │   └── tab10_settings.py          # Settings tab
│   ├── components/
│   │   ├── __init__.py
│   │   ├── charts.py                  # Chart components
│   │   ├── tables.py                  # Table components
│   │   ├── forms.py                   # Form components
│   │   └── modals.py                  # Modal dialogs
│   ├── callbacks/
│   │   ├── __init__.py
│   │   ├── period_callbacks.py        # Period-related callbacks
│   │   ├── income_callbacks.py        # Income callbacks
│   │   ├── expense_callbacks.py       # Expense callbacks
│   │   ├── reconciliation_callbacks.py # Reconciliation callbacks
│   │   └── settings_callbacks.py      # Settings callbacks
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── api_client.py              # API communication
│   │   ├── formatters.py              # Data formatting
│   │   └── validators.py              # Input validation
│   ├── main.py                        # Dash app entry point
│   └── __init__.py
├── assets/
│   ├── styles.css                     # Custom CSS
│   ├── logo.png                       # App logo
│   └── favicon.ico                    # Favicon
├── tests/
│   ├── test_components.py             # Component tests
│   └── test_callbacks.py              # Callback tests
├── Dockerfile                         # Frontend Docker image
└── requirements.txt                   # Dash dependencies
```

### 4.2 Key Frontend Files

#### app/main.py
```python
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from app.layouts.main_layout import create_layout
from app.callbacks import register_callbacks

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)

app.layout = create_layout()
register_callbacks(app)

server = app.server

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)
```

#### app/utils/api_client.py
```python
import requests
from typing import Dict, Any

class APIClient:
    def __init__(self, base_url: str = "http://backend:8000/api/v1"):
        self.base_url = base_url
        self.token = None
    
    def set_token(self, token: str):
        self.token = token
    
    def get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def get(self, endpoint: str) -> Dict[str, Any]:
        response = requests.get(
            f"{self.base_url}{endpoint}",
            headers=self.get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}{endpoint}",
            json=data,
            headers=self.get_headers()
        )
        response.raise_for_status()
        return response.json()
```

***

## 5. Testing Structure

### 5.1 Backend Testing

```
backend/tests/
├── unit/
│   ├── test_models.py                 # Model tests
│   ├── test_schemas.py                # Schema validation tests
│   ├── test_reconciliation.py         # Reconciliation logic tests
│   ├── test_currency.py               # Currency operations tests
│   └── test_validation.py             # Input validation tests
├── integration/
│   ├── test_database.py               # Database integration tests
│   ├── test_period_workflow.py        # Full period workflow tests
│   ├── test_api_auth.py               # Authentication tests
│   ├── test_api_periods.py            # Period API tests
│   ├── test_api_expenses.py           # Expense API tests
│   └── test_reconciliation_flow.py    # End-to-end reconciliation
├── conftest.py                        # Shared fixtures
└── __init__.py
```

### 5.2 Test Fixtures (conftest.py)

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import User, Currency

@pytest.fixture
def test_db():
    # Create test database
    engine = create_engine("postgresql://test:test@localhost:5432/test_db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)

@pytest.fixture
def test_user(test_db):
    user = User(
        email="test@example.com",
        password_hash="hashed_password",
        full_name="Test User"
    )
    test_db.add(user)
    test_db.commit()
    return user

@pytest.fixture
def test_currency(test_db, test_user):
    currency = Currency(
        user_id=test_user.id,
        ticker="PLN",
        name="Polish Zloty",
        is_default=True
    )
    test_db.add(currency)
    test_db.commit()
    return currency
```

***

## 6. Configuration Files

### 6.1 Essential Configuration Files

| File | Purpose |
|------|---------|
| `.cursorrules` | Cursor AI development instructions |
| `.env.example` | Example environment variables |
| `.gitignore` | Files to ignore in Git |
| `.flake8` | Flake8 linter configuration |
| `.pre-commit-config.yaml` | Pre-commit hooks |
| `docker-compose.yml` | Local development environment |
| `requirements.txt` | Python dependencies |
| `pyproject.toml` | Black, Mypy, Bandit config |
| `pytest.ini` | Pytest configuration |
| `alembic.ini` | Alembic migrations config |

---

## 7. File Naming Conventions

### 7.1 Python Files

- **Models**: Singular noun (e.g., `user.py`, `expense_item.py`)
- **Schemas**: Match model name (e.g., `user.py` for User schemas)
- **API Endpoints**: Plural noun (e.g., `expenses.py`, `periods.py`)
- **Services**: Noun + `_service.py` (e.g., `auth_service.py`)
- **Tests**: `test_` prefix (e.g., `test_reconciliation.py`)

### 7.2 Dash Components

- **Tabs**: `tab{number}_{name}.py` (e.g., `tab1_period_setup.py`)
- **Layouts**: `{name}_layout.py` (e.g., `main_layout.py`)
- **Callbacks**: `{feature}_callbacks.py` (e.g., `expense_callbacks.py`)

### 7.3 Database Migrations

- **Format**: `{revision_id}_{description}.py`
- **Example**: `001_initial_schema.py`
- **Generated by**: `alembic revision --autogenerate -m "description"`

***

## 8. Import Patterns

### 8.1 Absolute Imports

**Always use absolute imports from project root**:

```python
# ✅ Correct
from app.models.user import User
from app.schemas.auth import LoginRequest
from app.core.config import settings

# ❌ Incorrect
from ..models.user import User
from ...core.config import settings
```

### 8.2 Import Organization

**Order imports by type** (enforced by isort):

```python
# 1. Standard library
import os
from typing import List, Optional

# 2. Third-party
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# 3. Local application
from app.models.user import User
from app.schemas.auth import LoginRequest
from app.core.security import get_current_user
```

### 8.3 Circular Import Prevention

**Use TYPE_CHECKING for type hints**:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User

def process_user(user: "User") -> None:
    # Type hint doesn't trigger import at runtime
    pass
```

***

**END OF PROJECT_STRUCTURE.md**

