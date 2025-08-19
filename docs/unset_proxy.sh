#!/bin/bash

# Unset Proxy Configuration Script
# Usage: source unset_proxy.sh

# Unset all proxy environment variables
unset HTTP_PROXY
unset HTTPS_PROXY
unset NO_PROXY
unset http_proxy
unset https_proxy
unset no_proxy

echo "✅ Proxy settings cleared"
echo "   All proxy environment variables have been unset"
