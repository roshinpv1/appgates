#!/bin/bash

# Proxy Configuration Script
# Usage: source set_proxy.sh

# Default proxy settings (modify these as needed)
PROXY_HOST="proxy.example.com"
PROXY_PORT="8080"
PROXY_USER=""
PROXY_PASS=""

# Set proxy URLs
if [ -n "$PROXY_USER" ] && [ -n "$PROXY_PASS" ]; then
    # With authentication
    export HTTP_PROXY="http://${PROXY_USER}:${PROXY_PASS}@${PROXY_HOST}:${PROXY_PORT}"
    export HTTPS_PROXY="http://${PROXY_USER}:${PROXY_PASS}@${PROXY_HOST}:${PROXY_PORT}"
else
    # Without authentication
    export HTTP_PROXY="http://${PROXY_HOST}:${PROXY_PORT}"
    export HTTPS_PROXY="http://${PROXY_HOST}:${PROXY_PORT}"
fi

# Set NO_PROXY (domains that should bypass the proxy)
export NO_PROXY="localhost,127.0.0.1,.local,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"

# Also set lowercase versions (some applications use these)
export http_proxy="$HTTP_PROXY"
export https_proxy="$HTTPS_PROXY"
export no_proxy="$NO_PROXY"

echo "✅ Proxy settings configured:"
echo "   HTTP_PROXY: $HTTP_PROXY"
echo "   HTTPS_PROXY: $HTTPS_PROXY"
echo "   NO_PROXY: $NO_PROXY"
echo ""
echo "💡 To use these settings:"
echo "   source set_proxy.sh"
echo ""
echo "💡 To unset proxy settings:"
echo "   unset HTTP_PROXY HTTPS_PROXY NO_PROXY http_proxy https_proxy no_proxy"
