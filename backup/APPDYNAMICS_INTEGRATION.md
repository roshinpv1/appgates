# AppDynamics Integration for CodeGates

## Overview

CodeGates now includes comprehensive AppDynamics integration that allows you to query and validate data in both generic and enterprise AppDynamics instances. The integration supports SSL certificate handling, multiple authentication methods, and provides advanced validation capabilities for application performance, health rules, and error analysis.

## Features

- **Multi-AppDynamics Support**: Works with AppDynamics Cloud and Enterprise instances
- **SSL Certificate Handling**: Configurable SSL verification with support for self-signed certificates
- **Multiple Authentication Methods**: OAuth2 for Cloud, username/password for enterprise
- **Advanced Query Capabilities**: Execute custom metric queries with time ranges
- **Comprehensive Validation**: App performance validation, health rules analysis, and error tracking
- **Performance Analysis**: Automatic analysis of response times, throughput, and error rates
- **Health Rule Monitoring**: Track and validate application health rules

## Configuration

### Environment Variables

Set the following environment variables to configure AppDynamics integration:

```bash
# AppDynamics Connection
APPDYNAMICS_URL=https://your-appdynamics-instance.com:8090
APPDYNAMICS_USERNAME=your-username
APPDYNAMICS_PASSWORD=your-password

# Alternative: OAuth2 authentication for AppDynamics Cloud
APPDYNAMICS_CLIENT_ID=your-client-id
APPDYNAMICS_CLIENT_SECRET=your-client-secret
APPDYNAMICS_ACCOUNT_NAME=your-account-name

# SSL Configuration
CODEGATES_SSL_VERIFY=false  # Set to true for production with valid certificates

# Timeouts and Limits
CODEGATES_APPDYNAMICS_REQUEST_TIMEOUT=300
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

### 1. Test AppDynamics Connection

```http
GET /api/v1/appdynamics/test
```

**Response:**
```json
{
  "status": "success",
  "message": "Connected to AppDynamics successfully",
  "appd_version": "22.1.0",
  "server_info": {
    "version": "22.1.0",
    "serverName": "appdynamics-server"
  }
}
```

### 2. Get Applications List

```http
GET /api/v1/appdynamics/applications
```

**Response:**
```json
{
  "status": "success",
  "applications": [
    {
      "id": 123,
      "name": "MyApplication",
      "description": "Production application"
    }
  ],
  "total_applications": 1
}
```

### 3. Get Specific Application

```http
GET /api/v1/appdynamics/application/{app_name}
```

**Response:**
```json
{
  "status": "success",
  "application": {
    "id": 123,
    "name": "MyApplication",
    "description": "Production application",
    "description": "Production web application"
  }
}
```

### 4. Validate Application in AppDynamics

```http
POST /api/v1/appdynamics/validate-app
Content-Type: application/json

{
  "app_name": "MyApplication",
  "time_range": "60"
}
```

**Response:**
```json
{
  "status": "success",
  "app_name": "MyApplication",
  "time_range": "60",
  "overall_status": "excellent",
  "app_details": {
    "id": 123,
    "name": "MyApplication",
    "description": "Production application"
  },
  "health_rules": {
    "status": "success",
    "health_rules": [...],
    "total_health_rules": 5
  },
  "errors": {
    "status": "success",
    "errors": [...],
    "total_errors": 0
  },
  "performance": {
    "status": "success",
    "performance": {
      "response_time": [...],
      "throughput": [...],
      "error_rate": [...]
    }
  },
  "performance_analysis": {
    "overall_status": "excellent",
    "response_time_status": "excellent",
    "throughput_status": "excellent",
    "error_rate_status": "excellent"
  },
  "summary": {
    "health_rules_count": 5,
    "error_count": 0,
    "has_health_rules": true,
    "has_errors": false
  }
}
```

### 5. Get Application Metrics

```http
GET /api/v1/appdynamics/app/{app_id}/metrics?metric_path=Business Transaction Performance|Business Transactions|*|*|Calls per Minute
```

### 6. Get Health Rules

```http
GET /api/v1/appdynamics/app/{app_id}/health-rules
```

### 7. Get Errors

```http
GET /api/v1/appdynamics/app/{app_id}/errors?time_range=60
```

### 8. Get Performance Data

```http
GET /api/v1/appdynamics/app/{app_id}/performance?time_range=60
```

## Usage Examples

### 1. Basic Application Validation

```python
import requests

# Validate application data
response = requests.post("http://localhost:8000/api/v1/appdynamics/validate-app", json={
    "app_name": "MyApplication",
    "time_range": "60"
})

result = response.json()
print(f"App Status: {result['overall_status']}")
print(f"Health Rules: {result['summary']['health_rules_count']}")
print(f"Errors: {result['summary']['error_count']}")
```

### 2. Get Application List

```python
# Get all applications
response = requests.get("http://localhost:8000/api/v1/appdynamics/applications")
result = response.json()

for app in result['applications']:
    print(f"App: {app['name']} (ID: {app['id']})")
```

### 3. Get Specific Application

```python
# Get specific application
response = requests.get("http://localhost:8000/api/v1/appdynamics/application/MyApplication")
result = response.json()

if result['status'] == 'success':
    app = result['application']
    print(f"Found app: {app['name']} with ID: {app['id']}")
```

### 4. Get Performance Metrics

```python
# Get performance data for an application
response = requests.get("http://localhost:8000/api/v1/appdynamics/app/123/performance?time_range=60")
result = response.json()

if result['status'] == 'success':
    performance = result['performance']
    print(f"Performance metrics available: {list(performance.keys())}")
```

## Validation Capabilities

### 1. Application Discovery
- Lists all applications in AppDynamics
- Retrieves specific application details
- Validates application existence and configuration

### 2. Health Rules Validation
- Retrieves all health rules for an application
- Analyzes health rule configuration
- Provides health rule count and status

### 3. Error Analysis
- Retrieves error information for applications
- Analyzes error patterns and frequency
- Provides error count and categorization

### 4. Performance Validation
- Retrieves response time metrics
- Analyzes throughput data
- Monitors error rates
- Provides performance categorization (excellent/good/fair/poor)

### 5. Overall Status Assessment
The system provides an overall status based on:
- **Excellent**: Excellent performance, has health rules, no errors
- **Good**: Good performance, has health rules
- **Fair**: Fair performance, some issues
- **Poor**: Poor performance or excessive errors

## Metric Examples

### Response Time Metrics
```
Business Transaction Performance|Business Transactions|*|*|Average Response Time (ms)
```

### Throughput Metrics
```
Business Transaction Performance|Business Transactions|*|*|Calls per Minute
```

### Error Rate Metrics
```
Business Transaction Performance|Business Transactions|*|*|Errors per Minute
```

### Resource Metrics
```
Hardware Resources|*|*|*|CPU Used %
Hardware Resources|*|*|*|Memory Used %
```

## Error Handling

The integration includes comprehensive error handling:

- **Connection Errors**: SSL, timeout, and network issues
- **Authentication Errors**: Invalid credentials or expired tokens
- **Application Errors**: Missing applications or invalid app IDs
- **Metric Errors**: Invalid metric paths or time ranges

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
  "message": "Application 'MyApp' not found"
}
```

## Security Considerations

### SSL Certificate Handling
- **Development**: SSL verification disabled by default
- **Production**: Enable SSL verification with proper certificates
- **Custom Certificates**: Support for custom CA bundles

### Authentication
- **OAuth2**: Recommended for AppDynamics Cloud
- **Username/Password**: For enterprise AppDynamics instances
- **Token Management**: Automatic token refresh and expiry handling

### Network Security
- **Timeouts**: Configurable request timeouts
- **Connection Pooling**: Efficient connection reuse
- **Token Security**: Secure token storage and handling

## Troubleshooting

### Common Issues

1. **SSL Certificate Errors**
   ```
   Solution: Set CODEGATES_SSL_VERIFY=false for testing
   ```

2. **Authentication Failures**
   ```
   Solution: Verify APPDYNAMICS_USERNAME/APPDYNAMICS_PASSWORD or APPDYNAMICS_CLIENT_ID/APPDYNAMICS_CLIENT_SECRET
   ```

3. **Connection Timeouts**
   ```
   Solution: Increase CODEGATES_APPDYNAMICS_REQUEST_TIMEOUT
   ```

4. **Application Not Found**
   ```
   Solution: Verify application name and ensure it exists in AppDynamics
   ```

### Debug Mode

Enable debug logging:

```bash
export CODEGATES_LOG_LEVEL=debug
```

### Health Check

Monitor AppDynamics integration health:

```bash
curl -X GET "http://localhost:8000/api/v1/health"
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: CodeGates AppDynamics Validation
on: [push, pull_request]

jobs:
  appdynamics-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Validate App in AppDynamics
        run: |
          # Extract app name from repository name
          APP_NAME=$(echo ${{ github.repository }} | sed 's/.*app-//')
          
          # Validate app in AppDynamics
          curl -X POST "http://localhost:8000/api/v1/appdynamics/validate-app" \
            -H "Content-Type: application/json" \
            -d '{"app_name": "'$APP_NAME'", "time_range": "60"}'
```

## Performance Considerations

- **Metric Queries**: Use efficient metric paths
- **Time Ranges**: Use appropriate time ranges for queries
- **Connection Reuse**: Automatic connection pooling
- **Token Caching**: Automatic token refresh and caching

## Monitoring

### Metrics to Monitor
- AppDynamics API response times
- Authentication success rates
- Application discovery performance
- Metric retrieval times

### Logging

The integration provides detailed logging:

```python
import logging
logging.getLogger('gates.utils.appdynamics_integration').setLevel(logging.DEBUG)
```

## Future Enhancements

- **Real-time Monitoring**: WebSocket-based real-time data streaming
- **Advanced Analytics**: Machine learning-based performance prediction
- **Custom Dashboards**: Integration with AppDynamics dashboards
- **Alert Integration**: AppDynamics alert integration
- **Data Export**: Export capabilities for analysis

## Best Practices

### 1. Metric Optimization
- Use specific metric paths when possible
- Limit time ranges for better performance
- Use appropriate rollup settings
- Avoid wildcard searches when possible

### 2. Authentication
- Use OAuth2 for AppDynamics Cloud
- Use username/password for enterprise
- Rotate credentials regularly
- Use least privilege access

### 3. Error Handling
- Implement retry logic for transient failures
- Log all errors for debugging
- Provide meaningful error messages
- Handle timeouts gracefully

### 4. Performance
- Cache frequently used application data
- Implement result pagination
- Monitor query performance
- Use appropriate time ranges

## Configuration Examples

### Development Environment
```bash
export APPDYNAMICS_URL=https://dev-appdynamics.company.com:8090
export APPDYNAMICS_USERNAME=dev-user
export APPDYNAMICS_PASSWORD=dev-password
export CODEGATES_SSL_VERIFY=false
export CODEGATES_APPDYNAMICS_REQUEST_TIMEOUT=300
```

### Production Environment
```bash
export APPDYNAMICS_URL=https://prod-appdynamics.company.com:8090
export APPDYNAMICS_CLIENT_ID=your-client-id
export APPDYNAMICS_CLIENT_SECRET=your-client-secret
export APPDYNAMICS_ACCOUNT_NAME=your-account
export CODEGATES_SSL_VERIFY=true
export CODEGATES_SSL_CA_BUNDLE=/path/to/ca-bundle.crt
export CODEGATES_APPDYNAMICS_REQUEST_TIMEOUT=600
```

## Testing

### Test Script
Run the provided test script:

```bash
python test_appdynamics_integration.py
```

### Manual Testing
```bash
# Test connection
curl -X GET "http://localhost:8000/api/v1/appdynamics/test"

# Get applications
curl -X GET "http://localhost:8000/api/v1/appdynamics/applications"

# Validate app
curl -X POST "http://localhost:8000/api/v1/appdynamics/validate-app" \
  -H "Content-Type: application/json" \
  -d '{"app_name": "MyApplication", "time_range": "60"}'
```

## Authentication Methods

### AppDynamics Cloud (OAuth2)
```bash
export APPDYNAMICS_CLIENT_ID=your-client-id
export APPDYNAMICS_CLIENT_SECRET=your-client-secret
export APPDYNAMICS_ACCOUNT_NAME=your-account-name
```

### AppDynamics Enterprise (Basic Auth)
```bash
export APPDYNAMICS_USERNAME=your-username
export APPDYNAMICS_PASSWORD=your-password
```

## Performance Analysis

The integration provides automatic performance analysis:

### Response Time Analysis
- **Excellent**: < 100ms average response time
- **Good**: 100-500ms average response time
- **Fair**: 500-1000ms average response time
- **Poor**: > 1000ms average response time

### Throughput Analysis
- **Excellent**: > 100 calls per minute
- **Good**: 50-100 calls per minute
- **Fair**: 10-50 calls per minute
- **Poor**: < 10 calls per minute

### Error Rate Analysis
- **Excellent**: 0 errors per minute
- **Good**: < 1 error per minute
- **Fair**: 1-5 errors per minute
- **Poor**: > 5 errors per minute 