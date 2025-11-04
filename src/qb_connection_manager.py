"""
QuickBooks Connection Manager Process

Runs as a separate process to manage QuickBooks connections.
Provides isolation so that main app crashes don't orphan QB connections.
Monitors main app health via heartbeat and exits gracefully if main app dies.
"""

import time
import pythoncom
from multiprocessing import Queue
from typing import Optional, Dict, Any
from datetime import datetime
from qb_connection import QBConnection


class QBConnectionManager:
    """Connection manager that runs in separate process."""

    def __init__(self, request_queue: Queue, response_queue: Queue):
        """
        Initialize connection manager.

        Args:
            request_queue: Queue to receive requests from main app
            response_queue: Queue to send responses to main app
        """
        self.request_queue = request_queue
        self.response_queue = response_queue
        self.running = True
        self.last_heartbeat = time.time()
        self.heartbeat_timeout = 15.0  # Exit if no heartbeat for 15 seconds
        self.qb_connection = None
        self.connection_active = False  # Track if QB connection is currently active

    def run(self):
        """Main event loop for connection manager."""
        # Initialize COM for this process
        pythoncom.CoInitialize()

        try:
            print("[QB Manager] Connection manager started")
            self.last_heartbeat = time.time()

            while self.running:
                # Check for requests with timeout
                try:
                    # Wait for request with 1 second timeout to check heartbeat
                    if not self.request_queue.empty():
                        message = self.request_queue.get(timeout=1.0)
                        self._handle_message(message)
                    else:
                        # No message, just check heartbeat
                        time.sleep(0.1)

                    # Check if main app is still alive
                    if time.time() - self.last_heartbeat > self.heartbeat_timeout:
                        print("[QB Manager] No heartbeat detected, main app appears dead")
                        print("[QB Manager] Initiating graceful shutdown...")
                        self.running = False
                        break

                except Exception as e:
                    print(f"[QB Manager] Error in main loop: {e}")
                    time.sleep(0.1)

        except KeyboardInterrupt:
            print("[QB Manager] Received interrupt signal")
        finally:
            self._cleanup()
            pythoncom.CoUninitialize()
            print("[QB Manager] Connection manager stopped")

    def _handle_message(self, message: Dict[str, Any]):
        """
        Handle incoming message from main app.

        Args:
            message: Message dict with type and data
        """
        msg_type = message.get('type')

        if msg_type == 'heartbeat':
            # Update last heartbeat timestamp
            self.last_heartbeat = time.time()

        elif msg_type == 'shutdown':
            # Graceful shutdown requested
            print("[QB Manager] Shutdown requested by main app")
            self.running = False

        elif msg_type == 'request':
            # QB request to execute
            self._handle_request(message)

        else:
            print(f"[QB Manager] Unknown message type: {msg_type}")

    def _handle_request(self, message: Dict[str, Any]):
        """
        Handle QuickBooks request.

        Args:
            message: Request message with request_id, qbxml, company_file
        """
        request_id = message.get('request_id')
        qbxml = message.get('qbxml')
        company_file = message.get('company_file')

        response = {
            'request_id': request_id,
            'success': False,
            'response': None,
            'error': None
        }

        # Wait for previous connection to fully close
        timeout = 5.0  # 5 second timeout
        wait_start = time.time()
        while self.connection_active:
            if time.time() - wait_start > timeout:
                response['error'] = "Timeout waiting for previous connection to close"
                print(f"[QB Manager] Connection timeout for request {request_id}")
                self.response_queue.put(response, timeout=5.0)
                return
            time.sleep(0.05)  # Check every 50ms

        # Mark connection as active
        self.connection_active = True

        try:
            # Execute request using QBConnection instance
            # This uses execute_request which has finally block protection
            qb = QBConnection()
            qb_response = qb.execute_request(qbxml, company_file)

            response['success'] = True
            response['response'] = qb_response

        except Exception as e:
            response['success'] = False
            response['error'] = str(e)
            print(f"[QB Manager] Error executing request {request_id}: {e}")

        finally:
            # Mark connection as inactive (ready for next request)
            self.connection_active = False

        # Send response back to main app
        try:
            self.response_queue.put(response, timeout=5.0)
        except Exception as e:
            print(f"[QB Manager] Error sending response: {e}")

    def _cleanup(self):
        """Clean up resources before exit."""
        print("[QB Manager] Cleaning up resources...")

        # Close any open QB connections
        if self.qb_connection:
            try:
                self.qb_connection.disconnect()
            except Exception as e:
                print(f"[QB Manager] Error disconnecting: {e}")

        # Note: QBConnection.execute_request already handles cleanup via finally block
        # This is just extra safety in case we ever hold persistent connections

        print("[QB Manager] Cleanup complete")


def run_connection_manager(request_queue: Queue, response_queue: Queue):
    """
    Entry point for connection manager process.

    Args:
        request_queue: Queue to receive requests
        response_queue: Queue to send responses
    """
    manager = QBConnectionManager(request_queue, response_queue)
    manager.run()


if __name__ == '__main__':
    # For testing purposes only
    print("Connection manager should not be run directly")
    print("It will be started by the main application")
