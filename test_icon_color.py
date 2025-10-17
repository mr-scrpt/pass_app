import os
import re

from icon_utils import get_keyboard_icon

# Test loading an icon with red color
icon = get_keyboard_icon("escape", color="#f38ba8")

# Let's also manually check what happens to the SVG
ICON_ROOT = os.path.join(os.path.dirname(__file__), "icon", "keyboard", "icons")
filepath = os.path.join(ICON_ROOT, "icon-escape.svg")

with open(filepath, "r") as f:
    svg_content = f.read()

color = "#f38ba8"

# Replace black colors
svg_content = svg_content.replace("stroke:#000000", f"stroke:{color}")
svg_content = svg_content.replace("stroke:#000", f"stroke:{color}")
svg_content = svg_content.replace("stroke:black", f"stroke:{color}")
svg_content = svg_content.replace("fill:#000000", f"fill:{color}")
svg_content = svg_content.replace("fill:#000", f"fill:{color}")
svg_content = svg_content.replace("fill:black", f"fill:{color}")


# Find all path tags
def replace_path(match):
    path_tag = match.group(0)
    if 'fill="none"' in path_tag or 'class="st1"' in path_tag or 'class="st0"' in path_tag:
        return path_tag
    if "fill=" not in path_tag:
        return path_tag.replace("<path", f'<path fill="{color}"', 1)
    return path_tag


svg_content = re.sub(r"<path[^>]*>", replace_path, svg_content)

# Print a sample of modified SVG to see what changed
print("Modified SVG sample:")
lines = svg_content.split("\n")
for i, line in enumerate(lines[15:25], start=15):  # Show lines with path elements
    print(f"{i}: {line}")

print("\nIcon loaded successfully:", icon is not None and not icon.isNull())
