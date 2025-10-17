import os
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QByteArray, Qt

ICON_ROOT = os.path.join(os.path.dirname(__file__), 'icon', 'keyboard', 'icons')

ICON_FILES = {
    "enter": "icon-enter.svg",
    "escape": "icon-escape.svg",
    "backspace": "icon-backspace.svg",
}

def get_keyboard_icon(name, color="#FFFFFF") -> QIcon:
    """Loads a keyboard SVG icon from a file and applies color transformation.
    
    Args:
        name: Name of the icon (e.g., 'enter', 'escape', 'backspace')
        color: Hex color to apply to the icon (default: white)
    
    Returns:
        QIcon with the colored icon
    """
    filename = ICON_FILES.get(name)
    if not filename:
        return QIcon()

    filepath = os.path.join(ICON_ROOT, filename)
    
    try:
        # Read the SVG file
        with open(filepath, 'r') as f:
            svg_content = f.read()
        
        # Replace black colors with desired color (both stroke and fill)
        svg_content = svg_content.replace('stroke:#000000', f'stroke:{color}')
        svg_content = svg_content.replace('stroke:#000', f'stroke:{color}')
        svg_content = svg_content.replace('stroke:black', f'stroke:{color}')
        svg_content = svg_content.replace('fill:#000000', f'fill:{color}')
        svg_content = svg_content.replace('fill:#000', f'fill:{color}')
        svg_content = svg_content.replace('fill:black', f'fill:{color}')
        
        # More aggressive approach: add fill attribute to all <path> elements that don't have fill="none"
        import re
        
        # Find all path tags
        def replace_path(match):
            path_tag = match.group(0)
            # Skip only if it has fill="none" or class="st1" (which is fill:none in CSS)
            # st0 is stroke, not fill:none, so we need to process it
            if 'fill="none"' in path_tag or 'class="st1"' in path_tag:
                return path_tag
            # Add fill attribute if not present
            if 'fill=' not in path_tag:
                # Insert fill right after <path
                return path_tag.replace('<path', f'<path fill="{color}"', 1)
            return path_tag
        
        svg_content = re.sub(r'<path[^>]*>', replace_path, svg_content)
        
        # Also replace the default fill color in CSS if present
        svg_content = re.sub(r'fill:\s*#000000', f'fill: {color}', svg_content)
        svg_content = re.sub(r'fill:\s*#000\b', f'fill: {color}', svg_content)
        svg_content = re.sub(r'fill:\s*black\b', f'fill: {color}', svg_content)
        
        # Convert to QByteArray for Qt
        svg_bytes = QByteArray(svg_content.encode('utf-8'))
        
        # Create renderer and pixmap
        renderer = QSvgRenderer(svg_bytes)
        pixmap = QPixmap(128, 128)  # Higher resolution for better quality
        pixmap.fill(Qt.transparent)
        
        # Render SVG to pixmap
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        
        return QIcon(pixmap)
    except Exception as e:
        print(f"Error loading icon {name}: {e}")
        return QIcon()
