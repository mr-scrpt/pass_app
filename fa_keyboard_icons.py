"""
Font Awesome keyboard icons with custom transformations
"""

import qtawesome as qta
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap


def get_fa_keyboard_icon(key_name, color="#FFFFFF", size=64):
    """
    Get a Font Awesome icon for keyboard keys with custom transformations.

    Args:
        key_name: Name of the key ('enter', 'escape', 'backspace', etc.)
        color: Hex color for the icon
        size: Size in pixels for rendering

    Returns:
        QIcon with the keyboard icon
    """

    # Map key names to Font Awesome icons
    icon_map = {
        "escape": "fa5s.times",
        "backspace": "fa5s.backspace",
        "delete": "fa5s.trash",
        "enter": "fa5s.level-up-alt",  # Will be transformed
        "return": "fa5s.level-up-alt",  # Will be transformed
        "up": "fa5s.arrow-up",
        "down": "fa5s.arrow-down",
        "left": "fa5s.arrow-left",
        "right": "fa5s.arrow-right",
        "tab": "fa5s.arrow-right",
        "shift": "fa5s.arrow-up",
        "ctrl": "fa5s.keyboard",
        "alt": "fa5s.keyboard",
        "space": "fa5s.minus",
    }

    icon_name = icon_map.get(key_name.lower())
    if not icon_name:
        return QIcon()

    # Special handling for Enter key: flip horizontally then rotate 90° clockwise
    if key_name.lower() in ["enter", "return"]:
        return _create_transformed_enter_icon(icon_name, color, size)

    # Special handling for Backspace: render with larger canvas to avoid clipping
    if key_name.lower() == "backspace":
        return _create_enlarged_icon(icon_name, color, size)

    # For other icons, use qtawesome directly
    try:
        return qta.icon(icon_name, color=color)
    except Exception as e:
        print(f"Error loading icon {icon_name}: {e}")
        return QIcon()


def _create_transformed_enter_icon(icon_name, color, size):
    """
    Create Enter icon with horizontal flip + 90° clockwise rotation.
    """
    try:
        # Get the base icon
        base_icon = qta.icon(icon_name, color=color)

        # Render to pixmap
        source_pixmap = base_icon.pixmap(QSize(size, size))

        # Create final pixmap for the result
        final_pixmap = QPixmap(size, size)
        final_pixmap.fill(Qt.transparent)

        painter = QPainter(final_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # Move painter to center of canvas
        painter.translate(size / 2, size / 2)

        # Apply transformations in order:
        # 1. Flip horizontally (scale x by -1)
        painter.scale(-1, 1)

        # 2. Rotate 90 degrees clockwise
        painter.rotate(90)

        # Draw the original pixmap centered (offset by half its size)
        painter.drawPixmap(-size / 2, -size / 2, source_pixmap)

        painter.end()

        return QIcon(final_pixmap)

    except Exception as e:
        print(f"Error creating transformed enter icon: {e}")
        import traceback

        traceback.print_exc()
        # Fallback to base icon
        return qta.icon(icon_name, color=color)


def _create_enlarged_icon(icon_name, color, size):
    """
    Create icon with enlarged canvas to avoid clipping (for backspace, etc).
    """
    try:
        # Get the base icon
        base_icon = qta.icon(icon_name, color=color)

        # Use a larger canvas to avoid clipping
        work_size = int(size * 1.5)  # 50% larger to avoid edge clipping

        # Render to larger pixmap
        source_pixmap = base_icon.pixmap(QSize(work_size, work_size))

        # Scale down to target size with smooth scaling
        final_pixmap = source_pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        return QIcon(final_pixmap)

    except Exception as e:
        print(f"Error creating enlarged icon: {e}")
        # Fallback to base icon
        return qta.icon(icon_name, color=color)


def get_fa_keyboard_icon_for_button(key_name, color="#FFFFFF"):
    """
    Get keyboard icon optimized for button display (higher resolution).

    Args:
        key_name: Name of the key
        color: Hex color for the icon

    Returns:
        QIcon suitable for buttons
    """
    return get_fa_keyboard_icon(key_name, color, size=128)
