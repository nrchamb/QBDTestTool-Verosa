"""
Logging utilities for QuickBooks Desktop Test Tool.

Provides logging functions for create and monitor tabs.
"""

import tkinter as tk
from datetime import datetime


def log_create(app, message: str):
    """
    Log message to create tab.

    Args:
        app: Reference to the main QBDTestToolApp instance
        message: Message to log
    """
    timestamp = datetime.now().strftime('%H:%M:%S')
    app.create_log.insert(tk.END, f"[{timestamp}] {message}\n")
    app.create_log.see(tk.END)


def log_monitor(app, message: str):
    """
    Log message to monitor tab.

    Args:
        app: Reference to the main QBDTestToolApp instance
        message: Message to log
    """
    timestamp = datetime.now().strftime('%H:%M:%S')
    app.monitor_log.insert(tk.END, f"[{timestamp}] {message}\n")
    app.monitor_log.see(tk.END)
