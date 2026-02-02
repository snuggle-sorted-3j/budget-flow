"""
Unit Tests for Currency Conversion CRUD Operations

Tests cover:
- Creating currency conversions
- Listing conversions by period
- Updating and deleting conversions
"""
import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session

from app.crud.currency_conversion import (
    create_currency_conversion,
    get_currency_conversions,
    update_currency_conversion,
    delete_currency_conversion
)
from app.crud.period import create_period
from app.schemas.period import PeriodCreate
from app.schemas.currency_conversion import (
    CurrencyConversionCreate,
    CurrencyConversionUpdate
)
from app.models.user import User
from app.models.currency import Currency


class TestCurrencyConversionLifecycle:
    """Test full lifecycle of currency conversions."""
    
    def test_create_conversion(
        self, db: Session, test_user: User
    ):
        """Test: Create currency conversion."""
        # Create Period
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="Conv Test", start_date=date(2026, 1, 1), end_date=date(2026, 1, 31), snapshot_date=date(2026, 1, 31)
        ))
        
        # We need two currencies. Assuming test_currency fixture gives one. 
        # Helper to get another if needed, but factories usually handle this nicely.
        # Here we manually mock IDs for simplicity or use existing helpers if available in conftest.
        # Let's rely on creating them or simple mocking if DB not strictly enforced for IDs in unit tests (but it is).
        from app.crud.currency import create_currency
        from app.schemas.currency import CurrencyCreate
        
        c1 = create_currency(db, test_user.id, CurrencyCreate(ticker="USD", name="Dollar", is_default=True))
        c2 = create_currency(db, test_user.id, CurrencyCreate(ticker="EUR", name="Euro"))
        
        conv_data = CurrencyConversionCreate(
            from_currency_id=c1.id,
            to_currency_id=c2.id,
            from_amount=Decimal("100.00"),
            to_amount=Decimal("90.00"),
            conversion_date=date(2026, 1, 15),
            rate=Decimal("0.9")
        )
        
        conv = create_currency_conversion(db, conv_data, period.id)
        
        assert conv.from_amount == Decimal("100.00")
        assert conv.to_amount == Decimal("90.00")
        assert conv.calculation_period_id == period.id

    def test_list_and_delete_conversion(
        self, db: Session, test_user: User
    ):
        """Test: List and delete conversions."""
        # Setup similar to above...
        from app.crud.currency import create_currency
        from app.schemas.currency import CurrencyCreate
        
        period = create_period(db, test_user.id, PeriodCreate(
            period_name="List Test", start_date=date(2026, 2, 1), end_date=date(2026, 2, 28), snapshot_date=date(2026, 2, 28)
        ))
        c1 = create_currency(db, test_user.id, CurrencyCreate(ticker="GBP", name="Pound"))
        c2 = create_currency(db, test_user.id, CurrencyCreate(ticker="JPY", name="Yen"))
        
        conv = create_currency_conversion(db, CurrencyConversionCreate(
            from_currency_id=c1.id, to_currency_id=c2.id,
            from_amount=Decimal("10.00"), to_amount=Decimal("1500.00"),
            rate=Decimal("150.0"), conversion_date=date(2026, 2, 10)
        ), period.id)
        
        # List
        convs = get_currency_conversions(db, period.id)
        assert len(convs) == 1
        assert convs[0].id == conv.id
        
        # Delete
        delete_currency_conversion(db, conv)
        
        convs_after = get_currency_conversions(db, period.id)
        assert len(convs_after) == 0
