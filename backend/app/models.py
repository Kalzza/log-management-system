from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, JSON, ForeignKey, Index, func
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users = relationship("User", back_populates="tenant")
    logs = relationship("Log", back_populates="tenant")
    alerts = relationship("AlertRule", back_populates="tenant")

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="viewer")  # admin, viewer
    tenant_id = Column(String, ForeignKey("tenants.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="users")

class Log(Base):
    __tablename__ = "logs"
    
    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), index=True)
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)
    source = Column(String, index=True)
    vendor = Column(String, index=True)
    product = Column(String, index=True)
    event_type = Column(String, index=True)
    event_subtype = Column(String)
    severity = Column(Integer)
    action = Column(String)
    
    # Network
    src_ip = Column(String, index=True)
    src_port = Column(Integer)
    dst_ip = Column(String, index=True)
    dst_port = Column(Integer)
    protocol = Column(String)
    
    # Identity
    user = Column(String, index=True)
    host = Column(String, index=True)
    process = Column(String)
    
    # HTTP
    url = Column(String)
    http_method = Column(String)
    status_code = Column(Integer)
    
    # Rules
    rule_name = Column(String)
    rule_id = Column(String)
    
    # Cloud
    cloud_account_id = Column(String)
    cloud_region = Column(String)
    cloud_service = Column(String)
    
    # Raw data
    raw = Column(JSON)
    tags = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="logs")
    
    __table_args__ = (
        Index('idx_tenant_timestamp', 'tenant_id', 'timestamp'),
        Index('idx_source_event', 'source', 'event_type'),
        Index('idx_src_ip', 'src_ip'),
        Index('idx_user', 'user'),
    )

class AlertRule(Base):
    __tablename__ = "alert_rules"
    
    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), index=True)
    name = Column(String)
    description = Column(Text)
    condition = Column(JSON)
    enabled = Column(Boolean, default=True)
    webhook_url = Column(String)
    email_recipients = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="alerts")

class AlertEvent(Base):
    __tablename__ = "alert_events"
    
    id = Column(String, primary_key=True, index=True)
    alert_rule_id = Column(String, ForeignKey("alert_rules.id"))
    log_id = Column(String, ForeignKey("logs.id"))
    matched_at = Column(DateTime, default=datetime.utcnow)
    webhook_sent = Column(Boolean, default=False)
    webhook_response = Column(String)
    
    __table_args__ = (
        Index('idx_alert_rule_matched', 'alert_rule_id', 'matched_at'),
    )
