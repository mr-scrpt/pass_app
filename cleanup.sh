#!/bin/bash
# Cleanup script - moves development artifacts to _archive folder
# Run this before publishing to AUR

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ARCHIVE_DIR="_archive"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE_PATH="${ARCHIVE_DIR}/${TIMESTAMP}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Project Cleanup Script                ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════╝${NC}"
echo ""

# Create archive directory
mkdir -p "$ARCHIVE_PATH"
echo -e "${GREEN}✓${NC} Created archive directory: $ARCHIVE_PATH"
echo ""

# Function to move file/directory to archive
move_to_archive() {
    local item=$1
    if [ -e "$item" ]; then
        echo -e "${YELLOW}→${NC} Moving: $item"
        mv "$item" "$ARCHIVE_PATH/"
    fi
}

echo -e "${BLUE}Moving development artifacts...${NC}"
echo ""

# 1. Python cache files
echo "1. Python cache files:"
move_to_archive "__pycache__"

# 2. Build artifacts
echo ""
echo "2. Build artifacts:"
move_to_archive "build"
move_to_archive "dist"

# 3. Test files
echo ""
echo "3. Test files:"
move_to_archive "test_icon_color.py"
move_to_archive "test_keyboard_icons.py"
move_to_archive "test_line_edit.py"
move_to_archive "test_svg_mod.py"
move_to_archive "test_svg_mod2.py"
move_to_archive "save_modified_svg.py"

# 4. Unused/old files
echo ""
echo "4. Unused/old files:"
move_to_archive "hotkey_bar.py"
move_to_archive "icon_utils.py"
move_to_archive "modified_escape.svg"

# 5. Development docs (не для релиза)
echo ""
echo "5. Development documentation:"
move_to_archive "SPECS.md"
move_to_archive "HOTKEY_MAP.md"
move_to_archive "RENAME_SUMMARY.md"

# 6. Test data
echo ""
echo "6. Test data:"
move_to_archive ".password-store"

# 7. Icons directory (если не используется)
echo ""
echo "7. Icons directory (проверьте используется ли):"
if [ -d "icon" ]; then
    echo -e "${YELLOW}⚠${NC}  Found 'icon/' directory with many files"
    echo "   Checking if used in code..."
    if grep -r "icon/" --include="*.py" --exclude-dir="_archive" . > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Icons are used in code, keeping them"
    else
        echo -e "${YELLOW}→${NC} Icons don't appear to be used, moving to archive"
        move_to_archive "icon"
    fi
fi

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     Cleanup completed!                    ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════╝${NC}"
echo ""
echo "Archived files location: $ARCHIVE_PATH"
echo ""
echo "Next steps:"
echo "  1. Test the application: python pass_client.py"
echo "  2. Test installation: ./install.sh --user"
echo "  3. If everything works: rm -rf $ARCHIVE_DIR"
echo "  4. If something broke: mv $ARCHIVE_PATH/* . (restore files)"
echo ""
echo "Files remaining in project:"
ls -1 | grep -v "^_archive$" | head -20
echo ""
if [ $(ls -1 | grep -v "^_archive$" | wc -l) -gt 20 ]; then
    echo "... and $(( $(ls -1 | grep -v "^_archive$" | wc -l) - 20 )) more files"
fi
