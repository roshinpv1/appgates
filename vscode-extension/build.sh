#!/bin/bash

# CodeGates VS Code Extension Build Script
set -e

echo "🔧 Building CodeGates VS Code Extension..."

# Check Node.js version
NODE_VERSION=$(node --version)
echo "📦 Node.js version: $NODE_VERSION"

# Use Node 16 if available via nvm
if command -v nvm &> /dev/null; then
    echo "🔄 Switching to Node.js 16..."
    nvm use 16 2>/dev/null || echo "⚠️ Node.js 16 not available via nvm"
fi

# Clean previous build
echo "🧹 Cleaning previous build..."
rm -rf node_modules
rm -rf out
rm -f package-lock.json

# Install dependencies with legacy peer deps to avoid conflicts
echo "📦 Installing dependencies..."
npm install --legacy-peer-deps

# Install specific compatible versions to avoid ES module issues
echo "🔧 Installing compatible versions..."
npm install --save-dev @vscode/vsce@2.19.0 --legacy-peer-deps
npm install --save axios@0.27.2 --legacy-peer-deps

# Force install compatible glob/minimatch versions
npm install --save-dev minimatch@5.1.6 --legacy-peer-deps
npm install --save-dev glob@8.1.0 --legacy-peer-deps

# Compile TypeScript
echo "🔨 Compiling TypeScript..."
npx tsc -p ./

# Package the extension
echo "📦 Packaging extension..."
npx vsce package --allow-star-activation

echo "✅ Build completed successfully!"
echo "📄 Extension package created: codegates-*.vsix"

# List the generated files
ls -la *.vsix 2>/dev/null || echo "No .vsix files found" 