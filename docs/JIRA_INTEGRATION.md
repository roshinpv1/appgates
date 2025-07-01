# JIRA Integration

The MyGates platform supports optional JIRA integration to automatically post Hard Gate Assessment reports as comments to JIRA issues. This integration is completely configuration-driven and does not affect existing functionality.

## Features

- 🔗 **Automatic posting** of scan reports to JIRA issues
- 📝 **Configurable comment formats** (Markdown or Plain Text)
- 📎 **HTML report attachments** for comprehensive analysis
- ⚙️ **Flexible configuration** via environment variables or config files
- 🎯 **Per-scan overrides** for issue keys and formatting options
- 🔒 **Secure authentication** using JIRA API tokens
- 🧪 **Connection testing** to verify JIRA configuration
- 📊 **Rich formatting** with executive summaries, gate details, and recommendations

## Configuration

### Environment Variables

Set these environment variables to enable JIRA integration:

```bash
# Enable JIRA integration
JIRA_ENABLED=true

# JIRA instance configuration
JIRA_URL=https://your-company.atlassian.net
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=your-api-token

# Optional: Default project and issue
JIRA_PROJECT_KEY=PROJECT
JIRA_ISSUE_KEY=PROJECT-123

# Optional: Comment formatting and attachments
JIRA_COMMENT_FORMAT=markdown  # or 'text'
JIRA_INCLUDE_DETAILS=true
JIRA_INCLUDE_RECOMMENDATIONS=true
JIRA_ATTACH_HTML_REPORT=false  # Enable to attach detailed HTML reports
```

### Configuration File

Alternatively, create a `config/jira_config.json` file:

```json
{
  "enabled": true,
  "jira_url": "https://your-company.atlassian.net",
  "username": "your-email@company.com",
  "api_token": "your-api-token",
  "project_key": "PROJECT",
  "issue_key": "PROJECT-123",
  "comment_format": "markdown",
  "include_details": true,
  "include_recommendations": true,
  "attach_html_report": false,
  "custom_fields": {}
}
```

### Getting a JIRA API Token

1. Log into your JIRA instance
2. Go to **Account Settings** → **Security** → **API tokens**
3. Click **Create API token**
4. Give it a label (e.g., "MyGates Integration")
5. Copy the generated token and use it as `JIRA_API_TOKEN`

## Usage

### 1. Automatic Integration (During Scan)

Include JIRA options in your scan request:

```json
{
  "repository_url": "https://github.com/user/repo",
  "branch": "main",
  "jira_options": {
    "enabled": true,
    "issue_key": "PROJ-123",
    "comment_format": "markdown",
    "include_details": true,
    "include_recommendations": true,
    "attach_html_report": true
  }
}
```

### 2. Manual Posting (After Scan)

Post an existing scan result to JIRA:

```bash
curl -X POST "http://localhost:8000/api/v1/jira/post" \
  -H "Content-Type: application/json" \
  -d '{
    "scan_id": "your-scan-id",
    "issue_key": "PROJ-123",
    "comment_format": "markdown",
    "include_details": true,
    "include_recommendations": true,
    "attach_html_report": true
  }'
```

### 3. Testing Connection

Test your JIRA configuration:

```bash
curl "http://localhost:8000/api/v1/jira/status"
```

## Comment Formats

### Markdown Format (Default)

Generates rich markdown comments with:
- 📊 Executive summary table
- 🟢🟡🔴 Compliance indicators
- 📋 Categorized gate details
- 💡 Actionable recommendations
- 🔗 Links to detailed reports

### Text Format

Generates plain text comments suitable for basic JIRA instances:
- Simple text formatting
- Clean section headers
- Numbered recommendations
- Essential metrics only

## HTML Report Attachments

When `attach_html_report` is enabled, the integration will:

- 📎 **Attach detailed HTML report** to the JIRA issue alongside the comment
- 🎨 **Include rich visualizations** with charts, tables, and interactive elements
- 📋 **Provide comprehensive gate analysis** with full pattern match details
- 🔍 **Enable offline viewing** of complete assessment results
- 📝 **Add attachment notification** to the comment footer

### HTML Attachment Benefits

1. **Complete Analysis**: The HTML report contains full details that may be truncated in comments
2. **Rich Formatting**: Interactive tables, charts, and visual indicators
3. **Offline Access**: Download and view reports without API access
4. **Archival**: Permanent record attached to the JIRA issue
5. **Sharing**: Easy to forward complete reports to stakeholders

### Configuration Examples

**Enable attachments globally:**
```bash
JIRA_ATTACH_HTML_REPORT=true
```

**Enable per-scan:**
```json
{
  "jira_options": {
    "attach_html_report": true
  }
}
```

## API Endpoints

### Check JIRA Status
```
GET /api/v1/jira/status
```

Returns JIRA integration status, configuration, and connection test results.

### Manual Post to JIRA
```
POST /api/v1/jira/post
```

Posts an existing scan report to a specified JIRA issue.

**Request Body:**
```json
{
  "scan_id": "uuid",
  "issue_key": "PROJ-123",
  "comment_format": "markdown",
  "include_details": true,
  "include_recommendations": true,
  "attach_html_report": true
}
```

## Security Considerations

- 🔒 **API Tokens**: Use JIRA API tokens, not passwords
- 🎯 **Minimal Permissions**: Grant only necessary permissions to the JIRA user
- 🔐 **Environment Variables**: Store sensitive data in environment variables
- 🚫 **No Logging**: Sensitive information is not logged

## Troubleshooting

### JIRA Integration Not Available
```
⚠️ JIRA integration not available
```
**Solution**: Ensure all required dependencies are installed and the integration module is properly imported.

### Missing Configuration
```
⚠️ JIRA integration disabled: Missing required configuration
```
**Solution**: Set required environment variables: `JIRA_URL`, `JIRA_USERNAME`, `JIRA_API_TOKEN`.

### Authentication Failed
```
JIRA connection failed: 401 - Unauthorized
```
**Solution**: 
- Verify your JIRA API token is correct
- Ensure the username matches the token owner
- Check if the token has required permissions

### Issue Not Found
```
JIRA API error: 404 - Issue does not exist
```
**Solution**:
- Verify the issue key format (e.g., `PROJECT-123`)
- Ensure the issue exists and you have access to it
- Check the project key is correct

### Network Issues
```
JIRA connection error: timeout
```
**Solution**:
- Verify the JIRA URL is correct and accessible
- Check network connectivity to your JIRA instance
- Ensure firewall rules allow outbound HTTPS connections

## Example Configurations

### Cloud JIRA (Atlassian Cloud)
```bash
JIRA_ENABLED=true
JIRA_URL=https://yourcompany.atlassian.net
JIRA_USERNAME=user@company.com
JIRA_API_TOKEN=your-cloud-api-token
```

### Server JIRA (Self-hosted)
```bash
JIRA_ENABLED=true
JIRA_URL=https://jira.yourcompany.com
JIRA_USERNAME=username
JIRA_API_TOKEN=your-server-api-token
```

### Development Environment
```bash
JIRA_ENABLED=false  # Disable for development
```

## Sample JIRA Comment

When enabled, the integration posts rich comments like this to your JIRA issues:

```markdown
## 🛡️ Hard Gate Assessment Report

**Generated:** 2024-01-15 14:30:00
**Repository:** https://github.com/user/repo
**Branch:** main
**Scan ID:** 123e4567-e89b-12d3-a456-426614174000

---

### 📊 Executive Summary

| Metric | Value |
|--------|-------|
| **Overall Score** | **75.2%** |
| Total Gates | 15 |
| ✅ Implemented | 8 |
| ⚠️ Partial | 3 |
| ❌ Failed | 2 |
| 🚫 Not Applicable | 2 |
| Files Analyzed | 156 |
| Lines of Code | 12,543 |

🟡 **MODERATE COMPLIANCE** - Some improvements needed

### 🔍 Gate Details

#### Auditability
| Gate | Status | Score | Coverage |
|------|--------|-------|----------|
| Structured Logs | ✅ PASS | 85.0% | 78.5% |
| Avoid Logging Secrets | ⚠️ WARNING | 65.0% | 60.0% |

### 💡 Recommendations

1. Implement structured logging across all service endpoints
2. Add correlation IDs to improve request tracing
3. Enhance error handling in user-facing components

---
*Report generated by CodeGates Hard Gate Assessment* | [View Detailed Report](http://localhost:8000/api/v1/reports/scan-id)
```

This integration enhances your development workflow by bringing quality gate results directly into your project management process! 