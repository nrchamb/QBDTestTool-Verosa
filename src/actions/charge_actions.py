"""
Statement charge actions for QuickBooks Desktop Test Tool.

Handles statement charge creation actions.
"""

import threading
from tkinter import messagebox
from workers import create_charge_worker


def create_charge(app):
    """
    Create statement charge(s) in batch.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    state = app.store.get_state()

    # Validate customer selection
    if not app.charge_customer_combo.get():
        messagebox.showerror("Error", "Please select a customer first!")
        return

    if not state.items:
        messagebox.showerror("Error", "Please load items from QB first!")
        return

    # Get customer by ListID (not index) to avoid mismatch with nested jobs
    selected_display_name = app.charge_customer_combo.get()
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
        num_charges = int(app.num_charges.get())
        amount_min = float(app.charge_amount_min.get())
        amount_max = float(app.charge_amount_max.get())
        date_range = app.charge_date_range.get()

        if amount_min > amount_max:
            raise ValueError("Amount min cannot be greater than max")
        if num_charges < 1:
            raise ValueError("Number of charges must be at least 1")

    except ValueError as e:
        messagebox.showerror("Error", f"Invalid input: {str(e)}")
        return

    # Disable button and update status
    app.create_charge_btn.config(state='disabled')
    app.status_bar.config(text="Creating statement charges...")

    # Start worker thread
    thread = threading.Thread(
        target=create_charge_worker,
        args=(app, customer, num_charges, amount_min, amount_max, date_range, state.items),
        daemon=True
    )
    thread.start()
