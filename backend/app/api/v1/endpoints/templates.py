import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import template as crud_template
from app.models.user import User
from app.schemas.template import TemplateCreate, TemplateResponse, TemplateApply, TemplateUpdate

router = APIRouter()


@router.post("/from-period", response_model=TemplateResponse)
def create_template_from_period(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    template_in: TemplateCreate
) -> Any:
    """Create a template based on data from an existing period."""
    return crud_template.create_template_from_period(
        db=db,
        user_id=current_user.id,
        template_name=template_in.template_name,
        template_type=template_in.template_type,
        source_period_id=template_in.source_period_id
    )


@router.post("/{template_id}/apply")
def apply_template_to_period(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    template_id: uuid.UUID,
    apply_in: TemplateApply
) -> Any:
    """Apply template data to a target period."""
    summary = crud_template.apply_template_to_period(
        db=db,
        user_id=current_user.id,
        template_id=template_id,
        target_period_id=apply_in.target_period_id
    )
    if "error" in summary:
        raise HTTPException(status_code=404, detail=summary["error"])
    return summary


@router.get("/", response_model=List[TemplateResponse])
def list_templates(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """List all user's templates."""
    return crud_template.list_templates(db=db, user_id=current_user.id)


@router.patch("/{template_id}", response_model=TemplateResponse)
def update_template(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    template_id: uuid.UUID,
    template_in: TemplateUpdate
) -> Any:
    """Update template name or set as default."""
    template = crud_template.update_template(
        db=db,
        user_id=current_user.id,
        template_id=template_id,
        template_name=template_in.template_name,
        is_default=template_in.is_default
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.delete("/{template_id}")
def delete_template(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    template_id: uuid.UUID
) -> Any:
    """Delete a template."""
    success = crud_template.delete_template(db=db, user_id=current_user.id, template_id=template_id)
    if not success:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"status": "success"}
