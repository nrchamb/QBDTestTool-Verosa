"""
QuickBooks Desktop connection manager using COM (pywin32).
"""

import win32com.client
from typing import Optional, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QBConnectionError(Exception):
    """Exception raised for QB connection errors."""
    pass


def _parse_qb_error(error) -> str:
    """
    Parse QuickBooks COM error and return user-friendly message.

    Args:
        error: The exception object from COM

    Returns:
        User-friendly error message
    """
    error_str = str(error)

    # Common error codes
    if '-2147220472' in error_str or '0x80040408' in error_str:
        return (
            "QuickBooks Desktop is not running or no company file is open.\n\n"
            "Please:\n"
            "1. Start QuickBooks Desktop\n"
            "2. Open a company file\n"
            "3. Try again"
        )
    elif '-2147220445' in error_str or '0x80040423' in error_str:
        return (
            "QuickBooks Desktop is not set to allow access.\n\n"
            "Please:\n"
            "1. Open QuickBooks Desktop\n"
            "2. Go to Edit > Preferences > Integrated Applications\n"
            "3. Make sure this application is authorized"
        )
    elif '-2147467259' in error_str or '0x80004005' in error_str:
        return (
            "QuickBooks access denied or file is locked.\n\n"
            "Please:\n"
            "1. Make sure QuickBooks Desktop is not in use by another application\n"
            "2. Close any other applications that might be accessing QuickBooks\n"
            "3. Try again"
        )
    elif 'Could not start QuickBooks' in error_str:
        return (
            "Could not connect to QuickBooks Desktop.\n\n"
            "Please:\n"
            "1. Make sure QuickBooks Desktop is running\n"
            "2. Open a company file\n"
            "3. Grant permission when prompted"
        )
    elif 'user cancelled' in error_str.lower():
        return "Connection cancelled by user."
    else:
        # Return the original error for unknown cases
        return f"QuickBooks connection error:\n{error_str}"


class QBConnection:
    """
    Manages connections to QuickBooks Desktop using COM.

    Follows the pattern of opening/closing connections after each action or batch
    to allow other applications to connect to QuickBooks.
    """

    def __init__(self, app_name: str = "QBDTestTool-Verosa", app_id: str = ""):
        """
        Initialize QB connection manager.

        Args:
            app_name: Application name for QB connection
            app_id: Application ID (optional, can be empty for testing)
        """
        self.app_name = app_name
        self.app_id = app_id
        self.qb_app = None
        self.ticket = None
        self.session_manager = None

    def connect(self, company_file: Optional[str] = None) -> bool:
        """
        Open connection to QuickBooks.

        Args:
            company_file: Path to company file (None = currently open file)

        Returns:
            True if connected successfully

        Raises:
            QBConnectionError: If connection fails
        """
        try:
            # Create the QB session manager object
            self.session_manager = win32com.client.Dispatch("QBXMLRP2.RequestProcessor")

            # Open connection to QuickBooks
            self.session_manager.OpenConnection2(self.app_id, self.app_name, 1)  # 1 = localQBD
            logger.info(f"Connection opened to QuickBooks: {self.app_name}")

            # Begin session
            if company_file:
                self.ticket = self.session_manager.BeginSession(company_file, 2)  # 2 = qbFileOpenDoNotCare
            else:
                self.ticket = self.session_manager.BeginSession("", 1)  # 1 = qbFileOpenSingleUser

            logger.info("Session started with QuickBooks")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to QuickBooks: {str(e)}")
            friendly_message = _parse_qb_error(e)
            raise QBConnectionError(friendly_message)

    def disconnect(self) -> bool:
        """
        Close connection to QuickBooks.

        Returns:
            True if disconnected successfully
        """
        try:
            if self.session_manager and self.ticket:
                self.session_manager.EndSession(self.ticket)
                logger.info("Session ended")

            if self.session_manager:
                self.session_manager.CloseConnection()
                logger.info("Connection closed")

            self.ticket = None
            self.session_manager = None
            return True

        except Exception as e:
            logger.error(f"Error during disconnect: {str(e)}")
            return False

    def send_request(self, qbxml_request: str) -> str:
        """
        Send QBXML request to QuickBooks.

        Args:
            qbxml_request: QBXML formatted request string

        Returns:
            QBXML response string

        Raises:
            QBConnectionError: If request fails or no connection
        """
        if not self.session_manager or not self.ticket:
            raise QBConnectionError("Not connected to QuickBooks. Call connect() first.")

        try:
            logger.debug(f"Sending request:\n{qbxml_request}")
            response = self.session_manager.ProcessRequest(self.ticket, qbxml_request)
            logger.debug(f"Received response:\n{response}")
            return response

        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            friendly_message = _parse_qb_error(e)
            raise QBConnectionError(friendly_message)

    def execute_request(self, qbxml_request: str, company_file: Optional[str] = None) -> str:
        """
        Execute a request with automatic connect/disconnect.

        This is the recommended method for single requests, as it follows
        the pattern of opening/closing connections to avoid blocking other apps.

        Args:
            qbxml_request: QBXML formatted request string
            company_file: Path to company file (None = currently open file)

        Returns:
            QBXML response string

        Raises:
            QBConnectionError: If request fails
        """
        try:
            self.connect(company_file)
            response = self.send_request(qbxml_request)
            return response
        finally:
            self.disconnect()

    def __enter__(self):
        """Context manager support for batch operations."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.disconnect()
        return False


# Convenience function for single requests
def execute_qbxml_request(qbxml_request: str, company_file: Optional[str] = None) -> str:
    """
    Execute a single QBXML request with automatic connection management.

    Args:
        qbxml_request: QBXML formatted request string
        company_file: Path to company file (None = currently open file)

    Returns:
        QBXML response string

    Example:
        >>> from qbxml_builder import QBXMLBuilder
        >>> request = QBXMLBuilder.build_account_query()
        >>> response = execute_qbxml_request(request)
    """
    connection = QBConnection()
    return connection.execute_request(qbxml_request, company_file)
