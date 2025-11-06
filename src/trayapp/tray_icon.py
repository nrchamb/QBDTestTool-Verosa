"""
System Tray Icon Utilities

Manages system tray icon for connection manager status.
"""

from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item
import threading
from typing import Callable, Optional


class TrayIconManager:
    """Manages system tray icon for the application."""

    def __init__(self, on_exit: Callable, on_force_close: Callable):
        """
        Initialize tray icon manager.

        Args:
            on_exit: Callback for normal exit
            on_force_close: Callback for force close
        """
        self.on_exit = on_exit
        self.on_force_close = on_force_close
        self.icon: Optional[pystray.Icon] = None
        self.tray_thread: Optional[threading.Thread] = None
        self.current_state = 'green'

    def create_icon_image(self, color: str) -> Image.Image:
        """
        Create a colored circle icon.

        Args:
            color: 'green' or 'yellow'

        Returns:
            PIL Image of colored circle
        """
        # Create 64x64 image with transparency
        size = 64
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Define colors
        colors = {
            'green': (0, 200, 0, 255),    # Bright green
            'yellow': (255, 200, 0, 255)  # Yellow/orange
        }

        fill_color = colors.get(color, colors['green'])

        # Draw circle
        margin = 4
        draw.ellipse(
            [margin, margin, size - margin, size - margin],
            fill=fill_color,
            outline=(0, 0, 0, 255),
            width=2
        )

        return image

    def create_menu(self) -> pystray.Menu:
        """
        Create tray icon menu.

        Returns:
            pystray.Menu with Exit and Force Close options
        """
        return pystray.Menu(
            item('Exit', self._handle_exit),
            item('Force Close', self._handle_force_close)
        )

    def _handle_exit(self, icon, item):
        """Handle Exit menu item."""
        # Stop the tray icon
        icon.stop()
        # Call the exit callback
        self.on_exit()

    def _handle_force_close(self, icon, item):
        """Handle Force Close menu item."""
        # Stop the tray icon
        icon.stop()
        # Call the force close callback
        self.on_force_close()

    def start(self):
        """Start the tray icon in a background thread."""
        if self.icon and self.icon.visible:
            print("[Tray Icon] Already running")
            return

        # Create icon with green state
        green_image = self.create_icon_image('green')
        self.icon = pystray.Icon(
            'QBDTestTool',
            green_image,
            'QB Connection Manager',
            menu=self.create_menu()
        )

        # Run in background thread
        self.tray_thread = threading.Thread(target=self.icon.run, daemon=True)
        self.tray_thread.start()
        print("[Tray Icon] Started")

    def set_state(self, state: str):
        """
        Update tray icon color.

        Args:
            state: 'green' or 'yellow'
        """
        if self.icon and state != self.current_state:
            self.current_state = state
            new_image = self.create_icon_image(state)
            self.icon.icon = new_image
            print(f"[Tray Icon] State changed to {state}")

    def stop(self):
        """Stop the tray icon."""
        if self.icon:
            self.icon.stop()
            self.icon = None
            print("[Tray Icon] Stopped")
