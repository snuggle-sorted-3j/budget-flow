from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import Response, StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
import json
import io

from app.api import deps
from app.services import export_service
from app.models.user import User
from app.models.calculation_period import CalculationPeriod

router = APIRouter()

@router.get("/period/{period_id}/csv")
def export_period_csv(
    period_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Export all transactions for a specific period as a CSV file."""
    period = db.query(CalculationPeriod).filter(
        CalculationPeriod.id == period_id, 
        CalculationPeriod.user_id == current_user.id
    ).first()
    
    if not period:
        raise HTTPException(status_code=404, detail="Period not found")
        
    csv_data = export_service.generate_period_csv(db, current_user.id, period_id)
    
    filename = f"BudgetFlow_Period_{period.period_name}_{datetime.now().strftime('%Y%m%d')}.csv"
    
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/period/{period_id}/reconciliation-report")
def export_reconciliation_report(
    period_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Generate and export a PDF reconciliation report."""
    period = db.query(CalculationPeriod).filter(
        CalculationPeriod.id == period_id, 
        CalculationPeriod.user_id == current_user.id
    ).first()
    
    if not period:
        raise HTTPException(status_code=404, detail="Period not found")
        
    pdf_data = export_service.generate_reconciliation_pdf(db, current_user.id, period_id)
    
    filename = f"BudgetFlow_Reconciliation_{period.period_name}.pdf"
    
    return Response(
        content=pdf_data,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/annual-summary")
def export_annual_summary(
    year: int = Query(..., ge=2000, le=2100),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Export an annual financial summary for all periods in a year."""
    csv_data = export_service.generate_annual_csv(db, current_user.id, year)
    
    filename = f"BudgetFlow_Annual_Summary_{year}.csv"
    
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/full-backup")
def export_full_backup(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Export all user data as a JSON backup file."""
    backup_dict = export_service.generate_full_backup_json(db, current_user.id)
    
    filename = f"BudgetFlow_Backup_{datetime.now().strftime('%Y%m%d')}.json"
    
    return JSONResponse(
        content=backup_dict,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/import/backup")
async def import_backup(
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Import user data from a previously exported JSON backup file."""
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a JSON file.")
        
    try:
        content = await file.read()
        backup_data = json.loads(content)
        
        result = export_service.import_backup_json(db, current_user.id, backup_data)
        
        return {
            "message": "Backup imported successfully",
            "summary": result
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file content.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during import: {str(e)}")
