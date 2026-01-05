"""API v1 router combining all endpoint routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    accounts,
    auth,
    balance_snapshots,
    currencies,
    expense_categories,
    expenses,
    incomes,
    periods,
    reconciliation,
    periods,
    reconciliation,
    system,
    system,
    investments,
    suspended_expenses,
)

api_router = APIRouter()

api_router.include_router(accounts.router, prefix="/accounts", tags=["Accounts"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(balance_snapshots.router, tags=["Balance Snapshots"])
api_router.include_router(currencies.router, prefix="/currencies", tags=["Currencies"])
api_router.include_router(
    expense_categories.router, prefix="/expense-categories", tags=["Expense Categories"]
)
api_router.include_router(incomes.router, tags=["Incomes"])
api_router.include_router(expenses.router, tags=["Expenses"])
api_router.include_router(periods.router, prefix="/periods", tags=["Periods"])
api_router.include_router(reconciliation.router, tags=["Reconciliation"])
api_router.include_router(system.router, prefix="/system", tags=["System"])
api_router.include_router(investments.router, prefix="/investments", tags=["Investments"])
api_router.include_router(suspended_expenses.router, prefix="/suspended", tags=["Suspended Expenses"])



