from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from models import Report
from schemas.report import ReportRead, ReportList, ReportGenerateRequest

router = APIRouter()


@router.get("/reports", response_model=ReportList)
async def list_reports(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Report).order_by(Report.created_at.desc()).limit(50)
    )
    reports = result.scalars().all()
    total = (await db.execute(select(func.count(Report.id)))).scalar_one()
    return ReportList(items=list(reports), total=total)


@router.get("/reports/{report_id}", response_model=ReportRead)
async def get_report(report_id: str, db: AsyncSession = Depends(get_db)):
    from fastapi import HTTPException
    import uuid as _uuid
    try:
        uid = _uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report ID")
    result = await db.execute(select(Report).where(Report.id == uid))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.post("/reports/generate")
async def generate_report(
    request: ReportGenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    from services.reporting import ReportingService
    background_tasks.add_task(
        ReportingService.generate_and_send,
        report_type=request.report_type,
        send_email=request.send_email,
        send_slack=request.send_slack,
    )
    return {"status": "queued", "report_type": request.report_type}
