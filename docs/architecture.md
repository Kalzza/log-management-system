# Log Management System - Architecture

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              LOG SOURCES (4+ Ingestion Points)              │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │ Firewall │ Syslog   │ HTTP API │ Files    │ Custom   │  │
│  │ (UDP514) │ (TCP514) │ (POST)   │ (Batch)  │Simulators│  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
└─────────────────────────────────────────────────���───────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│            COLLECTOR LAYER (Data Ingestion)                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ • Syslog Receiver (UDP/TCP 514)                      │  │
│  │ • HTTP Ingest Handler (/ingest endpoint)            │  │
│  │ • File Batch Processor                              │  │
│  │ • Log Parser & Format Detector                      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│         NORMALIZATION LAYER (Schema Transformation)        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Unified Log Schema:                                  │  │
│  │ • @timestamp, tenant, source, vendor, product       │  │
│  │ • event_type, event_subtype, severity, action       │  │
│  │ • src_ip, src_port, dst_ip, dst_port, protocol      │  │
│  │ • user, host, process, url, status_code             │  │
│  │ • rule_name, rule_id, raw, _tags                    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│          BACKEND API LAYER (FastAPI - Port 8000)           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Endpoints:                                          │   │
│  │ • POST   /ingest          - Receive logs           │   │
│  │ • GET    /search          - Query logs             │   │
│  │ • POST   /alerts          - Create alert rules     │   │
│  │ • GET    /alerts          - List alerts            │   │
│  │ • POST   /auth/login      - User authentication    │   │
│  │ • GET    /dashboard       - Summary statistics     │   │
│  │ • GET    /users           - User management (Admin)│   │
│  └─────────────────────────────────────────────────────┘   │
│  Features:                                                  │
│  • JWT Authentication                                       │
│  • Multi-tenant Isolation                                   │
│  • RBAC (Admin/Viewer roles)                               │
│  • Rate Limiting                                            │
│  • Data Validation (Pydantic)                              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│      DATABASE LAYER (PostgreSQL + TimescaleDB)             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Tables:                                             │   │
│  │ • logs (partitioned by time)                       │   │
│  │ • alerts (alert rules & history)                   │   │
│  │ • users (user accounts)                            │   │
│  │ • tenants (multi-tenant config)                    │   │
│  │ • rbac_policies (role-based access)                │   │
│  │ • retention_policies (data cleanup)                │   │
│  └─────────────────────────────────────────────────────┘   │
│  Features:                                                  │
│  • Time-series optimization                                │
│  • GIN Index for full-text search                          │
│  • Automatic partitioning (7-day retention)                │
│  • Row-level security for multi-tenant                     │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│       FRONTEND LAYER (React + TypeScript - Port 3000)      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Pages:                                              │   │
│  │ • Dashboard     - Overview & statistics            │   │
│  │ • Search        - Advanced log search & filter     │   │
│  │ • Alerts        - Alert rules & notifications      │   │
│  │ • Admin Panel   - User & tenant management         │   │
│  └─────────────────────────────────────────────────────┘   │
│  Components:                                                │
│  • Timeline Chart (log events over time)                    │
│  • Top N Tables (IPs, users, event types)                  │
│  • Advanced Filters (by time, source, tenant, severity)    │
│  • Real-time Dashboard                                      │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Data Flow

```
1. LOG INGESTION
   Source Log → Parser → Normalizer → Queue (in-memory)
   
2. STORAGE
   Queue → Backend → Database (PostgreSQL)
   
3. SEARCH & RETRIEVAL
   User Query → API Endpoint → Database Query → Result
   
4. ALERTING
   New Log → Check Rules → Match Found → Send Alert
   
5. VISUALIZATION
   User Dashboard → API Call → Data → Charts/Tables
```

## 🔐 Security Architecture

```
┌─────────────────────────────────────────┐
│         Authentication (JWT)            │
│  • User login → Generate token          │
│  • Token validation on each request      │
│  • 30-minute expiration                 │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│    Authorization (RBAC + Multi-tenant)  │
│  • Admin role → Full access             │
│  • Viewer role → Read-only access       │
│  • Tenant isolation via user.tenant_id  │
│  • Row-level security in DB             │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│      Data Isolation (Multi-tenant)      │
│  • Each log filtered by tenant_id       │
│  • Users see only their tenant's logs   │
│  • Separate alert rules per tenant      │
└─────────────────────────────────────────┘
```

## 📦 Deployment Models

### Appliance Mode (All-in-one Docker Compose)
- Single machine/VM
- All services in Docker containers
- Volume persistence for PostgreSQL
- Network: Internal Docker network
- Best for: Testing, POC, single office

### SaaS Mode (Cloud Deployment)
- Backend on VM/Container (AWS EC2, DigitalOcean, etc.)
- PostgreSQL on managed database (RDS, etc.) or separate VM
- Frontend on CDN + backend API
- HTTPS with self-signed or Let's Encrypt certificates
- Best for: Multi-customer, high availability

## 🎯 Scaling Considerations

- **Horizontal Scaling**: Multiple backend instances behind load balancer
- **Database**: Connection pooling, read replicas
- **Ingestion**: Kafka/RabbitMQ for high volume (future)
- **Storage**: TimescaleDB compression for old logs
- **Caching**: Redis for frequently accessed data (future)

## 📋 Component Technology Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| API Framework | FastAPI | Async, fast, built-in validation |
| Database | PostgreSQL + TimescaleDB | Time-series optimized, reliable |
| Frontend | React + TypeScript | Modern, type-safe, rich UI |
| Logging Ingest | Python + Socket | Simple, no external dependencies |
| Containerization | Docker | Consistent, portable, reproducible |
| Orchestration | Docker Compose | Simple, suitable for demo/MVP |

## 🔄 Log Processing Pipeline

```
1. RECEIVE
   └─ UDP 514 (Syslog) / POST /ingest / File upload
   
2. PARSE
   └─ Detect format (CEF, JSON, Syslog, etc.)
   └─ Extract fields using regex/JSON parser
   
3. NORMALIZE
   └─ Map to unified schema
   └─ Validate required fields
   └─ Add @timestamp if missing
   
4. ENRICH (optional)
   └─ Add GeoIP info
   └─ Add Reverse DNS lookup
   └─ Tag classification
   
5. VALIDATE
   └─ Check multi-tenant isolation
   └─ Verify user permissions
   └─ Rate limiting
   
6. STORE
   └─ Insert into PostgreSQL
   └─ Create indexes
   └─ Trigger retention policy
   
7. ALERT
   └─ Check against alert rules
   └─ Send notification (webhook/email)
   
8. VISUALIZE
   └─ Return to dashboard in real-time
```

---

**Next**: See `setup_appliance.md` for deployment instructions.
