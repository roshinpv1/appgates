# 🔧 Environment Configuration Guide

## Overview

CodeGates now supports comprehensive environment variable configuration for all directory paths, server settings, and operational parameters. This makes the system highly configurable and suitable for various deployment scenarios.

## 🎯 **Environment Variables**

### **Server Configuration**

| Variable | Default | Description |
|----------|---------|-------------|
| `CODEGATES_HOST` | `0.0.0.0` | Server host address |
| `CODEGATES_PORT` | `8000` | Server port number |
| `CODEGATES_LOG_LEVEL` | `info` | Uvicorn log level (debug, info, warning, error) |

### **Directory Configuration**

| Variable | Default | Description |
|----------|---------|-------------|
| `CODEGATES_REPORTS_DIR` | `./reports` | Directory for storing generated reports |
| `CODEGATES_LOGS_DIR` | `./logs` | Directory for storing log files |
| `CODEGATES_TEMP_DIR` | System temp | Directory for temporary files (optional) |

### **CORS Configuration**

| Variable | Default | Description |
|----------|---------|-------------|
| `CODEGATES_CORS_ORIGINS` | `*` | Comma-separated list of allowed CORS origins |

### **LLM Configuration (Optional)**

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | None | OpenAI API key for GPT models |
| `ANTHROPIC_API_KEY` | None | Anthropic API key for Claude models |
| `AZURE_OPENAI_API_KEY` | None | Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | None | Azure OpenAI endpoint URL |

### **Git Configuration (Optional)**

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_TOKEN` | None | GitHub token for private repository access |

### **Advanced Configuration (Future)**

| Variable | Default | Description |
|----------|---------|-------------|
| `CODEGATES_MAX_FILES` | `500` | Maximum files to process per scan |
| `CODEGATES_MAX_FILE_SIZE_MB` | `5` | Maximum file size in MB |
| `CODEGATES_LANGUAGE_THRESHOLD_PERCENT` | `5.0` | Language detection threshold |

## 🚀 **Usage Examples**

### **Development Setup**
```bash
# Basic development configuration
export CODEGATES_HOST=localhost
export CODEGATES_PORT=3000
export CODEGATES_REPORTS_DIR=./dev-reports
export CODEGATES_LOGS_DIR=./dev-logs
export CODEGATES_LOG_LEVEL=debug

# Start the server
cd gates && python3 server.py
```

### **Production Setup**
```bash
# Production configuration
export CODEGATES_HOST=0.0.0.0
export CODEGATES_PORT=8000
export CODEGATES_REPORTS_DIR=/var/lib/codegates/reports
export CODEGATES_LOGS_DIR=/var/log/codegates
export CODEGATES_TEMP_DIR=/tmp/codegates
export CODEGATES_CORS_ORIGINS=https://your-domain.com,https://api.your-domain.com
export CODEGATES_LOG_LEVEL=info

# Start the server
cd gates && python3 server.py
```

### **Docker Setup**
```dockerfile
# Dockerfile example
FROM python:3.11-slim

# Set environment variables
ENV CODEGATES_HOST=0.0.0.0
ENV CODEGATES_PORT=8000
ENV CODEGATES_REPORTS_DIR=/app/reports
ENV CODEGATES_LOGS_DIR=/app/logs
ENV CODEGATES_TEMP_DIR=/tmp/codegates

# Create directories
RUN mkdir -p /app/reports /app/logs /tmp/codegates

# Copy application
COPY . /app
WORKDIR /app

# Install dependencies
RUN pip install -r requirements.txt

# Expose port
EXPOSE 8000

# Start server
CMD ["python3", "gates/server.py"]
```

### **Docker Compose Setup**
```yaml
# docker-compose.yml example
version: '3.8'
services:
  codegates:
    build: .
    ports:
      - "8000:8000"
    environment:
      - CODEGATES_HOST=0.0.0.0
      - CODEGATES_PORT=8000
      - CODEGATES_REPORTS_DIR=/app/reports
      - CODEGATES_LOGS_DIR=/app/logs
      - CODEGATES_TEMP_DIR=/tmp/codegates
      - CODEGATES_CORS_ORIGINS=*
      - CODEGATES_LOG_LEVEL=info
    volumes:
      - ./reports:/app/reports
      - ./logs:/app/logs
      - /tmp/codegates:/tmp/codegates
```

### **Kubernetes Setup**
```yaml
# kubernetes-deployment.yaml example
apiVersion: apps/v1
kind: Deployment
metadata:
  name: codegates
spec:
  replicas: 3
  selector:
    matchLabels:
      app: codegates
  template:
    metadata:
      labels:
        app: codegates
    spec:
      containers:
      - name: codegates
        image: codegates:latest
        ports:
        - containerPort: 8000
        env:
        - name: CODEGATES_HOST
          value: "0.0.0.0"
        - name: CODEGATES_PORT
          value: "8000"
        - name: CODEGATES_REPORTS_DIR
          value: "/app/reports"
        - name: CODEGATES_LOGS_DIR
          value: "/app/logs"
        - name: CODEGATES_TEMP_DIR
          value: "/tmp/codegates"
        - name: CODEGATES_CORS_ORIGINS
          value: "*"
        - name: CODEGATES_LOG_LEVEL
          value: "info"
        volumeMounts:
        - name: reports-volume
          mountPath: /app/reports
        - name: logs-volume
          mountPath: /app/logs
      volumes:
      - name: reports-volume
        persistentVolumeClaim:
          claimName: codegates-reports-pvc
      - name: logs-volume
        persistentVolumeClaim:
          claimName: codegates-logs-pvc
```

## 📁 **Directory Structure**

With environment variables, you can organize directories as needed:

### **Development Structure**
```
project/
├── gates/
├── reports/           # CODEGATES_REPORTS_DIR
├── logs/             # CODEGATES_LOGS_DIR
├── temp/             # CODEGATES_TEMP_DIR
└── env.example
```

### **Production Structure**
```
/var/lib/codegates/
├── reports/          # CODEGATES_REPORTS_DIR
└── data/

/var/log/
└── codegates/        # CODEGATES_LOGS_DIR

/tmp/
└── codegates/        # CODEGATES_TEMP_DIR

/opt/codegates/
└── app/              # Application code
```

## 🔒 **Security Considerations**

### **Directory Permissions**
```bash
# Set appropriate permissions for production
sudo mkdir -p /var/lib/codegates/reports
sudo mkdir -p /var/log/codegates
sudo mkdir -p /tmp/codegates

sudo chown -R codegates:codegates /var/lib/codegates
sudo chown -R codegates:codegates /var/log/codegates
sudo chown -R codegates:codegates /tmp/codegates

sudo chmod 755 /var/lib/codegates/reports
sudo chmod 755 /var/log/codegates
sudo chmod 1777 /tmp/codegates  # Sticky bit for temp directory
```

### **Environment File Security**
```bash
# Secure .env file
chmod 600 .env
chown codegates:codegates .env

# Never commit .env to version control
echo ".env" >> .gitignore
```

### **CORS Configuration**
```bash
# Production CORS - be specific about origins
export CODEGATES_CORS_ORIGINS=https://your-app.com,https://api.your-app.com

# Development CORS - can be permissive
export CODEGATES_CORS_ORIGINS=*
```

## 🎯 **Configuration Validation**

The server validates configuration on startup:

```
🔧 Configuration:
============================================================
📁 Reports Directory: /var/lib/codegates/reports
📁 Logs Directory: /var/log/codegates
📁 Temp Directory: /tmp/codegates
🌐 CORS Origins: https://your-domain.com, https://api.your-domain.com
📊 Log Level: info
============================================================
```

## 🚨 **Troubleshooting**

### **Common Issues**

1. **Permission Denied**
   ```bash
   # Fix: Set correct permissions
   sudo chown -R $USER:$USER /path/to/directory
   sudo chmod -R 755 /path/to/directory
   ```

2. **Directory Not Found**
   ```bash
   # Fix: Create missing directories
   mkdir -p $CODEGATES_REPORTS_DIR
   mkdir -p $CODEGATES_LOGS_DIR
   ```

3. **Port Already in Use**
   ```bash
   # Fix: Change port or kill existing process
   export CODEGATES_PORT=8001
   # or
   sudo lsof -ti:8000 | xargs kill -9
   ```

4. **CORS Issues**
   ```bash
   # Fix: Add your domain to CORS origins
   export CODEGATES_CORS_ORIGINS=https://your-domain.com,*
   ```

### **Debugging**
```bash
# Enable debug logging
export CODEGATES_LOG_LEVEL=debug

# Check environment variables
env | grep CODEGATES

# Test directory access
ls -la $CODEGATES_REPORTS_DIR
ls -la $CODEGATES_LOGS_DIR
```

## 🔮 **Future Enhancements**

### **Planned Environment Variables**
- `CODEGATES_DATABASE_URL` - Database connection string
- `CODEGATES_REDIS_URL` - Redis connection for caching
- `CODEGATES_WEBHOOK_URL` - Webhook notifications
- `CODEGATES_SMTP_*` - Email notification settings
- `CODEGATES_AUTH_*` - Authentication configuration
- `CODEGATES_RATE_LIMIT_*` - Rate limiting settings

### **Configuration File Support**
Future versions will support configuration files:
- `config.yaml` - YAML configuration
- `config.json` - JSON configuration
- `config.toml` - TOML configuration

---

## 🎉 **Benefits**

### **Deployment Flexibility**
- **Development**: Quick local setup with custom directories
- **Staging**: Isolated environments with proper paths
- **Production**: Secure, optimized directory structure
- **Containerization**: Easy Docker and Kubernetes deployment

### **Security**
- **Isolated Directories**: Separate data from application code
- **Proper Permissions**: Secure file system access
- **CORS Control**: Precise origin access control
- **Environment Isolation**: Separate configs per environment

### **Maintenance**
- **Log Management**: Centralized logging with configurable paths
- **Report Organization**: Structured report storage
- **Temp Cleanup**: Configurable temporary file handling
- **Monitoring**: Environment-specific logging levels

This environment variable system makes CodeGates suitable for any deployment scenario, from local development to enterprise production environments. 