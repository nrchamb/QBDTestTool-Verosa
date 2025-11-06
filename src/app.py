"""
Main application entry point - Tkinter GUI for QBD Test Tool.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from datetime import datetime
from typing import Optional
import multiprocessing

from store import (
    Store, AppState, InvoiceRecord, SalesReceiptRecord, StatementChargeRecord,
    add_customer, set_items, set_terms, set_classes, set_accounts, add_invoice, update_invoice,
    add_sales_receipt, update_sales_receipt, add_statement_charge, update_statement_charge,
    set_monitoring, add_verification_result, set_expected_deposit_account
)
from qb_connection import QBConnectionError
from qb_ipc_client import QBIPCClient, start_manager, stop_manager
from qbxml_builder import QBXMLBuilder
from qbxml_parser import QBXMLParser
from trayapp import TrayIconManager, on_closing, force_close
from ui.create_tab_setup import setup_create_tab
from ui.monitor_tab_setup import setup_monitor_tab
from ui.verify_tab_setup import setup_verify_tab
from ui.setup_subtab_setup import setup_setup_subtab
from ui.logging_utils import log_create, log_monitor
from ui.ui_utils import create_scrollable_frame
from actions.customer_actions import create_customer, update_customer_combo
from actions.monitor_actions import update_accounts_combo
from qb_data_loader import QBDataLoader
from workers import (
    load_items_worker, load_terms_worker, load_classes_worker, load_accounts_worker,
    load_customers_worker, load_all_worker, create_customer_worker, create_invoice_worker,
    create_sales_receipt_worker, query_sales_receipt_worker, create_charge_worker
)


class QBDTestToolApp:
    """Main application class."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("QBD Test Tool")
        self.root.geometry("900x700")

        # Initialize Redux store
        self.store = Store()
        self.store.subscribe(self._on_state_change)

        # Customer ListID mapping (to avoid index mismatch with nested jobs)
        self.customer_listid_map = {}  # Maps display_name -> list_id

        # Monitoring thread
        self.monitor_thread: Optional[threading.Thread] = None
        self.monitoring_stop_flag = False

        # Start connection manager process
        start_manager()

        # Initialize tray icon
        self.tray_icon = TrayIconManager(
            on_exit=lambda: on_closing(self),
            on_force_close=lambda: force_close(self)
        )
        self.tray_icon.start()

        # Setup UI
        self._setup_ui()

        # Setup graceful shutdown handler
        self.root.protocol("WM_DELETE_WINDOW", lambda: on_closing(self))

    def _setup_ui(self):
        """Setup the user interface."""
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Tab 1: Create Data
        self.create_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.create_tab, text='Create Data')
        setup_create_tab(self)

        # Tab 2: Monitor Transactions
        self.monitor_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.monitor_tab, text='Monitor Transactions')
        setup_monitor_tab(self)

        # Tab 3: Verification Results
        self.verify_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.verify_tab, text='Verification Results')
        setup_verify_tab(self)

        # Status bar
        self.status_bar = tk.Label(self.root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _create_scrollable_frame(self, parent):
        """Create a scrollable frame (wrapper for ui_utils.create_scrollable_frame)."""
        return create_scrollable_frame(parent)

    # Wrapper methods for logging - kept in app.py for convenience
    def _log_create(self, message: str):
        """Log message to create tab (wrapper for logging_utils.log_create)."""
        log_create(self, message)

    def _log_monitor(self, message: str):
        """Log message to monitor tab (wrapper for logging_utils.log_monitor)."""
        log_monitor(self, message)

### MARK: Wrapper functions that call workers in main app.
# This is done because we disable the button before launching the worker and moving them to a separate file and updating actions in-between is unnecessary overhead for a small action.

    def _load_items(self):
        """Load items from QuickBooks (wrapper - launches background thread)."""
        # Disable button
        self.load_items_btn.config(state='disabled')
        self.status_bar.config(text="Loading items from QuickBooks...")
        self.items_status_label.config(text="Loading...", foreground='orange')

        # Launch background thread
        thread = threading.Thread(target=load_items_worker, args=(self,), daemon=True)
        thread.start()

    def _load_terms(self):
        """Load terms from QuickBooks (wrapper - launches background thread)."""
        # Disable button
        self.load_terms_btn.config(state='disabled')
        self.status_bar.config(text="Loading terms from QuickBooks...")

        # Launch background thread
        thread = threading.Thread(target=load_terms_worker, args=(self,), daemon=True)
        thread.start()

    def _load_classes(self):
        """Load classes from QuickBooks (wrapper - launches background thread)."""
        # Disable button
        self.load_classes_btn.config(state='disabled')
        self.status_bar.config(text="Loading classes from QuickBooks...")

        # Launch background thread
        thread = threading.Thread(target=load_classes_worker, args=(self,), daemon=True)
        thread.start()

    def _load_accounts(self):
        """Load accounts from QuickBooks (wrapper - launches background thread)."""
        # Disable button
        self.load_accounts_btn.config(state='disabled')
        self.status_bar.config(text="Loading accounts from QuickBooks...")
        self.accounts_status_label.config(text="Loading...", foreground='orange')

        # Launch background thread
        thread = threading.Thread(target=load_accounts_worker, args=(self,), daemon=True)
        thread.start()

    def _load_all(self):
        """Load all data from QuickBooks (customers, items, terms, classes, accounts)."""
        # Disable Load All button
        self.load_all_btn.config(state='disabled')
        self.status_bar.config(text="Loading all data from QuickBooks...")

        # Launch background thread
        thread = threading.Thread(target=load_all_worker, args=(self,), daemon=True)
        thread.start()

    def _load_customers(self):
        """Load customers from QuickBooks (wrapper - launches background thread)."""
        # Disable button
        self.load_customers_btn.config(state='disabled')
        self.status_bar.config(text="Loading customers from QuickBooks...")

        # Launch background thread
        thread = threading.Thread(target=load_customers_worker, args=(self,), daemon=True)
        thread.start()

    def _update_customer_combo(self):
        """Update all customer dropdowns (wrapper for customer_actions.update_customer_combo)."""
        update_customer_combo(self)

    def _update_accounts_combo(self):
        """Update deposit account dropdown in Monitor tab (wrapper for monitor_actions.update_accounts_combo)."""
        update_accounts_combo(self)

    def _on_state_change(self):
        """Called when store state changes."""
        state = self.store.get_state()
        status_text = (f"Customers: {len(state.customers)} | "
                      f"Invoices: {len(state.invoices)} | "
                      f"Sales Receipts: {len(state.sales_receipts)} | "
                      f"Statement Charges: {len(state.statement_charges)}")
        if state.monitoring_active:
            status_text += " | MONITORING ACTIVE"
        self.status_bar.config(text=status_text)

        # Update monitor tab transaction list
        from workers.monitor_worker import update_invoice_tree
        update_invoice_tree(self)

### MARK: Main

def main():
    """Main entry point."""
    root = tk.Tk()
    app = QBDTestToolApp(root)
    root.mainloop()


if __name__ == '__main__':
    # Required for multiprocessing with PyInstaller
    multiprocessing.freeze_support()
    main()
