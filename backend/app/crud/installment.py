from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.installment_item import InstallmentItem
from app.models.installment_payment import InstallmentPayment
from app.schemas.installment import (
    InstallmentItemCreate,
    InstallmentPaymentCreate,
)

def create_installment_item(
    db: Session, user_id: UUID, item_in: InstallmentItemCreate
) -> InstallmentItem:
    item = InstallmentItem(
        user_id=user_id,
        item_name=item_in.item_name,
        total_price=item_in.total_price,
        currency_id=item_in.currency_id,
        initial_period_id=item_in.initial_period_id,
        remaining_balance=item_in.total_price, # Initially equals total
        monthly_payment_amount=item_in.monthly_payment_amount,
        months_to_pay=item_in.months_to_pay,
        notes=item_in.notes,
        status="ACTIVE"
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

def get_installment_items(
    db: Session, user_id: UUID, status: Optional[str] = None
) -> List[InstallmentItem]:
    stmt = select(InstallmentItem).where(InstallmentItem.user_id == user_id)
    if status:
        stmt = stmt.where(InstallmentItem.status == status)
    stmt = stmt.order_by(InstallmentItem.created_at.desc())
    return db.execute(stmt).scalars().all()

def get_installment_item(db: Session, item_id: UUID) -> Optional[InstallmentItem]:
    return db.get(InstallmentItem, item_id)

def create_installment_payment(
    db: Session, 
    item_id: UUID, 
    period_id: UUID, 
    payment_in: InstallmentPaymentCreate
) -> InstallmentPayment:
    # Get item first to lock it? Or just standard update.
    # We should likely use row locking if finding concurrency, but for single user app standard is fine.
    item = db.get(InstallmentItem, item_id)
    if not item:
        return None

    payment = InstallmentPayment(
        installment_item_id=item_id,
        calculation_period_id=period_id,
        payment_amount=payment_in.payment_amount,
        payment_date=payment_in.payment_date,
        notes=payment_in.notes
    )
    db.add(payment)
    
    # Update item balance
    item.remaining_balance -= payment_in.payment_amount
    
    # Check status
    if item.remaining_balance <= 0:
        item.remaining_balance = Decimal("0.00") # Cap at 0
        item.status = "PAID_OFF"
    
    db.commit()
    db.refresh(payment)
    db.refresh(item)
    return payment

def get_installment_payments(
    db: Session, item_id: UUID
) -> List[InstallmentPayment]:
    stmt = select(InstallmentPayment).where(
        InstallmentPayment.installment_item_id == item_id
    ).order_by(InstallmentPayment.payment_date.desc())
    return db.execute(stmt).scalars().all()

def delete_installment_payment(
    db: Session, payment: InstallmentPayment
) -> None:
    item = getattr(payment, "installment_item") # relationship should be loaded or lazy
    if not item:
        item = db.get(InstallmentItem, payment.installment_item_id)
        
    # Revert balance
    if item:
        item.remaining_balance += payment.payment_amount
        if item.status == "PAID_OFF" and item.remaining_balance > 0:
            item.status = "ACTIVE"
            
    db.delete(payment)
    db.commit()
