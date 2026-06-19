from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# ===== User & Auth Schemas =====
class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: str = "viewer"

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: str
    tenant_id: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class LoginRequest(BaseModel):
    username: str
    password: str

# ===== Log Schemas =====
class LogBase(BaseModel):
    source: str
    vendor: Optional[str] = None
    product: Optional[str] = None
    event_type: str
    event_subtype: Optional[str] = None
    severity: int = 5
    action: Optional[str] = None
    
    src_ip: Optional[str] = None
    src_port: Optional[int] = None
    dst_ip: Optional[str] = None
    dst_port: Optional[int] = None
    protocol: Optional[str] = None
    
    user: Optional[str] = None
    host: Optional[str] = None
    process: Optional[str] = None
    
    url: Optional[str] = None
    http_method: Optional[str] = None
    status_code: Optional[int] = None
    
    rule_name: Optional[str] = None
    rule_id: Optional[str] = None
    
    cloud_account_id: Optional[str] = None
    cloud_region: Optional[str] = None
    cloud_service: Optional[str] = None
    
    raw: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = []

class LogCreate(LogBase):
    timestamp: Optional[datetime] = None

class LogResponse(LogBase):
    id: str
    tenant_id: str
    timestamp: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

class LogSearchFilter(BaseModel):
    source: Optional[str] = None
    event_type: Optional[str] = None
    severity_min: Optional[int] = None
    severity_max: Optional[int] = None
    src_ip: Optional[str] = None
    user: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = 100
    offset: int = 0

# ===== Alert Schemas =====
class AlertRuleBase(BaseModel):
    name: str
    description: Optional[str] = None
    condition: Dict[str, Any]
    enabled: bool = True
    webhook_url: Optional[str] = None
    email_recipients: Optional[List[str]] = []

class AlertRuleCreate(AlertRuleBase):
    pass

class AlertRuleResponse(AlertRuleBase):
    id: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AlertEventResponse(BaseModel):
    id: str
    alert_rule_id: str
    log_id: str
    matched_at: datetime
    webhook_sent: bool
    webhook_response: Optional[str] = None
    
    class Config:
        from_attributes = True

# ===== Tenant Schemas =====
class TenantBase(BaseModel):
    name: str

class TenantCreate(TenantBase):
    pass

class TenantResponse(TenantBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# ===== Dashboard Schemas =====
class DashboardStats(BaseModel):
    total_logs: int
    logs_last_24h: int
    alerts_triggered: int
    active_alerts: int
    top_event_types: List[Dict[str, Any]]
    top_sources: List[Dict[str, Any]]
    top_users: List[Dict[str, Any]]

class TimeSeriesData(BaseModel):
    timestamp: datetime
    count: int
    severity_levels: Dict[str, int]

# ===== Error Schemas =====
class ErrorResponse(BaseModel):
    detail: str
    status_code: int
