#!/bin/bash
# Build script for Pass CLI with Keyboard Total Control executable

set -e

echo "🔨 Building Pass CLI with Keyboard Total Control executable..."

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "❌ PyInstaller not found. Installing..."
    pip install pyinstaller
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/

# Build executable
echo "📦 Building executable with PyInstaller..."
pyinstaller pass-kb.spec

# Check if build was successful
if [ -f "dist/pass-kb" ]; then
    echo "✅ Build successful!"
    echo "📍 Executable location: $(pwd)/dist/pass-kb"
    echo ""
    echo "To run:"
    echo "  ./dist/pass-kb"
    echo ""
    echo "To install system-wide (optional):"
    echo "  sudo cp dist/pass-kb /usr/local/bin/"
else
    echo "❌ Build failed!"
    exit 1
fi
