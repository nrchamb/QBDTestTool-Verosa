"""
Unified transaction actions for QuickBooks Desktop Test Tool.

Handles invoice, sales receipt, and statement charge creation through a unified interface.
"""

import threading
from tkinter import messagebox
from workers import create_invoice_worker, create_sales_receipt_worker, create_charge_worker


def create_transaction(app):
    """
    Create transactions in QuickBooks based on selected transaction type.
    Dispatches to appropriate worker based on app.transaction_type.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    # Get transaction type
    txn_type = app.transaction_type.get()

    # Validate customer selection
    if not app.txn_customer_combo.get():
        messagebox.showerror("Error", "Please select a customer!")
        return

    # Get state and validate items are loaded
    state = app.store.get_state()
    if not state.items:
        messagebox.showerror("Error", "Please load items from QuickBooks first!\n\nClick 'Load Items from QB' button.")
        return

    # Get customer by ListID (not index) to avoid mismatch with nested jobs
    selected_display_name = app.txn_customer_combo.get()
    customer_list_id = app.customer_listid_map.get(selected_display_name)
    if not customer_list_id:
        messagebox.showerror("Error", "Selected customer not found. Please reload customers.")
        return

    # Find customer by ListID
    customer = next((c for c in state.customers if c['list_id'] == customer_list_id), None)
    if not customer:
        messagebox.showerror("Error", "Customer data not found. Please reload customers.")
        return

    # Get common parameters
    try:
        num_transactions = int(app.txn_count.get())
        amount_min = float(app.txn_amount_min.get())
        amount_max = float(app.txn_amount_max.get())
        date_range = app.txn_date_range.get()

        # Validate common parameters
        if amount_max < amount_min:
            messagebox.showerror("Error", "Amount max must be >= min")
            return
        if num_transactions < 1:
            messagebox.showerror("Error", "Number of transactions must be at least 1")
            return

    except ValueError as e:
        messagebox.showerror("Error", f"Invalid input: {str(e)}")
        return

    # Dispatch based on transaction type
    if txn_type == "Invoice":
        _create_invoices(app, customer, num_transactions, amount_min, amount_max, date_range, state)
    elif txn_type == "SalesReceipt":
        _create_sales_receipts(app, customer, num_transactions, amount_min, amount_max, date_range, state)
    elif txn_type == "Charge":
        _create_charges(app, customer, num_transactions, amount_min, amount_max, date_range, state)
    else:
        messagebox.showerror("Error", f"Unknown transaction type: {txn_type}")


def _create_invoices(app, customer, num_invoices, amount_min, amount_max, date_range, state):
    """
    Create invoices using the invoice worker.

    Args:
        app: Reference to the main QBDTestToolApp instance
        customer: Customer dict
        num_invoices: Number of invoices to create
        amount_min: Minimum amount
        amount_max: Maximum amount
        date_range: Date range string
        state: Application state
    """
    try:
        # Get invoice-specific parameters
        line_items_min = int(app.txn_lines_min.get())
        line_items_max = int(app.txn_lines_max.get())

        # Validate line items range
        if line_items_max < line_items_min:
            messagebox.showerror("Error", "Line items max must be >= min")
            return

        # Get optional fields
        po_prefix = app.txn_po_prefix.get().strip()
        if not po_prefix:
            po_prefix = None  # Don't use empty string

        # Get selected terms and look up list_id
        terms_ref = None
        selected_terms = app.txn_terms_combo.get()
        if selected_terms and selected_terms != '(None)':
            # Find the terms in state by name
            for term in state.terms:
                if term['name'] == selected_terms:
                    terms_ref = term['list_id']
                    break

        # Get selected class and look up list_id
        class_ref = None
        selected_class = app.txn_class_combo.get()
        if selected_class and selected_class != '(None)':
            # Find the class in state by full_name
            for cls in state.classes:
                if cls['full_name'] == selected_class:
                    class_ref = cls['list_id']
                    break

        # Disable button and update status
        app.create_transaction_btn.config(state='disabled')
        plural = "s" if num_invoices > 1 else ""
        app.status_bar.config(text=f"Creating {num_invoices} invoice{plural}...")

        # Launch background thread
        thread = threading.Thread(
            target=create_invoice_worker,
            args=(app, customer, num_invoices, line_items_min, line_items_max,
                  amount_min, amount_max, date_range, state.items,
                  po_prefix, terms_ref, class_ref),
            daemon=True
        )
        thread.start()

    except ValueError as e:
        messagebox.showerror("Error", f"Invalid input: {str(e)}")


def _create_sales_receipts(app, customer, num_receipts, amount_min, amount_max, date_range, state):
    """
    Create sales receipts using the sales receipt worker.

    Args:
        app: Reference to the main QBDTestToolApp instance
        customer: Customer dict
        num_receipts: Number of sales receipts to create
        amount_min: Minimum amount
        amount_max: Maximum amount
        date_range: Date range string
        state: Application state
    """
    try:
        # Get sales receipt-specific parameters
        line_items_min = int(app.txn_lines_min.get())
        line_items_max = int(app.txn_lines_max.get())

        # Validate line items range
        if line_items_min > line_items_max:
            messagebox.showerror("Error", "Line items min cannot be greater than max")
            return

        # Disable button and update status
        app.create_transaction_btn.config(state='disabled')
        plural = "s" if num_receipts > 1 else ""
        app.status_bar.config(text=f"Creating {num_receipts} sales receipt{plural}...")

        # Start worker thread
        thread = threading.Thread(
            target=create_sales_receipt_worker,
            args=(app, customer, num_receipts, line_items_min, line_items_max,
                  amount_min, amount_max, date_range, state.items),
            daemon=True
        )
        thread.start()

    except ValueError as e:
        messagebox.showerror("Error", f"Invalid input: {str(e)}")


def _create_charges(app, customer, num_charges, amount_min, amount_max, date_range, state):
    """
    Create statement charges using the charge worker.

    Args:
        app: Reference to the main QBDTestToolApp instance
        customer: Customer dict
        num_charges: Number of charges to create
        amount_min: Minimum amount
        amount_max: Maximum amount
        date_range: Date range string
        state: Application state
    """
    # Disable button and update status
    app.create_transaction_btn.config(state='disabled')
    plural = "s" if num_charges > 1 else ""
    app.status_bar.config(text=f"Creating {num_charges} statement charge{plural}...")

    # Start worker thread
    thread = threading.Thread(
        target=create_charge_worker,
        args=(app, customer, num_charges, amount_min, amount_max, date_range, state.items),
        daemon=True
    )
    thread.start()
