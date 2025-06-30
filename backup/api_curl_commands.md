# MyGates API - Curl Commands Reference

This file contains curl commands for all available API endpoints in the MyGates server.

## Configuration

Default server URL: `http://localhost:8000`
API base path: `/api/v1`

## Health Check

### Basic Health Check
```bash
curl -X GET "http://localhost:8000/api/v1/health"
```

### Health Check with Headers
```bash
curl -I -X GET "http://localhost:8000/api/v1/health"
```

## Repository Scanning

### Basic Scan (Public Repository)
```bash
curl -X POST "http://localhost:8000/api/v1/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.com/octocat/Hello-World",
    "branch": "master"
  }'
```

### Scan with GitHub Token (Private Repository)
```bash
curl -X POST "http://localhost:8000/api/v1/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.com/username/private-repo",
    "branch": "main",
    "github_token": "ghp_your_github_token_here"
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

### Scan with API Preferred Checkout
```bash
curl -X POST "http://localhost:8000/api/v1/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.com/username/repository",
    "branch": "main",
    "github_token": "your_token",
    "scan_options": {
      "prefer_api_checkout": true,
      "enable_api_fallback": true
    }
  }'
```

### Scan with Custom Timeouts
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

## Intake Assessment (OCP Migration)

### Check Intake Module Status
```bash
curl -X GET "http://localhost:8000/api/v1/intake/status"
```

### Check Intake Module Status with Pretty JSON
```bash
curl -s -X GET "http://localhost:8000/api/v1/intake/status" | jq '.'
```

### Extract Data from Excel File (Utility)
```bash
curl -X POST "http://localhost:8000/api/v1/intake/extract-excel" \
  -H "Content-Type: application/json" \
  -d '{
    "excel_file_path": "/path/to/component_data.xlsx",
    "sheet_name": "Components"
  }'
```

### Start Intake Assessment (GitHub Repository Only)
```bash
curl -X POST "http://localhost:8000/api/v1/intake/assess" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.com/username/repository",
    "github_token": "your_github_token",
    "options": {
      "include_patterns": ["*.py", "*.js", "*.java", "*.go"],
      "exclude_patterns": ["tests/*", "node_modules/*"],
      "max_file_size": 100000,
      "use_cache": true,
      "include_jira": false
    }
  }'
```

### Start Intake Assessment (Repository + Component Data)
```bash
curl -X POST "http://localhost:8000/api/v1/intake/assess" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.com/username/repository",
    "github_token": "your_github_token",
    "component_data": {
      "component_name": "My Web Application",
      "business_criticality": "High",
      "current_environment": "TAS",
      "application_type": "Web Service",
      "technology_stack": {
        "language": "Java",
        "framework": "Spring Boot",
        "database": "PostgreSQL"
      },
      "dependencies": ["Redis", "Kafka", "LDAP"],
      "component_declarations": {
        "redis": true,
        "kafka": true,
        "ldap": true,
        "database": true,
        "postgresql": true,
        "mysql": false,
        "mongodb": false
      }
    },
    "options": {
      "use_cache": true,
      "include_jira": false
    }
  }'
```

### Start Intake Assessment (Component Data Only - No Code)
```bash
curl -X POST "http://localhost:8000/api/v1/intake/assess" \
  -H "Content-Type: application/json" \
  -d '{
    "component_data": {
      "component_name": "Legacy Payment Service",
      "business_criticality": "Critical",
      "current_environment": "On-Premises",
      "application_type": "Microservice",
      "technology_stack": {
        "language": "Python",
        "framework": "Django",
        "database": "Oracle"
      },
      "component_declarations": {
        "database": true,
        "oracle": true,
        "postgresql": false,
        "auth": true,
        "ldap": true,
        "soap_calls": true,
        "rest_api": true
      },
      "custom_fields": {
        "team": "Payments Team",
        "contact": "payments@company.com",
        "migration_priority": "High"
      }
    },
    "options": {
      "use_cache": true
    }
  }'
```

### Start Intake Assessment (Local Directory)
```bash
curl -X POST "http://localhost:8000/api/v1/intake/assess" \
  -H "Content-Type: application/json" \
  -d '{
    "local_directory": "/path/to/local/project",
    "component_data": {
      "component_name": "Local Development Project",
      "business_criticality": "Medium",
      "current_environment": "Development",
      "application_type": "API Service"
    },
    "options": {
      "include_patterns": ["*.py", "*.js", "*.yaml"],
      "use_cache": true
    }
  }'
```

### Complete Workflow: Excel → Component Data → Assessment
```bash
# Step 1: Extract data from Excel file
EXCEL_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/intake/extract-excel" \
  -H "Content-Type: application/json" \
  -d '{
    "excel_file_path": "/path/to/component_data.xlsx"
  }')

echo "Excel Extraction Response: $EXCEL_RESPONSE"

# Step 2: Extract component data from response (requires jq)
COMPONENT_DATA=$(echo $EXCEL_RESPONSE | jq '.component_data')

# Step 3: Start assessment with extracted component data and repository
ASSESSMENT_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/intake/assess" \
  -H "Content-Type: application/json" \
  -d "{
    \"repository_url\": \"https://github.com/username/repository\",
    \"github_token\": \"your_github_token\",
    \"component_data\": $COMPONENT_DATA,
    \"options\": {
      \"use_cache\": true
    }
  }")

echo "Assessment started: $ASSESSMENT_RESPONSE"
```

### Get Intake Assessment Status
```bash
# Replace {assessment_id} with actual assessment ID
curl -X GET "http://localhost:8000/api/v1/intake/assess/{assessment_id}/status"
```

### Get Intake Assessment Status with Pretty JSON
```bash
curl -s -X GET "http://localhost:8000/api/v1/intake/assess/{assessment_id}/status" | jq '.'
```

### Get OCP Assessment Report (HTML)
```bash
# Replace {assessment_id} with actual assessment ID
curl -X GET "http://localhost:8000/api/v1/intake/assess/{assessment_id}/reports/ocp_assessment" \
  -H "Accept: text/html" \
  -o "ocp_assessment_{assessment_id}.html"
```

### Get Hard Gate Assessment Report
```bash
curl -s -X GET "http://localhost:8000/api/v1/intake/assess/{assessment_id}/reports/hard_gate_assessment" | jq '.'
```

### Get Intake Assessment Report (HTML)
```bash
curl -X GET "http://localhost:8000/api/v1/intake/assess/{assessment_id}/reports/intake_assessment" \
  -H "Accept: text/html" \
  -o "intake_assessment_{assessment_id}.html"
```

### List All Intake Assessments
```bash
curl -X GET "http://localhost:8000/api/v1/intake/assessments"
```

### List All Intake Assessments with Pretty JSON
```bash
curl -s -X GET "http://localhost:8000/api/v1/intake/assessments" | jq '.'
```

### Component Data Examples

#### Example 1: Simple Component Data
```json
{
  "component_name": "User Authentication Service",
  "business_criticality": "High",
  "current_environment": "TKGI",
  "application_type": "Microservice"
}
```

#### Example 2: Detailed Component Data with Technology Stack
```json
{
  "component_name": "Order Processing API",
  "business_criticality": "Critical",
  "current_environment": "TAS",
  "application_type": "REST API",
  "technology_stack": {
    "primary_language": "Java",
    "framework": "Spring Boot",
    "build_tool": "Maven",
    "database": "PostgreSQL",
    "cache": "Redis",
    "messaging": "RabbitMQ"
  },
  "dependencies": [
    "PostgreSQL Database",
    "Redis Cache", 
    "RabbitMQ",
    "LDAP Authentication",
    "External Payment Gateway"
  ],
  "component_declarations": {
    "database": true,
    "postgresql": true,
    "mysql": false,
    "redis": true,
    "rabbitmq": true,
    "kafka": false,
    "ldap": true,
    "auth": true,
    "rest_api": true,
    "soap_calls": false,
    "splunk": true,
    "appd": false
  },
  "custom_fields": {
    "team_owner": "Platform Team",
    "business_owner": "John Doe",
    "migration_timeline": "Q2 2024",
    "compliance_requirements": ["PCI-DSS", "SOX"],
    "peak_traffic": "10000 requests/hour"
  }
}
```

### Legacy Excel File Support
For backwards compatibility, you can still extract from Excel files first:

```bash
# 1. Extract from Excel
curl -X POST "http://localhost:8000/api/v1/intake/extract-excel" \
  -H "Content-Type: application/json" \
  -d '{
    "excel_file_path": "/path/to/legacy_components.xlsx",
    "sheet_name": "ComponentData"
  }' > extracted_data.json

# 2. Use extracted data for assessment
curl -X POST "http://localhost:8000/api/v1/intake/assess" \
  -H "Content-Type: application/json" \
  -d "{
    \"repository_url\": \"https://github.com/company/legacy-app\",
    \"component_data\": $(cat extracted_data.json | jq '.component_data'),
    \"options\": {\"use_cache\": true}
  }"
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
curl -X GET "http://localhost:8000/api/v1/reports/{scan_id}"
```

### Save HTML Report to File
```bash
curl -X GET "http://localhost:8000/api/v1/reports/{scan_id}" \
  -H "Accept: text/html" \
  -o "scan_report_{scan_id}.html"
```

### List All Available Reports
```bash
curl -X GET "http://localhost:8000/api/v1/reports"
```

### List Reports with Pretty JSON
```bash
curl -s -X GET "http://localhost:8000/api/v1/reports" | jq '.'
```

## JIRA Integration

### Get JIRA Status
```bash
curl -X GET "http://localhost:8000/api/v1/jira/status"
```

### Get JIRA Status with Pretty JSON
```bash
curl -s -X GET "http://localhost:8000/api/v1/jira/status" | jq '.'
```

### Manually Post Scan to JIRA (Markdown Format)
```bash
curl -X POST "http://localhost:8000/api/v1/jira/post" \
  -H "Content-Type: application/json" \
  -d '{
    "scan_id": "12345678-1234-1234-1234-123456789abc",
    "issue_key": "PROJECT-123",
    "comment_format": "markdown",
    "include_details": true,
    "include_recommendations": true
  }'
```

### Manually Post Scan to JIRA (Text Format)
```bash
curl -X POST "http://localhost:8000/api/v1/jira/post" \
  -H "Content-Type: application/json" \
  -d '{
    "scan_id": "12345678-1234-1234-1234-123456789abc",
    "issue_key": "PROJECT-456",
    "comment_format": "text",
    "include_details": false,
    "include_recommendations": true
  }'
```

## System Management

### Manual Cleanup
```bash
curl -X GET "http://localhost:8000/api/v1/system/cleanup"
```

### Get Temporary Directory Status
```bash
curl -X GET "http://localhost:8000/api/v1/system/temp-status"
```

### Get Temporary Directory Status with Pretty JSON
```bash
curl -s -X GET "http://localhost:8000/api/v1/system/temp-status" | jq '.'
```

### Get Timeout Configuration
```bash
curl -X GET "http://localhost:8000/api/v1/system/timeout-config"
```

### Get Timeout Configuration with Pretty JSON
```bash
curl -s -X GET "http://localhost:8000/api/v1/system/timeout-config" | jq '.'
```

## CORS and Preflight

### CORS Preflight Request
```bash
curl -X OPTIONS "http://localhost:8000/api/v1/scan" \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type"
```

### CORS Preflight for Reports
```bash
curl -X OPTIONS "http://localhost:8000/api/v1/reports" \
  -H "Origin: vscode-webview://123" \
  -H "Access-Control-Request-Method: GET"
```

## Complete Workflow Examples

### Example 1: Basic Workflow
```bash
# 1. Start a scan
SCAN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.com/octocat/Hello-World",
    "branch": "master"
  }')

echo "Scan Response: $SCAN_RESPONSE"

# 2. Extract scan ID
SCAN_ID=$(echo $SCAN_RESPONSE | jq -r '.scan_id')
echo "Scan ID: $SCAN_ID"

# 3. Check status (repeat until completed)
curl -s -X GET "http://localhost:8000/api/v1/scan/$SCAN_ID/status" | jq '.'

# 4. Get HTML report once completed
curl -X GET "http://localhost:8000/api/v1/reports/$SCAN_ID" > "report_$SCAN_ID.html"
```

### Example 2: Private Repository with JIRA
```bash
# 1. Start scan with JIRA integration
SCAN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.com/company/private-repo",
    "branch": "main",
    "github_token": "your_github_token",
    "scan_options": {
      "threshold": 80,
      "analysis_timeout": 600
    },
    "jira_options": {
      "enabled": true,
      "issue_key": "DEV-123",
      "comment_format": "markdown"
    }
  }')

SCAN_ID=$(echo $SCAN_RESPONSE | jq -r '.scan_id')
echo "Monitoring scan: $SCAN_ID"

# 2. Monitor progress
while true; do
  STATUS=$(curl -s -X GET "http://localhost:8000/api/v1/scan/$SCAN_ID/status" | jq -r '.status')
  echo "Status: $STATUS"
  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    break
  fi
  sleep 5
done

# 3. Get final results
curl -s -X GET "http://localhost:8000/api/v1/scan/$SCAN_ID/status" | jq '.'
```

### Example 3: GitHub Enterprise Workflow
```bash
# 1. Scan GitHub Enterprise repository
curl -X POST "http://localhost:8000/api/v1/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.enterprise.com/company/project",
    "branch": "main",
    "github_token": "your_enterprise_token",
    "scan_options": {
      "verify_ssl": false,
      "prefer_api_checkout": true,
      "enable_api_fallback": true,
      "threshold": 70
    }
  }'
```

## Error Testing

### Test Invalid Repository URL
```bash
curl -X POST "http://localhost:8000/api/v1/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "invalid-url",
    "branch": "main"
  }'
```

### Test Non-existent Repository
```bash
curl -X POST "http://localhost:8000/api/v1/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.com/nonexistent/repository",
    "branch": "main"
  }'
```

### Test Invalid Branch
```bash
curl -X POST "http://localhost:8000/api/v1/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.com/octocat/Hello-World",
    "branch": "nonexistent-branch"
  }'
```

### Test Non-existent Scan ID
```bash
curl -X GET "http://localhost:8000/api/v1/scan/non-existent-id/status"
```

### Test Invalid JIRA Issue Key
```bash
curl -X POST "http://localhost:8000/api/v1/jira/post" \
  -H "Content-Type: application/json" \
  -d '{
    "scan_id": "valid-scan-id",
    "issue_key": "INVALID",
    "comment_format": "markdown"
  }'
```

## Performance Testing

### Test with Large Repository
```bash
curl -X POST "http://localhost:8000/api/v1/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.com/microsoft/vscode",
    "branch": "main",
    "scan_options": {
      "analysis_timeout": 1800,
      "threshold": 60
    }
  }'
```

### Test with Custom Timeouts
```bash
curl -X POST "http://localhost:8000/api/v1/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.com/username/repository",
    "branch": "main",
    "scan_options": {
      "git_clone_timeout": 60,
      "analysis_timeout": 120,
      "llm_request_timeout": 10
    }
  }'
```

## Utility Commands

### Check if Server is Running
```bash
curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1 && echo "Server is running" || echo "Server is not responding"
```

### Get All System Information
```bash
echo "=== Health Check ==="
curl -s http://localhost:8000/api/v1/health | jq '.'

echo -e "\n=== Timeout Configuration ==="
curl -s http://localhost:8000/api/v1/system/timeout-config | jq '.'

echo -e "\n=== JIRA Status ==="
curl -s http://localhost:8000/api/v1/jira/status | jq '.'

echo -e "\n=== Temp Directory Status ==="
curl -s http://localhost:8000/api/v1/system/temp-status | jq '.'

echo -e "\n=== Available Reports ==="
curl -s http://localhost:8000/api/v1/reports | jq '.'
```

## Notes

1. **Replace placeholders**: 
   - `{scan_id}` with actual scan IDs from scan responses
   - `your_github_token` with real GitHub tokens
   - `your_enterprise_token` with GitHub Enterprise tokens
   - Repository URLs with actual repositories

2. **Required tools**:
   - `curl` for API requests
   - `jq` for JSON formatting (optional but recommended)

3. **Server configuration**:
   - Default server runs on `http://localhost:8000`
   - Modify the URL if running on different host/port

4. **Authentication**:
   - Public repositories don't require tokens
   - Private repositories require GitHub tokens with `repo` scope
   - GitHub Enterprise may require SSL configuration

5. **Timeouts**:
   - Default timeouts are configured server-side
   - Can be overridden per-request via `scan_options`
   - Analysis of large repositories may require increased timeouts

6. **JIRA Integration**:
   - Requires JIRA configuration in server environment
   - Check JIRA status before attempting to post comments
   - Issue keys must be valid and accessible with configured credentials

7. **Error Handling**:
   - API returns appropriate HTTP status codes
   - Error messages are provided in JSON format
   - Check response status before processing results 