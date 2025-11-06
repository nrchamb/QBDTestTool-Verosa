"""
Invoice actions for QuickBooks Desktop Test Tool.

Handles invoice creation and management actions.
"""

import threading
from tkinter import messagebox
from workers import create_invoice_worker


def create_invoice(app):
    """
    Create invoices in QuickBooks (batch wrapper - launches background thread).

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    if not app.customer_combo.get():
        messagebox.showerror("Error", "Please select a customer!")
        return

    try:
        # Get selected customer and parameters
        state = app.store.get_state()

        # Check if items are loaded
        if not state.items:
            messagebox.showerror("Error", "Please load items from QuickBooks first!\n\nClick 'Load Items from QB' button.")
            return

        # Get customer by ListID (not index) to avoid mismatch with nested jobs
        selected_display_name = app.customer_combo.get()
        customer_list_id = app.customer_listid_map.get(selected_display_name)
        if not customer_list_id:
            messagebox.showerror("Error", "Selected customer not found. Please reload customers.")
            return

        # Find customer by ListID
        customer = next((c for c in state.customers if c['list_id'] == customer_list_id), None)
        if not customer:
            messagebox.showerror("Error", "Customer data not found. Please reload customers.")
            return

        # Get batch parameters
        num_invoices = int(app.num_invoices.get())
        line_items_min = int(app.num_lines_min.get())
        line_items_max = int(app.num_lines_max.get())
        amount_min = float(app.amount_min.get())
        amount_max = float(app.amount_max.get())
        date_range = app.invoice_date_range.get()

        # Get optional fields
        po_prefix = app.invoice_po_prefix.get().strip()
        if not po_prefix:
            po_prefix = None  # Don't use empty string

        # Get selected terms and look up list_id
        terms_ref = None
        selected_terms = app.invoice_terms_combo.get()
        if selected_terms and selected_terms != '(None)':
            # Find the terms in state by name
            for term in state.terms:
                if term['name'] == selected_terms:
                    terms_ref = term['list_id']
                    break

        # Get selected class and look up list_id
        class_ref = None
        selected_class = app.invoice_class_combo.get()
        if selected_class and selected_class != '(None)':
            # Find the class in state by full_name
            for cls in state.classes:
                if cls['full_name'] == selected_class:
                    class_ref = cls['list_id']
                    break

        # Validate ranges
        if line_items_max < line_items_min:
            messagebox.showerror("Error", "Line items max must be >= min")
            return
        if amount_max < amount_min:
            messagebox.showerror("Error", "Amount max must be >= min")
            return

        # Disable button and update status
        app.create_invoice_btn.config(state='disabled')
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
