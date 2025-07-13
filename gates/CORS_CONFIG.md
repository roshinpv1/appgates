# CORS Configuration Guide

This document explains how to configure Cross-Origin Resource Sharing (CORS) for the CodeGates FastAPI server.

## Overview

CORS (Cross-Origin Resource Sharing) is a security feature implemented by web browsers that restricts web pages from making requests to a different domain than the one serving the web page. The CodeGates API server includes CORS middleware to allow web applications to make requests to the API.

## Default Configuration

By default, the CodeGates API server is configured with permissive CORS settings suitable for development:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)
```

## Environment Variable Configuration

For production environments, you can configure CORS settings using environment variables:

### CORS_ORIGINS

Controls which origins are allowed to make requests to the API:

```bash
# Allow all origins (development only)
export CORS_ORIGINS="*"

# Allow specific origins (recommended for production)
export CORS_ORIGINS="https://your-frontend.com,https://another-domain.com"

# Allow localhost for development
export CORS_ORIGINS="http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000"
```

## Production Configuration

For production environments, it's recommended to:

1. **Specify exact origins** instead of using `*`
2. **Use HTTPS** for all origins
3. **Limit methods** to only what's needed
4. **Review headers** being exposed

### Example Production Configuration

```bash
# Set specific origins
export CORS_ORIGINS="https://codegates-ui.company.com,https://dashboard.company.com"

# Start the server
python gates/server.py
```

## Development Configuration

For development, you can use more permissive settings:

```bash
# Allow common development ports
export CORS_ORIGINS="http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000,http://localhost:5173"

# Start the server
python gates/server.py
```

## Testing CORS Configuration

### 1. Check CORS Headers

Test that CORS headers are properly set:

```bash
# Test preflight request
curl -X OPTIONS http://localhost:8000/api/v1/health \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v

# Should return CORS headers like:
# Access-Control-Allow-Origin: http://localhost:3000
# Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
# Access-Control-Allow-Headers: *
```

### 2. Test from Browser

Create a simple HTML file to test CORS:

```html
<!DOCTYPE html>
<html>
<head>
    <title>CORS Test</title>
</head>
<body>
    <h1>CodeGates API CORS Test</h1>
    <button onclick="testAPI()">Test API</button>
    <div id="result"></div>

    <script>
    async function testAPI() {
        try {
            const response = await fetch('http://localhost:8000/api/v1/health');
            const data = await response.json();
            document.getElementById('result').innerHTML = 
                '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
        } catch (error) {
            document.getElementById('result').innerHTML = 
                '<p style="color: red;">Error: ' + error.message + '</p>';
        }
    }
    </script>
</body>
</html>
```

### 3. JavaScript Fetch Test

```javascript
// Test API call from browser console
fetch('http://localhost:8000/api/v1/health')
  .then(response => response.json())
  .then(data => console.log('Success:', data))
  .catch(error => console.error('Error:', error));
```

## Common CORS Issues and Solutions

### 1. "CORS policy: No 'Access-Control-Allow-Origin' header"

**Problem**: The server is not sending CORS headers.

**Solution**: 
- Ensure the CORS middleware is properly configured
- Check that the server is running with the updated configuration
- Verify the request is going to the correct URL

### 2. "CORS policy: The request client is not a secure context"

**Problem**: Mixed content (HTTP/HTTPS) issues.

**Solution**:
- Use HTTPS for both frontend and API in production
- For development, ensure both are using the same protocol

### 3. "CORS policy: Credential is not supported if the CORS header 'Access-Control-Allow-Origin' is '*'"

**Problem**: Cannot use `allow_credentials=True` with `allow_origins=["*"]`.

**Solution**:
- Set specific origins instead of `*` when using credentials
- Or set `allow_credentials=False` if credentials are not needed

```bash
# Fix: Use specific origins
export CORS_ORIGINS="https://your-frontend.com"
```

## Security Considerations

### 1. Origin Validation

Always validate origins in production:

```bash
# Good: Specific origins
export CORS_ORIGINS="https://app.company.com,https://dashboard.company.com"

# Bad: Wildcard in production
export CORS_ORIGINS="*"
```

### 2. Credentials Handling

Be careful with credentials:

```python
# If you need to send cookies or authorization headers
allow_credentials=True

# If you don't need credentials (more secure)
allow_credentials=False
```

### 3. Method Restrictions

Limit methods to what's actually needed:

```python
# Current: All common methods
allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]

# More restrictive: Only what's needed
allow_methods=["GET", "POST", "OPTIONS"]
```

## API Endpoints and CORS

All CodeGates API endpoints support CORS:

- `GET /` - Root endpoint
- `GET /api/v1/health` - Health check
- `GET /api/v1/gates` - List gates
- `POST /api/v1/scan` - Start scan
- `GET /api/v1/scan/{scan_id}` - Get scan status
- `GET /api/v1/scan/{scan_id}/report/html` - Get HTML report
- `GET /api/v1/scan/{scan_id}/report/json` - Get JSON report

## Frontend Integration Examples

### React Example

```javascript
// api.js
const API_BASE_URL = 'http://localhost:8000/api/v1';

export const startScan = async (scanRequest) => {
  const response = await fetch(`${API_BASE_URL}/scan`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(scanRequest),
  });
  return response.json();
};

export const getScanStatus = async (scanId) => {
  const response = await fetch(`${API_BASE_URL}/scan/${scanId}`);
  return response.json();
};
```

### Vue.js Example

```javascript
// api.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const startScan = (scanRequest) => {
  return api.post('/scan', scanRequest);
};

export const getScanStatus = (scanId) => {
  return api.get(`/scan/${scanId}`);
};
```

## Troubleshooting

### Enable CORS Debug Logging

Add logging to see CORS processing:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Server Logs

Look for CORS-related messages in server logs:

```bash
# Start server with debug logging
python gates/server.py --log-level debug
```

### Browser Developer Tools

1. Open browser Developer Tools (F12)
2. Go to Network tab
3. Make the request
4. Check the response headers for CORS headers
5. Look for any CORS-related errors in the Console tab

## Summary

The CodeGates API server includes comprehensive CORS support that can be configured for both development and production environments. Use environment variables to control CORS settings and always follow security best practices in production. 