from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from croniter import croniter
from datetime import datetime

router = APIRouter()

class CronCheckResponse(BaseModel):
    shouldRun: bool

@router.get("/check", response_model=CronCheckResponse)
def check_cron(cron: str = Query(..., description="Cron expression"), datetime_str: str = Query(..., description="ISO format datetime")):
    try:
        dt = datetime.fromisoformat(datetime_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid datetime format. Use ISO format.")
    try:
        # croniter.match returns True if dt matches the cron expression
        should_run = croniter.match(cron, dt)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid cron expression.")
    return CronCheckResponse(shouldRun=should_run) 