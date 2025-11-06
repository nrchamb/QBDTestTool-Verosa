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
        self.last_request_time = None  # Track last request for idle timeout
        self.idle_timeout = 30.0  # Disconnect after 30 seconds of inactivity

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
                        # No message, just check heartbeat and idle timeout
                        time.sleep(0.1)

                    # Check if main app is still alive
                    if time.time() - self.last_heartbeat > self.heartbeat_timeout:
                        print("[QB Manager] No heartbeat detected, main app appears dead")
                        print("[QB Manager] Initiating graceful shutdown...")
                        self.running = False
                        break

                    # Check for idle timeout - disconnect if no requests for idle_timeout seconds
                    if self.qb_connection and self.last_request_time:
                        idle_time = time.time() - self.last_request_time
                        if idle_time > self.idle_timeout:
                            print(f"[QB Manager] Idle timeout ({idle_time:.1f}s) - disconnecting from QuickBooks")
                            try:
                                self.qb_connection.disconnect()
                                self.connection_active = False
                                self.qb_connection = None
                                self.last_request_time = None
                                print("[QB Manager] Disconnected due to inactivity")
                            except Exception as e:
                                print(f"[QB Manager] Error during idle disconnect: {e}")

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

        elif msg_type == 'disconnect':
            # Explicit disconnect request
            if self.qb_connection:
                print("[QB Manager] Explicit disconnect requested")
                try:
                    self.qb_connection.disconnect()
                    self.connection_active = False
                    self.qb_connection = None
                    self.last_request_time = None
                    print("[QB Manager] Disconnected successfully")
                except Exception as e:
                    print(f"[QB Manager] Error during disconnect: {e}")

        elif msg_type == 'request':
            # QB request to execute
            self._handle_request(message)

        else:
            print(f"[QB Manager] Unknown message type: {msg_type}")

    def _handle_request(self, message: Dict[str, Any]):
        """
        Handle QuickBooks request using persistent connection.

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

        try:
            # Create persistent connection if it doesn't exist
            if not self.qb_connection:
                print(f"[QB Manager] Creating new QB connection")
                self.qb_connection = QBConnection()
                self.qb_connection.connect(company_file)
                self.connection_active = True

            # Update last request time for idle timeout tracking
            self.last_request_time = time.time()

            # Reuse existing connection for request
            qb_response = self.qb_connection.send_request(qbxml)

            response['success'] = True
            response['response'] = qb_response

        except Exception as e:
            response['success'] = False
            response['error'] = str(e)
            print(f"[QB Manager] Error executing request {request_id}: {e}")

            # On error, disconnect and cleanup connection for next request
            if self.qb_connection:
                try:
                    self.qb_connection.disconnect()
                except:
                    pass
                self.qb_connection = None
                self.connection_active = False

        # Send response back to main app
        try:
            self.response_queue.put(response, timeout=5.0)
        except Exception as e:
            print(f"[QB Manager] Error sending response: {e}")

    def _cleanup(self):
        """Clean up resources before exit."""
        print("[QB Manager] Cleaning up resources...")

        # Close persistent QB connection
        if self.qb_connection:
            try:
                print("[QB Manager] Disconnecting from QuickBooks...")
                self.qb_connection.disconnect()
                self.connection_active = False
                self.qb_connection = None
                print("[QB Manager] Disconnected successfully")
            except Exception as e:
                print(f"[QB Manager] Error disconnecting: {e}")

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
