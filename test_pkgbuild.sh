#!/bin/bash
# Script to test PKGBUILD locally before publishing to AUR

set -e

echo "==> Testing PKGBUILD locally..."

# Create test directory
TEST_DIR="/tmp/pkgbuild-test-$(date +%s)"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

# Copy PKGBUILD
cp /home/mr/Hellkitchen/solution/pass/project/PKGBUILD .

echo "==> Generating .SRCINFO..."
makepkg --printsrcinfo > .SRCINFO

echo "==> Building package..."
makepkg -f

echo ""
echo "✅ SUCCESS! Package built successfully."
echo ""
echo "Package location: $TEST_DIR"
echo ""
echo "To install locally for testing:"
echo "  makepkg -si"
echo ""
echo "To clean up:"
echo "  rm -rf $TEST_DIR"
