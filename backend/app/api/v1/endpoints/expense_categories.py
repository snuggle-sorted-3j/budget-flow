from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import expense_category as crud_category
from app.models.user import User
from app.schemas.expense_category import ExpenseCategoryCreate, ExpenseCategoryResponse, ExpenseCategoryUpdate

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


@router.post("/initialize", response_model=List[ExpenseCategoryResponse], status_code=status.HTTP_201_CREATED)
def initialize_categories(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Initialize system categories if they don't exist.
    """
    return crud_category.create_system_categories(db=db, user_id=current_user.id)


@router.get("/", response_model=List[ExpenseCategoryResponse])
def read_categories(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    include_inactive: bool = False,
) -> Any:
    """
    Retrieve user's expense categories.
    """
    return crud_category.list_categories(db=db, user_id=current_user.id, include_inactive=include_inactive)


@router.patch("/{category_id}", response_model=ExpenseCategoryResponse)
def update_category(
    *,
    db: Session = Depends(deps.get_db),
    category_id: UUID,
    category_in: ExpenseCategoryUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Update an expense category.
    """
    if category_in.parent_category_id:
        parent = crud_category.get_category(db=db, user_id=current_user.id, category_id=category_in.parent_category_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent category not found or access denied",
            )
            
    category = crud_category.update_category(db=db, user_id=current_user.id, category_id=category_id, data=category_in)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    return category


@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
def delete_category(
    *,
    db: Session = Depends(deps.get_db),
    category_id: UUID,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Deactivate an expense category.
    """
    category = crud_category.get_category(db=db, user_id=current_user.id, category_id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
        
    if category.is_system_category:
        raise HTTPException(status_code=400, detail="Cannot delete system category")
        
    # Check for existing expense items
    if category.expense_items:
        raise HTTPException(status_code=400, detail="Cannot delete category with existing expenses")
        
    updated_category = crud_category.deactivate_category(db=db, user_id=current_user.id, category_id=category_id)
    return {"message": "Category deactivated successfully"}
