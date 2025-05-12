from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from croniter import croniter
from datetime import datetime

router = APIRouter()

class CronCheckRequest(BaseModel):
    cron: str
    datetime: str  # ISO 格式

class CronCheckResponse(BaseModel):
    shouldRun: bool

@router.post("/check", response_model=CronCheckResponse)
def check_cron(req: CronCheckRequest):
    try:
        dt = datetime.fromisoformat(req.datetime)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid datetime format. Use ISO format.")
    try:
        # croniter.match returns True if dt matches the cron expression
        should_run = croniter.match(req.cron, dt)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid cron expression.")
    return CronCheckResponse(shouldRun=should_run) 