from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import expense_category as crud_category
from app.models.user import User
from app.schemas.expense_category import ExpenseCategoryCreate, ExpenseCategoryResponse

router = APIRouter()


@router.post("/", response_model=ExpenseCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    *,
    db: Session = Depends(deps.get_db),
    category_in: ExpenseCategoryCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Create a new expense category.
    """
    # Existence check for parent category
    if category_in.parent_category_id:
        parent = crud_category.get_category(db=db, user_id=current_user.id, category_id=category_in.parent_category_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent category not found or access denied",
            )
            
    return crud_category.create_category(db=db, user_id=current_user.id, data=category_in)


@router.get("/", response_model=List[ExpenseCategoryResponse])
def read_categories(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve user's expense categories.
    """
    return crud_category.list_categories(db=db, user_id=current_user.id)
