"""
Customer action handlers for QuickBooks Desktop Test Tool.

Extracted from app.py to reduce monolithic file size.
"""

import threading
from tkinter import messagebox
from workers import create_customer_worker


def update_customer_combo(app):
    """
    Update all customer dropdowns with current customer list from state.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    state = app.store.get_state()
    customer_names = [f"{c['name']} ({c.get('email', 'no email')})" for c in state.customers]

    # Build ListID mapping (display_name -> list_id)
    app.customer_listid_map = {}
    for c in state.customers:
        display_name = f"{c['name']} ({c.get('email', 'no email')})"
        app.customer_listid_map[display_name] = c['list_id']

    # Update all customer comboboxes
    for combo in app.customer_combos:
        combo['values'] = customer_names
        if customer_names:
            combo.current(len(customer_names) - 1)

    # Update status label on Setup subtab
    count = len(state.customers)
    items_count = len(state.items)

    if count > 0:
        app.customers_status_label.config(
            text=f"{count} customer{'s' if count != 1 else ''} loaded",
            foreground='green'
        )
    else:
        app.customers_status_label.config(
            text="No customers loaded",
            foreground='red'
        )

    # Update summary - only show ready when BOTH customers and items are loaded
    if hasattr(app, 'setup_summary_label'):
        if count > 0 and items_count > 0:
            app.setup_summary_label.config(
                text=f"{count} customers, {items_count} items loaded - Ready to create transactions"
            )
        elif count > 0 or items_count > 0:
            app.setup_summary_label.config(
                text=f"{count} customers, {items_count} items loaded - Load both to begin"
            )
        else:
            app.setup_summary_label.config(
                text="Load customers and items from QuickBooks to begin"
            )


def create_customer(app):
    """
    Create a customer in QuickBooks (wrapper - launches background thread).

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    email = app.customer_email.get().strip()

    if not email:
        messagebox.showerror("Error", "Email is required!")
        return

    # Collect field enable states (True = random, False = manual)
    field_config = {
        'first_name': app.random_first_name.get(),
        'last_name': app.random_last_name.get(),
        'company': app.random_company.get(),
        'phone': app.random_phone.get(),
        'billing_address': app.random_billing_address.get(),
        'shipping_address': app.random_shipping_address.get()
    }

    # Collect manual values (only used when field_config[field] is False)
    manual_values = {
        'first_name': app.customer_first_name.get().strip() if not app.random_first_name.get() else None,
        'last_name': app.customer_last_name.get().strip() if not app.random_last_name.get() else None,
        'company': app.customer_company.get().strip() if not app.random_company.get() else None,
        'phone': app.customer_phone.get().strip() if not app.random_phone.get() else None,
    }

    # Collect billing address if not random
    if not app.random_billing_address.get():
        bill_addr1 = app.customer_bill_addr1.get().strip()
        bill_city = app.customer_bill_city.get().strip()
        bill_state = app.customer_bill_state.get().strip()
        bill_zip = app.customer_bill_zip.get().strip()

        # Only include billing address if at least one field has data
        if bill_addr1 or bill_city or bill_state or bill_zip:
            manual_values['billing_address'] = {
                'addr1': bill_addr1 or None,
                'city': bill_city or None,
                'state': bill_state or None,
                'postal_code': bill_zip or None
            }
        else:
            manual_values['billing_address'] = None
    else:
        manual_values['billing_address'] = None

    # Collect shipping address if not random
    if not app.random_shipping_address.get():
        ship_addr1 = app.customer_ship_addr1.get().strip()
        ship_city = app.customer_ship_city.get().strip()
        ship_state = app.customer_ship_state.get().strip()
        ship_zip = app.customer_ship_zip.get().strip()

        # Only include shipping address if at least one field has data
        if ship_addr1 or ship_city or ship_state or ship_zip:
            manual_values['shipping_address'] = {
                'addr1': ship_addr1 or None,
                'city': ship_city or None,
                'state': ship_state or None,
                'postal_code': ship_zip or None
            }
        else:
            manual_values['shipping_address'] = None
    else:
        manual_values['shipping_address'] = None

    # Collect job configuration
    try:
        num_jobs = int(app.num_jobs.get() or 0)
        num_subjobs = int(app.num_subjobs.get() or 0)
    except ValueError:
        messagebox.showerror("Error", "Invalid job count values!")
        return

    # Disable button and update status
    app.create_customer_btn.config(state='disabled')
    total_records = 1 + num_jobs + (num_jobs * num_subjobs)
    app.status_bar.config(text=f"Creating {total_records} record(s)...")

    # Launch background thread
    thread = threading.Thread(
        target=create_customer_worker,
        args=(app, email, field_config, manual_values, num_jobs, num_subjobs),
        daemon=True
    )
    thread.start()
