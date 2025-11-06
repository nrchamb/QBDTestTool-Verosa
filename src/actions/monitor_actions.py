"""
Monitor actions for QuickBooks Desktop Test Tool.

Handles monitor control actions (start, stop, settings).
"""

import tkinter as tk
from tkinter import messagebox
import threading
from store import set_monitoring, set_expected_deposit_account


def start_monitoring(app):
    """
    Start monitoring transactions.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    state = app.store.get_state()

    total_transactions = len(state.invoices) + len(state.sales_receipts) + len(state.statement_charges)
    if total_transactions == 0:
        messagebox.showwarning("Warning", "No transactions to monitor! Create some invoices, sales receipts, or statement charges first.")
        return

    app.monitoring_stop_flag = False
    app.store.dispatch(set_monitoring(True))

    app.start_monitor_btn.config(state='disabled')
    app.stop_monitor_btn.config(state='normal')

    app._log_monitor(f"Starting monitoring for {len(state.invoices)} invoice(s), {len(state.sales_receipts)} sales receipt(s), {len(state.statement_charges)} charge(s)...")

    # Start monitoring thread
    from workers.monitor_worker import monitor_loop_worker
    app.monitor_thread = threading.Thread(target=monitor_loop_worker, args=(app,), daemon=True)
    app.monitor_thread.start()


def stop_monitoring(app):
    """
    Stop monitoring invoices.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    app.monitoring_stop_flag = True
    app.store.dispatch(set_monitoring(False))

    app.start_monitor_btn.config(state='normal')
    app.stop_monitor_btn.config(state='disabled')

    app._log_monitor("Monitoring stopped.")


def set_expected_deposit_account(app):
    """
    Set the expected deposit account for validation.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    from store import set_expected_deposit_account as set_account_action

    account_name = app.expected_deposit_account_combo.get().strip()
    if account_name:
        app.store.dispatch(set_account_action(account_name))
        messagebox.showinfo("Success", f"Expected deposit account set to: {account_name}")
    else:
        app.store.dispatch(set_account_action(None))
        messagebox.showinfo("Info", "Expected deposit account cleared")


def clear_search(app):
    """
    Clear all search fields.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    app.search_text.delete(0, tk.END)
    app.search_txn_id.delete(0, tk.END)
    app.search_date_from.delete(0, tk.END)
    app.search_date_to.delete(0, tk.END)
    app.search_amount_min.delete(0, tk.END)
    app.search_amount_max.delete(0, tk.END)
    app.search_txn_type.set('All')


def update_accounts_combo(app):
    """
    Update deposit account dropdown in Monitor tab.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    state = app.store.get_state()
    account_names = [acc['full_name'] for acc in state.accounts]

    # Update the deposit account combobox
    if hasattr(app, 'expected_deposit_account_combo'):
        app.expected_deposit_account_combo['values'] = account_names
