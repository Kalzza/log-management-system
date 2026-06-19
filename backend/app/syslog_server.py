import asyncio
import socket
from datetime import datetime
from app.database import SessionLocal
from app.models import Log
from app.config import get_settings
import uuid
import json
import re

settings = get_settings()

class SyslogServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 514):
        self.host = host
        self.port = port
        self.running = False
    
    async def start(self):
        """Start the syslog server"""
        self.running = True
        loop = asyncio.get_event_loop()
        
        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.host, self.port))
        sock.setblocking(False)
        
        print(f"Syslog server listening on {self.host}:{self.port}")
        
        try:
            while self.running:
                try:
                    data, addr = sock.recvfrom(65535)
                    # Handle in background
                    asyncio.create_task(self.process_message(data, addr))
                except BlockingIOError:
                    await asyncio.sleep(0.01)
        finally:
            sock.close()
    
    async def process_message(self, data: bytes, addr: tuple):
        """Process incoming syslog message"""
        try:
            message = data.decode('utf-8', errors='ignore')
            log_entry = self.parse_syslog(message, addr[0])
            
            if log_entry:
                db = SessionLocal()
                try:
                    # Find tenant by source or use default
                    log = Log(**log_entry)
                    db.add(log)
                    db.commit()
                    print(f"Log stored: {log.id}")
                finally:
                    db.close()
        except Exception as e:
            print(f"Error processing syslog: {e}")
    
    def parse_syslog(self, message: str, source_ip: str) -> dict:
        """Parse RFC 3164 or RFC 5424 syslog message"""
        try:
            # Try RFC 5424 format first
            if message.startswith("<"):
                match = re.match(r'<(\d+)>(\d+)\s([\w-]+)\s([\w-]+)\s([\w.-]+)\s\[(\d+)\]:\s(.*)', message)
                if match:
                    priority, version, timestamp, hostname, app_name, proc_id, msg = match.groups()
                    severity = int(priority) % 8
                    facility = int(priority) // 8
                    
                    return {
                        "id": str(uuid.uuid4()),
                        "tenant_id": self.get_tenant_for_source(hostname),
                        "timestamp": datetime.utcnow(),
                        "source": source_ip,
                        "host": hostname,
                        "process": app_name,
                        "event_type": app_name or "unknown",
                        "severity": severity,
                        "raw": {
                            "priority": priority,
                            "facility": facility,
                            "version": version,
                            "message": msg
                        }
                    }
                
                # Try RFC 3164 format
                match = re.match(r'<(\d+)>([\w\s:]+)\s([\w.-]+)\s([\w\[\]]+):\s(.*)', message)
                if match:
                    priority, timestamp, hostname, tag, msg = match.groups()
                    severity = int(priority) % 8
                    facility = int(priority) // 8
                    
                    return {
                        "id": str(uuid.uuid4()),
                        "tenant_id": self.get_tenant_for_source(hostname),
                        "timestamp": datetime.utcnow(),
                        "source": source_ip,
                        "host": hostname,
                        "process": tag,
                        "event_type": tag or "unknown",
                        "severity": severity,
                        "raw": {
                            "priority": priority,
                            "facility": facility,
                            "message": msg
                        }
                    }
            
            # Try JSON format
            try:
                data = json.loads(message)
                return {
                    "id": str(uuid.uuid4()),
                    "tenant_id": self.get_tenant_for_source(data.get("hostname", "unknown")),
                    "timestamp": datetime.utcnow(),
                    "source": source_ip,
                    "host": data.get("hostname"),
                    "event_type": data.get("event_type", "unknown"),
                    "severity": data.get("severity", 5),
                    "user": data.get("user"),
                    "src_ip": data.get("src_ip"),
                    "dst_ip": data.get("dst_ip"),
                    "action": data.get("action"),
                    "raw": data
                }
            except json.JSONDecodeError:
                pass
            
            # Plain text fallback
            return {
                "id": str(uuid.uuid4()),
                "tenant_id": self.get_tenant_for_source(source_ip),
                "timestamp": datetime.utcnow(),
                "source": source_ip,
                "event_type": "unknown",
                "severity": 5,
                "raw": {"message": message}
            }
        except Exception as e:
            print(f"Parse error: {e}")
            return None
    
    def get_tenant_for_source(self, hostname: str) -> str:
        """Map source hostname to tenant - for now use a default"""
        # In production, implement tenant discovery logic
        from app.models import Tenant
        db = SessionLocal()
        try:
            tenant = db.query(Tenant).first()
            return tenant.id if tenant else "default"
        finally:
            db.close()
    
    async def stop(self):
        """Stop the syslog server"""
        self.running = False

# Global server instance
syslog_server = SyslogServer(host=settings.syslog_host, port=settings.syslog_port)

async def start_syslog_server():
    """Start syslog server"""
    await syslog_server.start()

def stop_syslog_server():
    """Stop syslog server"""
    asyncio.create_task(syslog_server.stop())
