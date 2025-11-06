"""
Sales receipt actions for QuickBooks Desktop Test Tool.

Handles sales receipt creation and query actions.
"""

import threading
from tkinter import messagebox
from workers import create_sales_receipt_worker, query_sales_receipt_worker


def create_sales_receipt(app):
    """
    Create sales receipt(s) in batch.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    state = app.store.get_state()

    # Validate customer selection
    if not app.sr_customer_combo.get():
        messagebox.showerror("Error", "Please select a customer first!")
        return

    if not state.items:
        messagebox.showerror("Error", "Please load items from QB first!")
        return

    # Get customer by ListID (not index) to avoid mismatch with nested jobs
    selected_display_name = app.sr_customer_combo.get()
    customer_list_id = app.customer_listid_map.get(selected_display_name)
    if not customer_list_id:
        messagebox.showerror("Error", "Selected customer not found. Please reload customers.")
        return

    # Find customer by ListID
    customer = next((c for c in state.customers if c['list_id'] == customer_list_id), None)
    if not customer:
        messagebox.showerror("Error", "Customer data not found. Please reload customers.")
        return

    # Get and validate parameters
    try:
        num_receipts = int(app.num_sales_receipts.get())
        line_items_min = int(app.num_sr_lines_min.get())
        line_items_max = int(app.num_sr_lines_max.get())
        amount_min = float(app.sr_amount_min.get())
        amount_max = float(app.sr_amount_max.get())
        date_range = app.sr_date_range.get()

        if line_items_min > line_items_max:
            raise ValueError("Line items min cannot be greater than max")
        if amount_min > amount_max:
            raise ValueError("Amount min cannot be greater than max")
        if num_receipts < 1:
            raise ValueError("Number of sales receipts must be at least 1")

    except ValueError as e:
        messagebox.showerror("Error", f"Invalid input: {str(e)}")
        return

    # Disable button and update status
    app.create_sales_receipt_btn.config(state='disabled')
    app.status_bar.config(text="Creating sales receipts...")

    # Start worker thread
    thread = threading.Thread(
        target=create_sales_receipt_worker,
        args=(app, customer, num_receipts, line_items_min, line_items_max,
              amount_min, amount_max, date_range, state.items),
        daemon=True
    )
    thread.start()


def query_sales_receipt(app):
    """
    Query a sales receipt by TxnID to debug visibility issue.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    txn_id = app.query_txn_id.get().strip()

    if not txn_id:
        messagebox.showerror("Error", "Please enter a TxnID to query!")
        return

    # Disable button and update status
    app.query_sr_btn.config(state='disabled')
    app.status_bar.config(text="Querying sales receipt...")

    # Start worker thread
    thread = threading.Thread(
        target=query_sales_receipt_worker,
        args=(app, txn_id),
        daemon=True
    )
    thread.start()
