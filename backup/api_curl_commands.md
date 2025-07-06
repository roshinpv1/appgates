# CodeGates API - cURL Commands

This document provides cURL command examples for interacting with the CodeGates API.

## Base URL

```
http://localhost:8000
```

## Health Check

### Basic Health Check
```bash
curl -X GET "http://localhost:8000/api/v1/health"
```

### Health Check with Pretty JSON
```bash
curl -s -X GET "http://localhost:8000/api/v1/health" | jq '.'
```

## Repository Scanning

### Basic Scan (Public Repository)
```bash
curl -X POST "http://localhost:8000/api/v1/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.com/username/repository",
    "branch": "main"
  }'
```

### Scan with GitHub Token (Private Repository)
```bash
curl -X POST "http://localhost:8000/api/v1/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.com/username/private-repo",
    "branch": "main",
    "github_token": "your_github_token_here"
  }'
```

### Scan with Custom Threshold
```bash
curl -X POST "http://localhost:8000/api/v1/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.com/username/repository",
    "branch": "main",
    "scan_options": {
      "threshold": 80
    }
  }'
```

### Scan with Timeout Configuration
```bash
curl -X POST "http://localhost:8000/api/v1/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.com/username/repository",
    "branch": "main",
    "scan_options": {
      "git_clone_timeout": 600,
      "api_download_timeout": 300,
      "analysis_timeout": 900,
      "llm_request_timeout": 60
    }
  }'
```

### Scan with SSL Configuration (GitHub Enterprise)
```bash
curl -X POST "http://localhost:8000/api/v1/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.enterprise.com/company/repo",
    "branch": "main",
    "github_token": "your_enterprise_token",
    "scan_options": {
      "verify_ssl": false,
      "prefer_api_checkout": true
    }
  }'
```

### Scan with All Options
```bash
curl -X POST "http://localhost:8000/api/v1/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.com/username/repository",
    "branch": "develop",
    "github_token": "your_token_here",
    "scan_options": {
      "threshold": 75,
      "prefer_api_checkout": false,
      "enable_api_fallback": true,
      "verify_ssl": true,
      "git_clone_timeout": 300,
      "api_download_timeout": 120,
      "analysis_timeout": 600,
      "llm_request_timeout": 45
    }
  }'
```

### Scan with JIRA Integration
```bash
curl -X POST "http://localhost:8000/api/v1/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.com/username/repository",
    "branch": "main",
    "github_token": "your_token",
    "jira_options": {
      "enabled": true,
      "issue_key": "PROJECT-123",
      "comment_format": "markdown",
      "include_details": true,
      "include_recommendations": true
    }
  }'
```

## Scan Status and Results

### Get Scan Status
```bash
# Replace {scan_id} with actual scan ID
curl -X GET "http://localhost:8000/api/v1/scan/{scan_id}/status"
```

### Example with Real Scan ID
```bash
curl -X GET "http://localhost:8000/api/v1/scan/12345678-1234-1234-1234-123456789abc/status"
```

### Get Scan Status with Pretty JSON
```bash
curl -s -X GET "http://localhost:8000/api/v1/scan/{scan_id}/status" | jq '.'
```

## Reports

### Get HTML Report
```bash
# Replace {scan_id} with actual scan ID
curl -X GET "http://localhost:8000/api/v1/reports/{scan_id}" \
  -H "Accept: text/html" \
  -o "report_{scan_id}.html"
```

### Get HTML Report with Comments
```bash
# Comments as JSON string
curl -X GET "http://localhost:8000/api/v1/reports/{scan_id}?comments=%7B%22gate1%22%3A%22This%20needs%20improvement%22%7D" \
  -H "Accept: text/html" \
  -o "report_with_comments_{scan_id}.html"
```

### Update Report Comments
```bash
curl -X POST "http://localhost:8000/api/v1/reports/{scan_id}/comments" \
  -H "Content-Type: application/json" \
  -d '{
    "Logs Searchable/Available": "Need to implement structured logging",
    "Avoid Logging Confidential Data": "Review password logging in auth module",
    "Create Audit Trail Logs": "Add audit logging for admin actions"
  }'
```

### List All Reports
```bash
curl -X GET "http://localhost:8000/api/v1/reports"
```

### List Reports with Pretty JSON
```bash
curl -s -X GET "http://localhost:8000/api/v1/reports" | jq '.'
```

## JIRA Integration

### Check JIRA Status
```bash
curl -X GET "http://localhost:8000/api/v1/jira/status"
```

### Check JIRA Status with Pretty JSON
```bash
curl -s -X GET "http://localhost:8000/api/v1/jira/status" | jq '.'
```

### Post Report to JIRA
```bash
curl -X POST "http://localhost:8000/api/v1/jira/post" \
  -H "Content-Type: application/json" \
  -d '{
    "scan_id": "12345678-1234-1234-1234-123456789abc",
    "issue_key": "PROJECT-123",
    "comment_format": "markdown",
    "include_details": true,
    "include_recommendations": true,
    "attach_html_report": false
  }'
```

### Post Report to JIRA with All Options
```bash
curl -X POST "http://localhost:8000/api/v1/jira/post" \
  -H "Content-Type: application/json" \
  -d '{
    "scan_id": "12345678-1234-1234-1234-123456789abc",
    "issue_key": "PROJECT-123",
    "comment_format": "markdown",
    "include_details": true,
    "include_recommendations": true,
    "attach_html_report": true
  }'
```

## System Administration

### Manual Cleanup
```bash
curl -X GET "http://localhost:8000/api/v1/system/cleanup"
```

### Get Temporary Directory Status
```bash
curl -X GET "http://localhost:8000/api/v1/system/temp-status"
```

### Get Timeout Configuration
```bash
curl -X GET "http://localhost:8000/api/v1/system/timeout-config"
```

### Get Timeout Configuration with Pretty JSON
```bash
curl -s -X GET "http://localhost:8000/api/v1/system/timeout-config" | jq '.'
```

## Response Examples

### Successful Scan Response
```json
{
  "scan_id": "12345678-1234-1234-1234-123456789abc",
  "status": "running",
  "score": 0,
  "gates": [],
  "recommendations": [],
  "report_url": null,
  "jira_result": null
}
```

### Scan Status Response (Completed)
```json
{
  "scan_id": "12345678-1234-1234-1234-123456789abc",
  "status": "completed",
  "score": 85.5,
  "gates": [
    {
      "name": "Logs Searchable/Available",
      "status": "PASS",
      "score": 90.0,
      "details": ["Found structured logging implementation"],
      "expected": 5,
      "found": 4,
      "coverage": 80.0,
      "quality_score": 90.0,
      "matches": []
    }
  ],
  "recommendations": [
    "Implement structured logging in remaining modules",
    "Add correlation IDs to all log entries"
  ],
  "report_url": "http://localhost:8000/api/v1/reports/12345678-1234-1234-1234-123456789abc",
  "jira_result": null
}
```

### Error Response
```json
{
  "detail": "Repository not found or access denied"
}
```

## Tips

1. **Save Scan ID**: Always save the `scan_id` from the scan response to check status and retrieve reports later.

2. **Check Status**: Use the status endpoint to monitor long-running scans.

3. **Pretty JSON**: Add `| jq '.'` to any curl command for formatted JSON output.

4. **Save Reports**: Use `-o filename.html` to save HTML reports to files.

5. **Environment Variables**: Use environment variables for tokens:
   ```bash
   export GITHUB_TOKEN="your_token_here"
   curl -X POST "http://localhost:8000/api/v1/scan" \
     -H "Content-Type: application/json" \
     -d "{\"repository_url\": \"https://github.com/user/repo\", \"github_token\": \"$GITHUB_TOKEN\"}"
   ```

6. **Batch Processing**: Create scripts to scan multiple repositories:
   ```bash
   #!/bin/bash
   repos=("user/repo1" "user/repo2" "user/repo3")
   for repo in "${repos[@]}"; do
     echo "Scanning $repo..."
     curl -X POST "http://localhost:8000/api/v1/scan" \
       -H "Content-Type: application/json" \
       -d "{\"repository_url\": \"https://github.com/$repo\"}"
   done
   ``` 