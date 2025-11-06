"""
QuickBooks IPC Client

Drop-in replacement for QBConnection that communicates with
the connection manager process via multiprocessing queues.
"""

import time
import uuid
import threading
from multiprocessing import Queue, Process
from typing import Optional
from queue import Empty


# Global references to manager process and queues
_manager_process: Optional[Process] = None
_request_queue: Optional[Queue] = None
_response_queue: Optional[Queue] = None
_heartbeat_thread: Optional[threading.Thread] = None
_heartbeat_stop_flag = False


class QBIPCClient:
    """
    QuickBooks IPC client that communicates with connection manager.

    Drop-in replacement for QBConnection class.
    """

    @staticmethod
    def execute_request(qbxml_request: str, company_file: Optional[str] = None) -> str:
        """
        Execute a QBXML request via the connection manager process.

        Args:
            qbxml_request: QBXML request string
            company_file: Optional path to company file

        Returns:
            QBXML response string

        Raises:
            Exception: If request fails or times out
        """
        global _request_queue, _response_queue

        if not _request_queue or not _response_queue:
            raise Exception("Connection manager not started. Call start_manager() first.")

        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Create request message
        request = {
            'type': 'request',
            'request_id': request_id,
            'qbxml': qbxml_request,
            'company_file': company_file
        }

        # Send request to manager
        try:
            _request_queue.put(request, timeout=5.0)
        except Exception as e:
            raise Exception(f"Failed to send request to connection manager: {e}")

        # Wait for response with timeout
        timeout = 30.0  # 30 seconds
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = _response_queue.get(timeout=0.5)

                # Check if this is our response
                if response.get('request_id') == request_id:
                    if response.get('success'):
                        return response.get('response')
                    else:
                        error = response.get('error', 'Unknown error')
                        raise Exception(f"QB request failed: {error}")

                else:
                    # Not our response, put it back (shouldn't happen with sequential processing)
                    _response_queue.put(response)

            except Empty:
                # No response yet, keep waiting
                continue

        # Timeout
        raise Exception(f"Request timed out after {timeout} seconds")

    def __enter__(self):
        """Context manager entry (no-op for IPC client)."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit (no-op for IPC client)."""
        return False


def start_manager():
    """Start the connection manager process and heartbeat thread."""
    global _manager_process, _request_queue, _response_queue, _heartbeat_thread, _heartbeat_stop_flag

    if _manager_process and _manager_process.is_alive():
        print("[IPC Client] Connection manager already running")
        return

    # Create queues for IPC
    _request_queue = Queue()
    _response_queue = Queue()

    # Start connection manager process
    from qb_connection_manager import run_connection_manager

    _manager_process = Process(
        target=run_connection_manager,
        args=(_request_queue, _response_queue),
        daemon=False  # Not daemon so it can cleanup properly
    )
    _manager_process.start()

    # Start heartbeat thread
    _heartbeat_stop_flag = False
    _heartbeat_thread = threading.Thread(target=_heartbeat_loop, daemon=True)
    _heartbeat_thread.start()

    print(f"[IPC Client] Connection manager started (PID: {_manager_process.pid})")


def disconnect_qb():
    """Request the connection manager to disconnect from QuickBooks."""
    global _request_queue

    if not _request_queue:
        return

    try:
        disconnect_msg = {'type': 'disconnect'}
        _request_queue.put(disconnect_msg, timeout=2.0)
    except Exception as e:
        print(f"[IPC Client] Error sending disconnect: {e}")


def stop_manager():
    """Stop the connection manager process gracefully."""
    global _manager_process, _request_queue, _heartbeat_stop_flag, _heartbeat_thread

    if not _manager_process or not _manager_process.is_alive():
        print("[IPC Client] Connection manager not running")
        return

    print("[IPC Client] Stopping connection manager...")

    # Stop heartbeat thread
    _heartbeat_stop_flag = True
    if _heartbeat_thread:
        _heartbeat_thread.join(timeout=2.0)

    # Send shutdown message
    if _request_queue:
        try:
            shutdown_msg = {'type': 'shutdown'}
            _request_queue.put(shutdown_msg, timeout=2.0)
        except Exception as e:
            print(f"[IPC Client] Error sending shutdown: {e}")

    # Wait for manager to exit gracefully
    if _manager_process:
        _manager_process.join(timeout=5.0)

        if _manager_process.is_alive():
            print("[IPC Client] Manager did not exit gracefully, terminating...")
            _manager_process.terminate()
            _manager_process.join(timeout=2.0)

    print("[IPC Client] Connection manager stopped")


def _heartbeat_loop():
    """Send periodic heartbeats to connection manager."""
    global _request_queue, _heartbeat_stop_flag

    heartbeat_interval = 5.0  # Send heartbeat every 5 seconds

    while not _heartbeat_stop_flag:
        try:
            if _request_queue:
                heartbeat_msg = {
                    'type': 'heartbeat',
                    'timestamp': time.time()
                }
                _request_queue.put(heartbeat_msg, timeout=1.0)

        except Exception as e:
            print(f"[IPC Client] Error sending heartbeat: {e}")

        # Wait before next heartbeat
        time.sleep(heartbeat_interval)


def is_manager_alive() -> bool:
    """Check if connection manager is still running."""
    global _manager_process
    return _manager_process is not None and _manager_process.is_alive()
