# CodeGates VS Code Extension Build Instructions

## Prerequisites

- Node.js 16.x (recommended) or 18.x
- npm 8+ or yarn
- VS Code 1.80.0+

## Quick Build (Recommended)

```bash
# Run the automated build script
./build.sh
```

## Manual Build Steps

### 1. Node.js Version (Important!)

Use Node.js 16.x to avoid ES module compatibility issues:

```bash
# If using nvm
nvm use 16

# Check version
node --version  # Should be v16.x.x
```

### 2. Clean Install

```bash
# Navigate to extension directory
cd vscode-extension

# Clean previous builds
rm -rf node_modules out package-lock.json

# Install with legacy peer deps flag to avoid conflicts
npm install --legacy-peer-deps
```

### 3. Install Compatible Versions

```bash
# Install specific compatible versions
npm install --save-dev @vscode/vsce@2.19.0 --legacy-peer-deps
npm install --save axios@0.27.2 --legacy-peer-deps
npm install --save-dev minimatch@5.1.6 --legacy-peer-deps
npm install --save-dev glob@8.1.0 --legacy-peer-deps
```

### 4. Compile and Package

```bash
# Compile TypeScript
npx tsc -p ./

# Package extension
npx vsce package --allow-star-activation
```

## Common Issues & Solutions

### Issue: `ERR_REQUIRE_ESM` with brace-expansion/minimatch

**Solution**: Use Node.js 16.x and the compatible versions specified above.

### Issue: Cannot find module 'axios'

**Solution**: Install axios 0.27.2 specifically:
```bash
npm install --save axios@0.27.2 --legacy-peer-deps
```

### Issue: TypeScript compilation errors

**Solution**: Clean and reinstall:
```bash
rm -rf node_modules out
npm install --legacy-peer-deps
npx tsc -p ./
```

## Output

After successful build, you'll have:
- `codegates-2.0.1.vsix` - The extension package
- `out/` directory with compiled JavaScript

## Installation

Install the built extension in VS Code:

```bash
code --install-extension codegates-2.0.1.vsix
```

## Development

For development with hot reload:

```bash
npm run watch
```

Then press F5 in VS Code to launch Extension Development Host. 