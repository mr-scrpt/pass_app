import os
import re

ICON_ROOT = os.path.join(os.path.dirname(__file__), 'icon', 'keyboard', 'icons')
filepath = os.path.join(ICON_ROOT, 'icon-escape.svg')

with open(filepath, 'r') as f:
    svg_content = f.read()

color = '#f38ba8'

# Replace black colors
svg_content = svg_content.replace('stroke:#000000', f'stroke:{color}')
svg_content = svg_content.replace('stroke:#000', f'stroke:{color}')
svg_content = svg_content.replace('stroke:black', f'stroke:{color}')
svg_content = svg_content.replace('fill:#000000', f'fill:{color}')
svg_content = svg_content.replace('fill:#000', f'fill:{color}')
svg_content = svg_content.replace('fill:black', f'fill:{color}')

# Print style section
print("Style section after color replacement:")
lines = svg_content.split('\n')
in_style = False
for line in lines:
    if '<style' in line:
        in_style = True
    if in_style:
        print(line)
    if '</style>' in line:
        in_style = False
        break
