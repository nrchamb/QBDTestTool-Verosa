"""
Tray app package for QuickBooks Desktop Test Tool.

Handles system tray icon and daemon process management.
"""

from .tray_icon import TrayIconManager
from .daemon_actions import on_closing, force_close

__all__ = [
    'TrayIconManager',
    'on_closing',
    'force_close',
]
