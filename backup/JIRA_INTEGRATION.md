# JIRA Integration for CodeGates

## Overview

CodeGates now includes comprehensive JIRA integration that allows you to automatically post scan reports to JIRA issues. The integration supports both JIRA Enterprise and Standard instances, with SSL certificate handling and secure authentication.

## Features

- **Multi-JIRA Support**: Works with JIRA Cloud, Server, and Data Center instances
- **SSL Certificate Handling**: Configurable SSL verification with support for self-signed certificates
- **Multiple Authentication Methods**: Basic auth, API tokens, and Personal Access Tokens (PAT)
- **Automatic Report Posting**: Posts scan reports to JIRA stories identified by APPID
- **File Attachments**: Attaches HTML reports to JIRA issues
- **Rich Comments**: Creates formatted comments with scan summaries and status indicators

## Configuration

### Environment Variables

Set the following environment variables to configure JIRA integration:

```bash
# JIRA Connection
JIRA_URL=https://your-jira-instance.com
JIRA_USERNAME=your-username
JIRA_API_TOKEN=your-api-token

# Alternative: Personal Access Token
JIRA_PAT_TOKEN=your-pat-token

# SSL Configuration
CODEGATES_SSL_VERIFY=false  # Set to true for production with valid certificates

# Timeouts
CODEGATES_JIRA_REQUEST_TIMEOUT=300
CODEGATES_JIRA_HEALTH_TIMEOUT=100

# Database Integration (for fetching JIRA stories)
# These are configured in your database integration setup
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

### 1. Test JIRA Connection

```http
GET /api/v1/jira/test
```

**Response:**
```json
{
  "status": "success",
  "message": "Connected to JIRA as John Doe",
  "jira_version": "9.4.0",
  "server_info": {
    "displayName": "John Doe",
    "emailAddress": "john.doe@company.com"
  }
}
```

### 2. Get JIRA Stories for App ID

```http
GET /api/v1/jira/stories/{app_id}
```

**Response:**
```json
{
  "app_id": "APP123",
  "stories": ["STORY-123", "STORY-456"],
  "count": 2
}
```

### 3. Post Report to JIRA

```http
POST /api/v1/jira/post-report
Content-Type: application/json

{
  "scan_id": "scan-uuid-here",
  "app_id": "APP123"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Posted report to 2 JIRA stories for app_id: APP123",
  "stories_processed": 2,
  "results": [
    {
      "story_key": "STORY-123",
      "comment_added": true,
      "attachment_added": true,
      "issue_summary": "Implement CodeGates validation"
    }
  ]
}
```

### 4. Get JIRA Issue Details

```http
GET /api/v1/jira/issue/{issue_key}
```

### 5. Add Comment to JIRA Issue

```http
POST /api/v1/jira/issue/{issue_key}/comment
Content-Type: application/json

{
  "body": "This is a test comment"
}
```

### 6. Attach File to JIRA Issue

```http
POST /api/v1/jira/issue/{issue_key}/attach
Content-Type: application/json

{
  "file_path": "/path/to/file.html",
  "filename": "codegates_report.html"
}
```

## Usage Examples

### 1. Complete Workflow

```python
import requests

# 1. Start a scan
scan_response = requests.post("http://localhost:8000/api/v1/scan", json={
    "repository_url": "https://github.com/company/app-ABC",
    "branch": "main"
})

scan_id = scan_response.json()["scan_id"]

# 2. Wait for scan completion (poll status)
while True:
    status_response = requests.get(f"http://localhost:8000/api/v1/scan/{scan_id}")
    if status_response.json()["status"] == "completed":
        break
    time.sleep(5)

# 3. Post report to JIRA
jira_response = requests.post("http://localhost:8000/api/v1/jira/post-report", json={
    "scan_id": scan_id,
    "app_id": "ABC"  # Extracted from repository URL
})

print(f"Posted to {jira_response.json()['stories_processed']} JIRA stories")
```

### 2. Test JIRA Connection

```bash
curl -X GET "http://localhost:8000/api/v1/jira/test"
```

### 3. Get Stories for App ID

```bash
curl -X GET "http://localhost:8000/api/v1/jira/stories/APP123"
```

## Database Integration

The JIRA integration relies on database functions to fetch JIRA stories associated with app IDs:

### Required Database Functions

1. **`fetch_jira_stories(app_id: str)`**: Fetches JIRA story keys from the database
2. **`extract_app_id_from_url(url: str)`**: Extracts app ID from repository URL

### Database Schema

The integration expects the following database view:

```sql
-- JIRA_GATES_SUMMARY_VM view
SELECT STORY, app_id, business_appliation_wf_guid 
FROM EFTVISTA.VW_DC_ENTRY.JIRA_GATES_SUMMARY_VM
WHERE app_id = ? OR business_appliation_wf_guid = ?
```

## Error Handling

The integration includes comprehensive error handling:

- **Connection Errors**: SSL, timeout, and network issues
- **Authentication Errors**: Invalid credentials or expired tokens
- **Permission Errors**: Insufficient permissions to access issues
- **File Errors**: Missing reports or attachment failures

### Common Error Responses

```json
{
  "status": "error",
  "message": "Authentication failed - check credentials"
}
```

```json
{
  "status": "warning",
  "message": "No JIRA stories found for app_id: APP123",
  "stories_processed": 0
}
```

## Security Considerations

### SSL Certificate Handling

- **Development**: SSL verification disabled by default
- **Production**: Enable SSL verification with proper certificates
- **Custom Certificates**: Support for custom CA bundles

### Authentication

- **API Tokens**: Recommended for production use
- **Personal Access Tokens**: Alternative authentication method
- **Basic Auth**: Legacy support (less secure)

### Network Security

- **Timeouts**: Configurable request timeouts
- **Retry Logic**: Automatic retry for transient failures
- **Connection Pooling**: Efficient connection reuse

## Troubleshooting

### Common Issues

1. **SSL Certificate Errors**
   ```
   Solution: Set CODEGATES_SSL_VERIFY=false for testing
   ```

2. **Authentication Failures**
   ```
   Solution: Verify JIRA_USERNAME and JIRA_API_TOKEN
   ```

3. **No Stories Found**
   ```
   Solution: Check database integration and app_id mapping
   ```

4. **File Attachment Failures**
   ```
   Solution: Verify file permissions and JIRA attachment settings
   ```

### Debug Mode

Enable debug logging:

```bash
export CODEGATES_LOG_LEVEL=debug
```

### Health Check

Monitor JIRA integration health:

```bash
curl -X GET "http://localhost:8000/api/v1/health"
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: CodeGates JIRA Integration
on: [push, pull_request]

jobs:
  codegates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Start CodeGates Scan
        run: |
          curl -X POST "http://localhost:8000/api/v1/scan" \
            -H "Content-Type: application/json" \
            -d '{"repository_url": "${{ github.repositoryUrl }}", "branch": "${{ github.ref_name }}"}'
      
      - name: Post to JIRA
        run: |
          # Extract app_id from repository name
          APP_ID=$(echo ${{ github.repository }} | sed 's/.*app-//')
          
          # Post report to JIRA
          curl -X POST "http://localhost:8000/api/v1/jira/post-report" \
            -H "Content-Type: application/json" \
            -d '{"scan_id": "${{ steps.scan.outputs.scan_id }}", "app_id": "'$APP_ID'"}'
```

## Performance Considerations

- **Connection Pooling**: Reuses HTTP connections
- **Timeout Configuration**: Prevents hanging requests
- **Batch Processing**: Efficient handling of multiple stories
- **File Size Limits**: Configurable attachment size limits

## Monitoring

### Metrics to Monitor

- JIRA API response times
- Authentication success rates
- File attachment success rates
- Story lookup performance

### Logging

The integration provides detailed logging:

```python
import logging
logging.getLogger('gates.utils.jira_integration').setLevel(logging.DEBUG)
```

## Future Enhancements

- **Webhook Support**: Real-time notifications
- **Advanced Filtering**: JQL-based story selection
- **Bulk Operations**: Batch processing for multiple apps
- **Custom Fields**: Support for custom JIRA fields
- **Workflow Integration**: Automatic issue transitions 