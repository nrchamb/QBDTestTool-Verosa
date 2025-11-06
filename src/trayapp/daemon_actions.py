"""
Daemon process action handlers for QuickBooks Desktop Test Tool.

Handles graceful and forced shutdown of the connection manager daemon.
"""

from config import AppConfig
from qb_ipc_client import stop_manager


def on_closing(app):
    """
    Handle graceful application shutdown.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    # Set tray icon to yellow (shutting down)
    if hasattr(app, 'tray_icon'):
        app.tray_icon.set_state('yellow')

    # Stop monitoring if active
    if app.monitoring_stop_flag is False and hasattr(app, 'monitor_thread'):
        app.monitoring_stop_flag = True
        if app.monitor_thread and app.monitor_thread.is_alive():
            print("Waiting for monitoring thread to stop...")
            app.monitor_thread.join(timeout=5.0)

    # Stop connection manager
    print("Stopping connection manager...")
    stop_manager()

    # Stop tray icon
    if hasattr(app, 'tray_icon'):
        app.tray_icon.stop()

    # Save window geometry before closing
    try:
        geometry = app.root.winfo_geometry()  # Returns "widthxheight+x+y"
        # Parse geometry string: "900x700+100+50"
        parts = geometry.replace('+', ' ').replace('x', ' ').split()
        if len(parts) == 4:
            width, height, x, y = map(int, parts)
            AppConfig.save_window_geometry(width, height, x, y)
            print(f"Saved window geometry: {width}x{height}+{x}+{y}")
    except Exception as e:
        print(f"Error saving window geometry: {e}")

    # Destroy window
    app.root.destroy()


def force_close(app):
    """
    Force close connection manager and exit immediately.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    print("Force closing connection manager...")

    # Set tray icon to yellow
    if hasattr(app, 'tray_icon'):
        app.tray_icon.set_state('yellow')

    # Import for process termination
    from qb_ipc_client import _manager_process

    # Kill manager process immediately
    if _manager_process and _manager_process.is_alive():
        print(f"Terminating manager process (PID: {_manager_process.pid})")
        _manager_process.terminate()
        _manager_process.join(timeout=2.0)

        if _manager_process.is_alive():
            print("Manager still alive, killing forcefully...")
            _manager_process.kill()

    # Stop tray icon
    if hasattr(app, 'tray_icon'):
        app.tray_icon.stop()

    # Destroy window
    app.root.destroy()
