# Splunk Integration for CodeGates

## Overview

CodeGates now includes comprehensive Splunk integration that allows you to query and validate data in both generic and enterprise Splunk instances. The integration supports SSL certificate handling, multiple authentication methods, and provides advanced validation capabilities for application logs, errors, and performance metrics.

## Features

- **Multi-Splunk Support**: Works with Splunk Cloud, Enterprise, and Data Center instances
- **SSL Certificate Handling**: Configurable SSL verification with support for self-signed certificates
- **Multiple Authentication Methods**: Token-based auth, username/password for enterprise
- **Advanced Query Capabilities**: Execute custom SPL queries with time ranges
- **Job Management**: Long-running search jobs with status tracking
- **Comprehensive Validation**: App log validation, error analysis, and performance metrics
- **Pattern Analysis**: Automatic analysis of log patterns, error types, and performance ranges

## Configuration

### Environment Variables

Set the following environment variables to configure Splunk integration:

```bash
# Splunk Connection
SPLUNK_URL=https://your-splunk-instance.com:8089
SPLUNK_USERNAME=your-username
SPLUNK_PASSWORD=your-password

# Alternative: Token-based authentication
SPLUNK_TOKEN=your-splunk-token

# SSL Configuration
CODEGATES_SSL_VERIFY=false  # Set to true for production with valid certificates

# Timeouts and Limits
CODEGATES_SPLUNK_REQUEST_TIMEOUT=300
CODEGATES_SPLUNK_MAX_RESULTS=1000
```

### SSL Certificate Handling

For enterprise environments with custom SSL certificates:

```bash
# Disable SSL verification (for development/testing)
CODEGATES_SSL_VERIFY=false

# For production with custom certificates
CODEGATES_SSL_VERIFY=true
CODEGATES_SSL_CA_BUNDLE=/path/to/custom/ca-bundle.crt
```

## API Endpoints

### 1. Test Splunk Connection

```http
GET /api/v1/splunk/test
```

**Response:**
```json
{
  "status": "success",
  "message": "Connected to Splunk successfully",
  "splunk_version": "9.0.0",
  "server_info": {
    "entry": [{
      "content": {
        "version": "9.0.0",
        "serverName": "splunk-server"
      }
    }]
  }
}
```

### 2. Execute Splunk Search

```http
POST /api/v1/splunk/search
Content-Type: application/json

{
  "query": "search index=* app_id=\"APP123\" | head 100",
  "earliest_time": "-24h",
  "latest_time": "now",
  "max_results": 1000
}
```

**Response:**
```json
{
  "status": "success",
  "results": [...],
  "total_results": 150,
  "query": "search index=* app_id=\"APP123\" | head 100",
  "execution_time": 2.5
}
```

### 3. Validate Application in Splunk

```http
POST /api/v1/splunk/validate-app
Content-Type: application/json

{
  "app_id": "APP123",
  "time_range": "-24h"
}
```

**Response:**
```json
{
  "status": "success",
  "app_id": "APP123",
  "time_range": "-24h",
  "overall_status": "excellent",
  "log_validation": {
    "status": "success",
    "log_count": 1250,
    "has_logs": true,
    "log_analysis": {
      "total_logs": 1250,
      "log_levels": {"INFO": 800, "WARN": 300, "ERROR": 150},
      "sources": ["app-server-1", "app-server-2"]
    }
  },
  "error_validation": {
    "status": "success",
    "error_count": 5,
    "has_errors": true,
    "error_analysis": {
      "total_errors": 5,
      "error_types": {"TimeoutException": 3, "ConnectionError": 2},
      "error_messages": ["Connection timeout after 30s", "Database connection failed"]
    }
  },
  "performance_validation": {
    "status": "success",
    "metric_count": 500,
    "has_metrics": true,
    "performance_analysis": {
      "total_metrics": 500,
      "avg_response_time": 150.5,
      "max_response_time": 2000,
      "min_response_time": 50,
      "performance_ranges": {
        "excellent": 300,
        "good": 150,
        "fair": 40,
        "poor": 10
      }
    }
  }
}
```

### 4. Start Splunk Search Job

```http
POST /api/v1/splunk/job
Content-Type: application/json

{
  "query": "search index=* | stats count by source",
  "earliest_time": "-7d",
  "latest_time": "now"
}
```

**Response:**
```json
{
  "status": "success",
  "job_id": "1234567890.1234567890"
}
```

### 5. Get Job Status

```http
GET /api/v1/splunk/job/{job_id}
```

**Response:**
```json
{
  "status": "success",
  "job_id": "1234567890.1234567890",
  "is_done": true,
  "progress": 100,
  "result_count": 150
}
```

### 6. Get Job Results

```http
GET /api/v1/splunk/job/{job_id}/results?offset=0&count=100
```

## Usage Examples

### 1. Basic Search Query

```python
import requests

# Execute a simple search
response = requests.post("http://localhost:8000/api/v1/splunk/search", json={
    "query": "search index=* | head 10",
    "earliest_time": "-1h",
    "latest_time": "now"
})

result = response.json()
print(f"Found {result['total_results']} results")
```

### 2. App Validation Workflow

```python
# Validate application data
response = requests.post("http://localhost:8000/api/v1/splunk/validate-app", json={
    "app_id": "APP123",
    "time_range": "-24h"
})

result = response.json()
print(f"App Status: {result['overall_status']}")
print(f"Log Count: {result['log_validation']['log_count']}")
print(f"Error Count: {result['error_validation']['error_count']}")
```

### 3. Long-Running Job

```python
# Start a long-running job
job_response = requests.post("http://localhost:8000/api/v1/splunk/job", json={
    "query": "search index=* | stats count by source",
    "earliest_time": "-7d",
    "latest_time": "now"
})

job_id = job_response.json()["job_id"]

# Poll for completion
while True:
    status_response = requests.get(f"http://localhost:8000/api/v1/splunk/job/{job_id}")
    status = status_response.json()
    
    if status["is_done"]:
        # Get results
        results_response = requests.get(f"http://localhost:8000/api/v1/splunk/job/{job_id}/results")
        results = results_response.json()
        print(f"Job completed with {results['total_results']} results")
        break
    
    time.sleep(5)
```

## Validation Capabilities

### 1. Log Validation

The integration validates application logs by:
- Searching for logs with the specified app_id
- Analyzing log levels and sources
- Identifying log patterns and trends
- Providing log count and distribution

### 2. Error Validation

Error validation includes:
- Searching for error-level logs
- Analyzing error types and messages
- Identifying most common errors
- Providing error count and patterns

### 3. Performance Validation

Performance validation covers:
- Response time metrics
- Latency analysis
- Performance categorization (excellent/good/fair/poor)
- Statistical analysis of performance data

### 4. Overall Status Assessment

The system provides an overall status based on:
- **Excellent**: Has logs, no errors, has metrics
- **Good**: Has logs, no errors
- **Fair**: Has logs, some errors
- **Poor**: No logs or excessive errors

## Query Examples

### Application Logs
```spl
search index=* app_id="APP123" OR source="*APP123*" | head 1000
```

### Error Logs
```spl
search index=* (app_id="APP123" OR source="*APP123*") (level=ERROR OR level=error OR severity=ERROR OR severity=error OR "ERROR" OR "error") | head 1000
```

### Performance Metrics
```spl
search index=* (app_id="APP123" OR source="*APP123*") (response_time OR latency OR duration OR "response time" OR "response_time") | head 1000
```

### Custom Queries
```spl
search index=* app_id="APP123" | stats count by level | sort -count
```

## Error Handling

The integration includes comprehensive error handling:

- **Connection Errors**: SSL, timeout, and network issues
- **Authentication Errors**: Invalid credentials or expired tokens
- **Query Errors**: Invalid SPL syntax or search parameters
- **Job Errors**: Failed job creation or execution

### Common Error Responses

```json
{
  "status": "error",
  "message": "Authentication failed - check credentials"
}
```

```json
{
  "status": "error",
  "message": "Invalid search query syntax"
}
```

## Security Considerations

### SSL Certificate Handling
- **Development**: SSL verification disabled by default
- **Production**: Enable SSL verification with proper certificates
- **Custom Certificates**: Support for custom CA bundles

### Authentication
- **Token-based**: Recommended for Splunk Cloud
- **Username/Password**: For enterprise Splunk instances
- **Session Management**: Automatic session handling

### Network Security
- **Timeouts**: Configurable request timeouts
- **Connection Pooling**: Efficient connection reuse
- **Query Limits**: Configurable result limits

## Troubleshooting

### Common Issues

1. **SSL Certificate Errors**
   ```
   Solution: Set CODEGATES_SSL_VERIFY=false for testing
   ```

2. **Authentication Failures**
   ```
   Solution: Verify SPLUNK_USERNAME/SPLUNK_PASSWORD or SPLUNK_TOKEN
   ```

3. **Connection Timeouts**
   ```
   Solution: Increase CODEGATES_SPLUNK_REQUEST_TIMEOUT
   ```

4. **Query Syntax Errors**
   ```
   Solution: Validate SPL syntax in Splunk interface first
   ```

### Debug Mode

Enable debug logging:

```bash
export CODEGATES_LOG_LEVEL=debug
```

### Health Check

Monitor Splunk integration health:

```bash
curl -X GET "http://localhost:8000/api/v1/health"
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: CodeGates Splunk Validation
on: [push, pull_request]

jobs:
  splunk-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Validate App in Splunk
        run: |
          # Extract app_id from repository name
          APP_ID=$(echo ${{ github.repository }} | sed 's/.*app-//')
          
          # Validate app in Splunk
          curl -X POST "http://localhost:8000/api/v1/splunk/validate-app" \
            -H "Content-Type: application/json" \
            -d '{"app_id": "'$APP_ID'", "time_range": "-24h"}'
```

## Performance Considerations

- **Query Optimization**: Use efficient SPL queries
- **Result Limits**: Configure appropriate max_results
- **Time Ranges**: Use appropriate time ranges for queries
- **Job Management**: Use jobs for long-running queries

## Monitoring

### Metrics to Monitor
- Splunk API response times
- Authentication success rates
- Query execution times
- Job completion rates

### Logging

The integration provides detailed logging:

```python
import logging
logging.getLogger('gates.utils.splunk_integration').setLevel(logging.DEBUG)
```

## Future Enhancements

- **Real-time Monitoring**: WebSocket-based real-time data streaming
- **Advanced Analytics**: Machine learning-based pattern detection
- **Custom Dashboards**: Integration with Splunk dashboards
- **Alert Integration**: Splunk alert integration
- **Data Export**: Export capabilities for analysis

## Best Practices

### 1. Query Optimization
- Use specific indexes when possible
- Limit result sets with `head` or `limit`
- Use appropriate time ranges
- Avoid wildcard searches when possible

### 2. Authentication
- Use tokens for Splunk Cloud
- Use username/password for enterprise
- Rotate credentials regularly
- Use least privilege access

### 3. Error Handling
- Implement retry logic for transient failures
- Log all errors for debugging
- Provide meaningful error messages
- Handle timeouts gracefully

### 4. Performance
- Use jobs for long-running queries
- Implement result pagination
- Cache frequently used queries
- Monitor query performance

## Configuration Examples

### Development Environment
```bash
export SPLUNK_URL=https://dev-splunk.company.com:8089
export SPLUNK_USERNAME=dev-user
export SPLUNK_PASSWORD=dev-password
export CODEGATES_SSL_VERIFY=false
export CODEGATES_SPLUNK_REQUEST_TIMEOUT=300
```

### Production Environment
```bash
export SPLUNK_URL=https://prod-splunk.company.com:8089
export SPLUNK_TOKEN=your-splunk-token
export CODEGATES_SSL_VERIFY=true
export CODEGATES_SSL_CA_BUNDLE=/path/to/ca-bundle.crt
export CODEGATES_SPLUNK_REQUEST_TIMEOUT=600
```

## Testing

### Test Script
Run the provided test script:

```bash
python test_splunk_integration.py
```

### Manual Testing
```bash
# Test connection
curl -X GET "http://localhost:8000/api/v1/splunk/test"

# Test search
curl -X POST "http://localhost:8000/api/v1/splunk/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "search index=* | head 10"}'

# Test app validation
curl -X POST "http://localhost:8000/api/v1/splunk/validate-app" \
  -H "Content-Type: application/json" \
  -d '{"app_id": "APP123", "time_range": "-24h"}'
``` 