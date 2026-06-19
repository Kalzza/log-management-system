from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.database import get_db
from app.models import Log, User
from app.schemas import LogCreate, LogResponse, LogSearchFilter
from app.security import get_current_user
import uuid
from datetime import datetime, timedelta

router = APIRouter(prefix="/logs", tags=["logs"])

@router.post("/", response_model=LogResponse)
async def create_log(log: LogCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new log entry"""
    new_log = Log(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        timestamp=log.timestamp or datetime.utcnow(),
        source=log.source,
        vendor=log.vendor,
        product=log.product,
        event_type=log.event_type,
        event_subtype=log.event_subtype,
        severity=log.severity,
        action=log.action,
        src_ip=log.src_ip,
        src_port=log.src_port,
        dst_ip=log.dst_ip,
        dst_port=log.dst_port,
        protocol=log.protocol,
        user=log.user,
        host=log.host,
        process=log.process,
        url=log.url,
        http_method=log.http_method,
        status_code=log.status_code,
        rule_name=log.rule_name,
        rule_id=log.rule_id,
        cloud_account_id=log.cloud_account_id,
        cloud_region=log.cloud_region,
        cloud_service=log.cloud_service,
        raw=log.raw,
        tags=log.tags or []
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log

@router.get("/", response_model=list[LogResponse])
async def search_logs(
    filter: LogSearchFilter = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search logs with filters"""
    query = db.query(Log).filter(Log.tenant_id == current_user.tenant_id)
    
    if filter.source:
        query = query.filter(Log.source == filter.source)
    if filter.event_type:
        query = query.filter(Log.event_type == filter.event_type)
    if filter.severity_min is not None:
        query = query.filter(Log.severity >= filter.severity_min)
    if filter.severity_max is not None:
        query = query.filter(Log.severity <= filter.severity_max)
    if filter.src_ip:
        query = query.filter(Log.src_ip == filter.src_ip)
    if filter.user:
        query = query.filter(Log.user == filter.user)
    
    if filter.start_time:
        query = query.filter(Log.timestamp >= filter.start_time)
    if filter.end_time:
        query = query.filter(Log.timestamp <= filter.end_time)
    
    return query.order_by(Log.timestamp.desc()).offset(filter.offset).limit(filter.limit).all()

@router.get("/{log_id}", response_model=LogResponse)
async def get_log(
    log_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific log"""
    log = db.query(Log).filter(
        and_(Log.id == log_id, Log.tenant_id == current_user.tenant_id)
    ).first()
    
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")
    return log

@router.get("/stats/summary")
async def get_log_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get log statistics"""
    total_logs = db.query(Log).filter(Log.tenant_id == current_user.tenant_id).count()
    
    # Last 24 hours
    yesterday = datetime.utcnow() - timedelta(days=1)
    logs_24h = db.query(Log).filter(
        and_(
            Log.tenant_id == current_user.tenant_id,
            Log.timestamp >= yesterday
        )
    ).count()
    
    # Top event types
    top_events = db.query(Log.event_type).filter(
        Log.tenant_id == current_user.tenant_id
    ).group_by(Log.event_type).count()
    
    return {
        "total_logs": total_logs,
        "logs_last_24h": logs_24h,
        "top_event_types": top_events
    }
