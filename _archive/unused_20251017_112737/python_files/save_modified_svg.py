import os
import re

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
    if 'fill="none"' in path_tag or 'class="st1"' in path_tag:
        return path_tag
    if "fill=" not in path_tag:
        return path_tag.replace("<path", f'<path fill="{color}"', 1)
    return path_tag


svg_content = re.sub(r"<path[^>]*>", replace_path, svg_content)

svg_content = re.sub(r"fill:\s*#000000", f"fill: {color}", svg_content)
svg_content = re.sub(r"fill:\s*#000\b", f"fill: {color}", svg_content)
svg_content = re.sub(r"fill:\s*black\b", f"fill: {color}", svg_content)

with open("modified_escape.svg", "w") as f:
    f.write(svg_content)

print("Saved modified SVG to modified_escape.svg")
print("\nKey changes:")
print("- Stroke color changed in CSS")
print("- Fill attribute added to text paths")
