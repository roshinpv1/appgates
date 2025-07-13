# GitHub Enterprise Configuration

This document explains how to configure CodeGates for GitHub Enterprise environments to avoid connection issues like "Connection reset by peer" and SSL certificate verification errors.

## Enterprise Repository Detection

CodeGates automatically detects GitHub Enterprise repositories by checking if the hostname contains "github" but is not "github.com".

Examples:
- `https://github.company.com/user/repo` → GitHub Enterprise
- `https://github.abcd.com/app-sds/repo` → GitHub Enterprise
- `https://github.com/user/repo` → GitHub.com
- `https://git.company.com/user/repo` → Other Git server

## Automatic SSL Certificate Handling

**NEW**: CodeGates now automatically detects and handles SSL certificate issues:

1. **First Attempt**: Uses default SSL verification
2. **Auto-Retry**: If SSL certificate verification fails, automatically retries with SSL disabled
3. **Fallback**: Falls back to Git clone if API fails

## Checkout Method Priority

### GitHub Enterprise Repositories
1. **API First** (preferred for enterprise networks)
   - Tries with SSL verification
   - Auto-retries with SSL disabled if certificate fails
2. **Git Clone** (fallback)
   - Tries with SSL verification  
   - Auto-retries with SSL disabled if certificate fails

### GitHub.com Repositories  
1. **Git Clone** (unlimited, no rate limits)
2. **API** (fallback)

## Configuration Options

### SSL/TLS Issues

#### Quick Fix for Self-Signed Certificates
```bash
# For immediate resolution of SSL certificate issues
export GITHUB_ENTERPRISE_DISABLE_SSL=true
```

#### Proper SSL Configuration (Recommended)
```bash
# Provide custom CA bundle (more secure)
export GITHUB_ENTERPRISE_CA_BUNDLE=/path/to/ca-bundle.crt
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_ENTERPRISE_DISABLE_SSL` | Disable SSL verification | `false` |
| `GITHUB_ENTERPRISE_CA_BUNDLE` | Path to custom CA bundle | Not set |
| `CODEGATES_ENTERPRISE_PREFER_API` | Force API preference for enterprise | `true` |

## Troubleshooting Connection Issues

### 1. SSL Certificate Verification Failed (Self-Signed Certificates)

**Symptoms:**
```
SSLError (SSLCertVerificationError): certificate verify failed: self-signed certificate in certificate chain
```

**Automatic Handling:**
- ✅ CodeGates now automatically detects this error
- ✅ Automatically retries with SSL verification disabled
- ✅ Works for both API and Git clone methods

**Manual Override (if needed):**
```bash
export GITHUB_ENTERPRISE_DISABLE_SSL=true
```

### 2. Connection Reset by Peer

**Symptoms:**
```
Github API download Failed: ('Connection aborted.', ConnectionResetError(54, 'Connection reset by peer'))
```

**Solutions:**
1. **Automatic Fallback:** The system will automatically fallback to git clone
2. **SSL Settings:** Often related to SSL issues, try `GITHUB_ENTERPRISE_DISABLE_SSL=true`
3. **Network Configuration:** Check with your IT team about proxy/firewall settings

### 3. Authentication Issues

**Symptoms:**
```
Authentication failed. Check your GitHub token.
```

**Solutions:**
1. Verify your GitHub token has proper permissions
2. Check if token is expired
3. Ensure token has repository access scope

## Example Usage

### For Self-Signed Certificate Issues (Your Current Issue)
```bash
# Quick fix - disable SSL verification
export GITHUB_ENTERPRISE_DISABLE_SSL=true

# Run CodeGates
python gates/cli.py scan https://github.abcd.com/app-sds/bobgi-appts-by-sd --branch develop
```

### For Proper SSL Configuration
```bash
# Use custom CA bundle (more secure)
export GITHUB_ENTERPRISE_CA_BUNDLE=/etc/ssl/certs/company-ca.crt

# Run CodeGates
python gates/cli.py scan https://github.abcd.com/app-sds/bobgi-appts-by-sd --branch develop
```

## What's New - Automatic SSL Handling

### Enhanced Error Detection
- ✅ Detects `certificate verify failed` errors
- ✅ Detects `self-signed certificate` errors
- ✅ Provides specific error messages with solutions

### Auto-Retry Logic
- ✅ **API Method**: Automatically retries with SSL disabled
- ✅ **Git Clone**: Automatically retries with `GIT_SSL_NO_VERIFY=true`
- ✅ **Fallback**: Falls back between API and Git methods

### Better Debugging
- ✅ Shows SSL configuration being used
- ✅ Indicates when SSL verification is disabled
- ✅ Provides clear success/failure messages

## Network Requirements

For GitHub Enterprise API access, ensure these endpoints are accessible:
- `https://your-github-enterprise.com/api/v3/`
- `https://your-github-enterprise.com/api/v3/repos/*/zipball/*`

For Git clone access:
- `https://your-github-enterprise.com/` (HTTPS Git protocol)
- Port 443 (HTTPS) or 22 (SSH) depending on URL format

## Security Considerations

1. **Automatic SSL Retry**: Only happens for detected GitHub Enterprise repos
2. **Temporary Disable**: SSL is only disabled for the specific operation
3. **Proper CA Bundle**: Use `GITHUB_ENTERPRISE_CA_BUNDLE` for production
4. **Token Security**: Rotate GitHub tokens regularly

## Getting Help

If you continue to experience issues:
1. Check the debug output for SSL configuration messages
2. Try the automatic SSL retry (should work automatically now)
3. Set `GITHUB_ENTERPRISE_DISABLE_SSL=true` for immediate resolution
4. Contact your IT/DevOps team for proper CA bundle
5. Enable debug logging for more details 