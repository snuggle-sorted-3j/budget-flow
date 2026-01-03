"""API v1 router combining all endpoint routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import accounts, auth, balance_snapshots, periods, system

api_router = APIRouter()

api_router.include_router(accounts.router, prefix="/accounts", tags=["Accounts"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(balance_snapshots.router, tags=["Balance Snapshots"])  # No prefix to support /periods/{id}/snapshots
api_router.include_router(periods.router, prefix="/periods", tags=["Periods"])
api_router.include_router(system.router, prefix="/system", tags=["System"])



