"""
Application configuration management.

Handles loading and saving of application settings including window geometry,
logging preferences, and persistence options.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


# Config directory and file paths
CONFIG_DIR = Path.home() / ".qbd_test_tool"
CONFIG_FILE = CONFIG_DIR / "config.json"


# Default configuration
DEFAULT_CONFIG = {
    "window": {
        "width": 900,
        "height": 700,
        "x": None,  # None = OS default
        "y": None
    },
    "logging": {
        "level": "NORMAL"  # MINIMAL, NORMAL, VERBOSE, DEBUG
    },
    "persistence": {
        "auto_load": False,  # Auto-load previous session on startup
        "verify_on_load": True  # Verify transactions against QB on load
    }
}


class AppConfig:
    """Application configuration manager."""

    @staticmethod
    def ensure_config_dir():
        """Ensure config directory exists."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def load_config() -> Dict[str, Any]:
        """
        Load configuration from file.

        Returns:
            Config dict, or default config if file doesn't exist
        """
        AppConfig.ensure_config_dir()

        if not CONFIG_FILE.exists():
            return DEFAULT_CONFIG.copy()

        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            # Merge with defaults to handle new config keys
            return {**DEFAULT_CONFIG, **config}
        except Exception as e:
            print(f"Error loading config: {e}")
            return DEFAULT_CONFIG.copy()

    @staticmethod
    def save_config(config: Dict[str, Any]) -> bool:
        """
        Save configuration to file.

        Args:
            config: Configuration dict to save

        Returns:
            True if successful, False otherwise
        """
        AppConfig.ensure_config_dir()

        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    @staticmethod
    def get_window_geometry() -> Dict[str, Optional[int]]:
        """
        Get saved window geometry.

        Returns:
            Dict with width, height, x, y
        """
        config = AppConfig.load_config()
        return config.get('window', DEFAULT_CONFIG['window'])

    @staticmethod
    def save_window_geometry(width: int, height: int, x: int, y: int) -> bool:
        """
        Save window geometry.

        Args:
            width: Window width in pixels
            height: Window height in pixels
            x: Window x position
            y: Window y position

        Returns:
            True if successful
        """
        config = AppConfig.load_config()
        config['window'] = {
            'width': width,
            'height': height,
            'x': x,
            'y': y
        }
        return AppConfig.save_config(config)

    @staticmethod
    def get_log_level() -> str:
        """
        Get saved log verbosity level.

        Returns:
            Log level string (MINIMAL, NORMAL, VERBOSE, DEBUG)
        """
        config = AppConfig.load_config()
        return config.get('logging', {}).get('level', 'NORMAL')

    @staticmethod
    def save_log_level(level: str) -> bool:
        """
        Save log verbosity level.

        Args:
            level: Log level (MINIMAL, NORMAL, VERBOSE, DEBUG)

        Returns:
            True if successful
        """
        config = AppConfig.load_config()
        if 'logging' not in config:
            config['logging'] = {}
        config['logging']['level'] = level
        return AppConfig.save_config(config)

    @staticmethod
    def get_persistence_settings() -> Dict[str, bool]:
        """
        Get persistence settings.

        Returns:
            Dict with auto_load and verify_on_load flags
        """
        config = AppConfig.load_config()
        return config.get('persistence', DEFAULT_CONFIG['persistence'])

    @staticmethod
    def save_persistence_settings(auto_load: bool, verify_on_load: bool) -> bool:
        """
        Save persistence settings.

        Args:
            auto_load: Whether to auto-load previous session
            verify_on_load: Whether to verify transactions on load

        Returns:
            True if successful
        """
        config = AppConfig.load_config()
        config['persistence'] = {
            'auto_load': auto_load,
            'verify_on_load': verify_on_load
        }
        return AppConfig.save_config(config)
