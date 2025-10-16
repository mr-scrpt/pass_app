#!/bin/bash
# Build script for Pass CLI with Keyboard Total Control pip package

set -e

echo "📦 Building Pass CLI with Keyboard Total Control pip package..."

# Check if build module is installed
if ! python3 -c "import build" &> /dev/null; then
    echo "❌ 'build' module not found. Installing..."
    pip install build
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info/

# Build package
echo "🔨 Building wheel and source distribution..."
python3 -m build

# Check if build was successful
if [ -f dist/*.whl ]; then
    echo "✅ Build successful!"
    echo "📍 Package location: $(pwd)/dist/"
    ls -lh dist/
    echo ""
    echo "To install locally:"
    echo "  pip install dist/pass_cli_with_keyboard_total_control-*.whl"
    echo ""
    echo "To upload to PyPI (requires account):"
    echo "  pip install twine"
    echo "  twine upload dist/*"
else
    echo "❌ Build failed!"
    exit 1
fi
