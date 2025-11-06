"""
Logging utilities for QuickBooks Desktop Test Tool.

Provides logging functions with log levels and rolling buffer support.
"""

import tkinter as tk
from datetime import datetime
from config import AppConfig
from .logging_config import should_log, LOG_NORMAL

# Maximum number of log messages to retain (rolling buffer)
MAX_LOG_MESSAGES = 250
BATCH_DELETE_SIZE = 50  # Delete in batches for performance


def log_create(app, message: str, level: str = LOG_NORMAL):
    """
    Log message to create tab with log level filtering and rolling buffer.

    Args:
        app: Reference to the main QBDTestToolApp instance
        message: Message to log
        level: Log level (MINIMAL, NORMAL, VERBOSE, DEBUG)
    """
    # Check if message should be logged based on current level
    current_level = AppConfig.get_log_level()
    if not should_log(level, current_level):
        return

    # Apply rolling buffer (keep only last MAX_LOG_MESSAGES)
    _apply_rolling_buffer(app.create_log)

    # Log the message
    timestamp = datetime.now().strftime('%H:%M:%S')
    app.create_log.insert(tk.END, f"[{timestamp}] {message}\n")
    app.create_log.see(tk.END)


def log_monitor(app, message: str, level: str = LOG_NORMAL):
    """
    Log message to monitor tab with log level filtering and rolling buffer.

    Args:
        app: Reference to the main QBDTestToolApp instance
        message: Message to log
        level: Log level (MINIMAL, NORMAL, VERBOSE, DEBUG)
    """
    # Check if message should be logged based on current level
    current_level = AppConfig.get_log_level()
    if not should_log(level, current_level):
        return

    # Apply rolling buffer (keep only last MAX_LOG_MESSAGES)
    _apply_rolling_buffer(app.monitor_log)

    # Log the message
    timestamp = datetime.now().strftime('%H:%M:%S')
    app.monitor_log.insert(tk.END, f"[{timestamp}] {message}\n")
    app.monitor_log.see(tk.END)


def _apply_rolling_buffer(text_widget):
    """
    Apply rolling buffer to text widget - delete oldest messages if over limit.

    Args:
        text_widget: ScrolledText widget to apply rolling buffer to
    """
    # Get all text and count lines
    content = text_widget.get("1.0", "end-1c")
    line_count = len(content.split("\n"))

    # If over limit, delete oldest BATCH_DELETE_SIZE lines
    if line_count > MAX_LOG_MESSAGES:
        # Delete lines 1 through BATCH_DELETE_SIZE
        text_widget.delete("1.0", f"{BATCH_DELETE_SIZE + 1}.0")
