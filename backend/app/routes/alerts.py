from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.database import get_db
from app.models import AlertRule, AlertEvent, User, Log
from app.schemas import AlertRuleCreate, AlertRuleResponse, AlertEventResponse
from app.security import get_current_user, get_current_admin
import uuid
from datetime import datetime
import httpx

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.post("/rules", response_model=AlertRuleResponse)
async def create_alert_rule(
    rule: AlertRuleCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new alert rule (admin only)"""
    new_rule = AlertRule(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        name=rule.name,
        description=rule.description,
        condition=rule.condition,
        enabled=rule.enabled,
        webhook_url=rule.webhook_url,
        email_recipients=rule.email_recipients or []
    )
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    return new_rule

@router.get("/rules", response_model=list[AlertRuleResponse])
async def list_alert_rules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all alert rules for tenant"""
    rules = db.query(AlertRule).filter(AlertRule.tenant_id == current_user.tenant_id).all()
    return rules

@router.get("/rules/{rule_id}", response_model=AlertRuleResponse)
async def get_alert_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific alert rule"""
    rule = db.query(AlertRule).filter(
        and_(AlertRule.id == rule_id, AlertRule.tenant_id == current_user.tenant_id)
    ).first()
    
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert rule not found")
    return rule

@router.put("/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: str,
    rule: AlertRuleCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update an alert rule (admin only)"""
    db_rule = db.query(AlertRule).filter(
        and_(AlertRule.id == rule_id, AlertRule.tenant_id == current_user.tenant_id)
    ).first()
    
    if not db_rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert rule not found")
    
    db_rule.name = rule.name
    db_rule.description = rule.description
    db_rule.condition = rule.condition
    db_rule.enabled = rule.enabled
    db_rule.webhook_url = rule.webhook_url
    db_rule.email_recipients = rule.email_recipients
    db_rule.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_rule)
    return db_rule

@router.delete("/rules/{rule_id}")
async def delete_alert_rule(
    rule_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete an alert rule (admin only)"""
    rule = db.query(AlertRule).filter(
        and_(AlertRule.id == rule_id, AlertRule.tenant_id == current_user.tenant_id)
    ).first()
    
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert rule not found")
    
    db.delete(rule)
    db.commit()
    return {"message": "Alert rule deleted"}

@router.get("/events", response_model=list[AlertEventResponse])
async def list_alert_events(
    rule_id: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List alert events"""
    query = db.query(AlertEvent).join(AlertRule).filter(
        AlertRule.tenant_id == current_user.tenant_id
    )
    
    if rule_id:
        query = query.filter(AlertEvent.alert_rule_id == rule_id)
    
    return query.order_by(AlertEvent.matched_at.desc()).limit(100).all()

async def check_alert_condition(condition: dict, log: dict) -> bool:
    """Check if log matches alert condition"""
    field = condition.get("field")
    operator = condition.get("operator")
    value = condition.get("value")
    
    log_value = log.get(field)
    
    if operator == "==":
        return log_value == value
    elif operator == "!=":
        return log_value != value
    elif operator == ">":
        return log_value > value
    elif operator == "<":
        return log_value < value
    elif operator == ">=":
        return log_value >= value
    elif operator == "<=":
        return log_value <= value
    elif operator == "contains":
        return value in str(log_value)
    elif operator == "in":
        return log_value in value
    
    return False

async def send_webhook(url: str, payload: dict):
    """Send webhook notification"""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Webhook failed: {e}")

@router.post("/check/{log_id}")
async def check_alerts_for_log(
    log_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check and trigger alerts for a log"""
    log = db.query(Log).filter(
        and_(Log.id == log_id, Log.tenant_id == current_user.tenant_id)
    ).first()
    
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")
    
    rules = db.query(AlertRule).filter(
        and_(AlertRule.tenant_id == current_user.tenant_id, AlertRule.enabled == True)
    ).all()
    
    triggered_alerts = []
    log_dict = {
        "source": log.source,
        "event_type": log.event_type,
        "severity": log.severity,
        "user": log.user,
        "host": log.host,
        "src_ip": log.src_ip,
        "action": log.action
    }
    
    for rule in rules:
        if await check_alert_condition(rule.condition, log_dict):
            alert_event = AlertEvent(
                id=str(uuid.uuid4()),
                alert_rule_id=rule.id,
                log_id=log.id,
                matched_at=datetime.utcnow()
            )
            db.add(alert_event)
            
            if rule.webhook_url:
                await send_webhook(rule.webhook_url, {
                    "alert_rule_id": rule.id,
                    "log_id": log.id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "log": log_dict
                })
                alert_event.webhook_sent = True
            
            triggered_alerts.append(rule.id)
    
    db.commit()
    return {"triggered_alerts": triggered_alerts}
