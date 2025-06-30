# 🚀 CodeGates API Deployment Guide

This guide covers deploying the CodeGates API server for enterprise use, enabling centralized code analysis and team collaboration.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Architecture Overview](#architecture-overview)
- [Deployment Options](#deployment-options)
- [Configuration](#configuration)
- [VS Code Extension Setup](#vs-code-extension-setup)
- [API Documentation](#api-documentation)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Troubleshooting](#troubleshooting)

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd codegates

# Set environment variables
export SECRET_KEY="your-super-secret-key-here"
export OPENAI_API_KEY="your-openai-api-key"  # Optional for LLM features

# Start the stack
docker-compose up -d

# Check status
docker-compose ps
```

### Option 2: Local Development

```bash
# Install dependencies
pip install -r requirements.txt
pip install flask flask-cors flask-limiter redis celery

# Set environment variables
export FLASK_ENV=development
export SECRET_KEY="dev-secret-key"

# Start Redis (required)
redis-server

# Start the API server
python api_server.py

# In another terminal, start Celery worker
celery -A codegates.api.tasks worker --loglevel=info
```

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   VS Code       │    │   Web Client    │    │   CI/CD         │
│   Extension     │    │   Dashboard     │    │   Pipeline      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │      Load Balancer       │
                    │       (Nginx)            │
                    └─────────────┬─────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
    ┌─────▼─────┐           ┌─────▼─────┐           ┌─────▼─────┐
    │ API Server│           │ API Server│           │ API Server│
    │ Instance 1│           │ Instance 2│           │ Instance 3│
    └─────┬─────┘           └─────┬─────┘           └─────┬─────┘
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
    ┌─────▼─────┐           ┌─────▼─────┐           ┌─────▼─────┐
    │  Celery   │           │   Redis   │           │PostgreSQL │
    │  Workers  │           │  Cache    │           │ Database  │
    └───────────┘           └───────────┘           └───────────┘
```

### Components

- **API Server**: Flask-based REST API with authentication and rate limiting
- **Celery Workers**: Background task processing for long-running scans
- **Redis**: Caching, rate limiting, and task queue
- **PostgreSQL**: Persistent storage for scan results and user data
- **Nginx**: Reverse proxy and load balancer (production)

## 🌐 Deployment Options

### 1. Local Development

Perfect for testing and development:

```bash
python api_server.py
```

**Pros**: Quick setup, easy debugging
**Cons**: Single instance, no persistence

### 2. Docker Compose

Ideal for small teams and staging environments:

```bash
docker-compose up -d
```

**Pros**: Full stack, easy management, persistent data
**Cons**: Single machine deployment

### 3. Kubernetes

Enterprise-grade deployment with auto-scaling:

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: codegates-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: codegates-api
  template:
    metadata:
      labels:
        app: codegates-api
    spec:
      containers:
      - name: api
        image: codegates/api:latest
        ports:
        - containerPort: 5000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: codegates-secrets
              key: database-url
```

**Pros**: Auto-scaling, high availability, cloud-native
**Cons**: Complex setup, requires Kubernetes knowledge

### 4. Cloud Deployment

#### AWS ECS/Fargate

```bash
# Build and push image
docker build -t codegates-api .
docker tag codegates-api:latest <account>.dkr.ecr.<region>.amazonaws.com/codegates-api:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/codegates-api:latest

# Deploy using ECS CLI or CloudFormation
```

#### Google Cloud Run

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT-ID/codegates-api
gcloud run deploy --image gcr.io/PROJECT-ID/codegates-api --platform managed
```

#### Azure Container Instances

```bash
# Create resource group and deploy
az group create --name codegates-rg --location eastus
az container create --resource-group codegates-rg --name codegates-api \
  --image codegates/api:latest --dns-name-label codegates-api --ports 5000
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `FLASK_ENV` | Environment (development/production/testing) | development | No |
| `SECRET_KEY` | Flask secret key | - | Yes (production) |
| `DATABASE_URL` | Database connection string | sqlite:///codegates.db | No |
| `REDIS_URL` | Redis connection string | redis://localhost:6379/0 | No |
| `CELERY_BROKER_URL` | Celery broker URL | redis://localhost:6379/1 | No |
| `OPENAI_API_KEY` | OpenAI API key for LLM features | - | No |
| `ANTHROPIC_API_KEY` | Anthropic API key | - | No |
| `GEMINI_API_KEY` | Google Gemini API key | - | No |
| `GITHUB_TOKEN` | GitHub token for private repos | - | No |
| `LOG_LEVEL` | Logging level | INFO | No |
| `CORS_ORIGINS` | Allowed CORS origins | http://localhost:3000 | No |

### Production Configuration

```bash
# .env file for production
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-change-this
DATABASE_URL=postgresql://user:pass@localhost:5432/codegates
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# LLM API Keys (optional)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...

# Security
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
WEBHOOK_SECRET=your-webhook-secret

# Monitoring
LOG_LEVEL=WARNING
LOG_FILE=/var/log/codegates/api.log
```

## 🔌 VS Code Extension Setup

### Configure API Mode

1. Open VS Code Settings (`Cmd/Ctrl + ,`)
2. Search for "CodeGates"
3. Enable API mode:

```json
{
  "codegates.api.enabled": true,
  "codegates.api.baseUrl": "https://your-api-server.com/api/v1",
  "codegates.api.apiKey": "your-api-key",
  "codegates.api.timeout": 300
}
```

### Generate API Key

```bash
# Using the API
curl -X POST https://your-api-server.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "your-username", "password": "your-password"}'

# Response includes JWT token
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "expires_in": 86400
}
```

## 📚 API Documentation

### Base URL

```
https://your-api-server.com/api/v1
```

### Authentication

```bash
# Include JWT token in requests
curl -H "Authorization: Bearer <token>" \
  https://your-api-server.com/api/v1/scan/workspace
```

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/auth/login` | POST | User authentication |
| `/scan/workspace` | POST | Scan workspace/directory |
| `/scan/file` | POST | Scan single file |
| `/scan/repository` | POST | Scan Git repository |
| `/scan/{id}/status` | GET | Get scan status |
| `/scan/{id}/result` | GET | Get scan result |
| `/projects` | GET | List projects |
| `/reports/{id}` | GET | Get report |

### Example API Usage

```javascript
// Scan workspace
const response = await fetch('/api/v1/scan/workspace', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    path: '/path/to/workspace',
    async: true,
    llm_enabled: true,
    llm_provider: 'openai',
    threshold: 80
  })
});

const result = await response.json();
console.log('Scan ID:', result.scan_id);

// Poll for results
const pollResult = async (scanId) => {
  const response = await fetch(`/api/v1/scan/${scanId}/status`);
  const status = await response.json();
  
  if (status.status === 'completed') {
    const result = await fetch(`/api/v1/scan/${scanId}/result`);
    return await result.json();
  }
  
  // Continue polling
  setTimeout(() => pollResult(scanId), 5000);
};
```

## 📊 Monitoring & Maintenance

### Health Checks

```bash
# Basic health check
curl https://your-api-server.com/health

# Detailed health check
curl https://your-api-server.com/health/detailed
```

### Metrics & Logging

```bash
# View logs
docker-compose logs -f codegates-api

# Monitor Celery tasks
celery -A codegates.api.tasks inspect active

# Redis monitoring
redis-cli monitor
```

### Database Maintenance

```sql
-- Clean up old scan results (older than 30 days)
DELETE FROM scan_results 
WHERE created_at < NOW() - INTERVAL '30 days';

-- Vacuum database
VACUUM ANALYZE;
```

### Backup & Recovery

```bash
# Database backup
pg_dump codegates > backup_$(date +%Y%m%d).sql

# Redis backup
redis-cli --rdb dump.rdb

# Restore database
psql codegates < backup_20240101.sql
```

## 🔧 Troubleshooting

### Common Issues

#### 1. API Server Won't Start

```bash
# Check logs
docker-compose logs codegates-api

# Common causes:
# - Missing SECRET_KEY in production
# - Database connection issues
# - Port already in use
```

#### 2. Celery Workers Not Processing Tasks

```bash
# Check worker status
celery -A codegates.api.tasks inspect active

# Restart workers
docker-compose restart codegates-worker
```

#### 3. High Memory Usage

```bash
# Monitor memory usage
docker stats

# Optimize:
# - Reduce Celery concurrency
# - Enable Redis memory policies
# - Clean up old scan results
```

#### 4. VS Code Extension Connection Issues

1. Verify API server is running: `curl https://your-api-server.com/health`
2. Check API key is valid
3. Verify CORS settings allow VS Code origin
4. Check firewall/network settings

### Performance Tuning

#### Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX idx_scan_results_created_at ON scan_results(created_at);
CREATE INDEX idx_scan_jobs_status ON scan_jobs(status);
CREATE INDEX idx_scan_jobs_user_id ON scan_jobs(user_id);
```

#### Redis Configuration

```bash
# redis.conf optimizations
maxmemory 2gb
maxmemory-policy allkeys-lru
tcp-keepalive 60
```

#### Nginx Configuration

```nginx
# nginx.conf for production
upstream codegates_api {
    server codegates-api-1:5000;
    server codegates-api-2:5000;
    server codegates-api-3:5000;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location /api/ {
        proxy_pass http://codegates_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-running scans
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

## 🚀 Scaling Considerations

### Horizontal Scaling

- **API Servers**: Add more instances behind load balancer
- **Celery Workers**: Scale workers based on queue length
- **Database**: Use read replicas for read-heavy workloads
- **Redis**: Use Redis Cluster for high availability

### Vertical Scaling

- **CPU**: More cores for parallel processing
- **Memory**: Larger instances for LLM operations
- **Storage**: Fast SSDs for database and temporary files

### Auto-scaling Examples

#### Kubernetes HPA

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: codegates-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: codegates-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

#### AWS ECS Auto Scaling

```json
{
  "serviceName": "codegates-api",
  "scalableDimension": "ecs:service:DesiredCount",
  "targetTrackingScalingPolicies": [
    {
      "targetValue": 70.0,
      "predefinedMetricSpecification": {
        "predefinedMetricType": "ECSServiceAverageCPUUtilization"
      }
    }
  ]
}
```

---

## 📞 Support

- **Documentation**: [https://docs.codegates.com](https://docs.codegates.com)
- **Issues**: [GitHub Issues](https://github.com/yourusername/codegates/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/codegates/discussions)
- **Email**: support@codegates.com

---

**Happy Deploying! 🚀** 