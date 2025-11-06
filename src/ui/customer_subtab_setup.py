"""
Customer subtab setup for QuickBooks Desktop Test Tool.

"""

import tkinter as tk
from tkinter import ttk
from actions.customer_actions import create_customer
from .ui_utils import create_scrollable_frame


def select_all_customer_fields(app):
    """
    Select all customer field checkboxes.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    app.random_first_name.set(True)
    app.random_last_name.set(True)
    app.random_company.set(True)
    app.random_phone.set(True)
    app.random_billing_address.set(True)
    app.random_shipping_address.set(True)


def clear_all_customer_fields(app):
    """
    Clear all customer field checkboxes.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    app.random_first_name.set(False)
    app.random_last_name.set(False)
    app.random_company.set(False)
    app.random_phone.set(False)
    app.random_billing_address.set(False)
    app.random_shipping_address.set(False)


def setup_customer_subtab(app):
    """
    Setup the Customer subtab for creating new customers.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    # Create scrollable frame
    canvas, scrollbar, container = create_scrollable_frame(app.customer_subtab)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Content container with padding
    content = ttk.Frame(container, padding=20)
    content.pack(fill='x')

    # Instructions
    ttk.Label(
        content,
        text="Create a new customer. Check 'Random' to generate data, uncheck to enter manually (leave blank if not needed).",
        wraplength=750
    ).pack(pady=(0, 15))

    # Form frame with grid layout
    form_frame = ttk.Frame(content)
    form_frame.pack(fill='x', pady=(0, 15))

    row = 0

    # Email (required, always enabled)
    ttk.Label(form_frame, text="Email:", font=('TkDefaultFont', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=5, padx=(0, 10))
    ttk.Label(form_frame, text="(required)").grid(row=row, column=1, sticky='w', pady=5)
    app.customer_email = ttk.Entry(form_frame, width=50)
    app.customer_email.grid(row=row, column=2, pady=5, padx=5, sticky='w')
    row += 1

    # Separator
    ttk.Separator(form_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky='ew', pady=10)
    row += 1

    # Jobs configuration
    ttk.Label(form_frame, text="Jobs:", font=('TkDefaultFont', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=5, padx=(0, 10))
    app.num_jobs = tk.Spinbox(form_frame, from_=0, to=10, width=10)
    app.num_jobs.delete(0, tk.END)
    app.num_jobs.insert(0, "0")
    app.num_jobs.grid(row=row, column=2, pady=5, padx=5, sticky='w')
    row += 1

    # Sub-jobs per job configuration
    ttk.Label(form_frame, text="Sub-jobs per Job:", font=('TkDefaultFont', 9)).grid(row=row, column=0, sticky='w', pady=5, padx=(0, 10))
    app.num_subjobs = tk.Spinbox(form_frame, from_=0, to=10, width=10)
    app.num_subjobs.delete(0, tk.END)
    app.num_subjobs.insert(0, "0")
    app.num_subjobs.grid(row=row, column=2, pady=5, padx=5, sticky='w')
    row += 1

    # Calculation display
    app.customer_calc_label = ttk.Label(form_frame, text="Will create: 1 customer", foreground='gray')
    app.customer_calc_label.grid(row=row, column=0, columnspan=3, sticky='w', pady=5, padx=(0, 10))
    row += 1

    # Bind spinboxes to update calculation
    def update_calculation(*args):
        try:
            jobs = int(app.num_jobs.get() or 0)
            subjobs = int(app.num_subjobs.get() or 0)
            total = 1 + jobs + (jobs * subjobs)

            parts = [f"1 customer"]
            if jobs > 0:
                parts.append(f"{jobs} job{'s' if jobs > 1 else ''}")
            if jobs > 0 and subjobs > 0:
                total_subjobs = jobs * subjobs
                parts.append(f"{total_subjobs} sub-job{'s' if total_subjobs > 1 else ''}")

            app.customer_calc_label.config(text=f"Will create: {' + '.join(parts)} = {total} total")
        except ValueError:
            app.customer_calc_label.config(text="Will create: 1 customer")

    app.num_jobs.config(command=update_calculation)
    app.num_subjobs.config(command=update_calculation)

    # Separator
    ttk.Separator(form_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky='ew', pady=10)
    row += 1

    # Helper function to create field row
    def create_field_row(label_text, var_name, entry_name, default_random=True):
        nonlocal row
        # Checkbox
        var = tk.BooleanVar(value=default_random)
        setattr(app, var_name, var)

        chk = ttk.Checkbutton(form_frame, text="Random", variable=var)
        chk.grid(row=row, column=1, sticky='w', pady=5)

        # Label
        ttk.Label(form_frame, text=label_text).grid(row=row, column=0, sticky='w', pady=5, padx=(0, 10))

        # Entry
        entry = ttk.Entry(form_frame, width=50)
        entry.grid(row=row, column=2, pady=5, padx=5, sticky='w')
        setattr(app, entry_name, entry)

        # Bind checkbox to enable/disable entry
        def toggle_entry(*args):
            if var.get():
                entry.config(state='disabled')
            else:
                entry.config(state='normal')

        var.trace_add('write', toggle_entry)
        toggle_entry()  # Set initial state

        row += 1

    # Simple fields
    create_field_row("First Name:", "random_first_name", "customer_first_name")
    create_field_row("Last Name:", "random_last_name", "customer_last_name")
    create_field_row("Company:", "random_company", "customer_company")
    create_field_row("Phone:", "random_phone", "customer_phone")

    # Billing Address section
    ttk.Separator(form_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky='ew', pady=10)
    row += 1

    # Billing address checkbox
    app.random_billing_address = tk.BooleanVar(value=True)
    chk = ttk.Checkbutton(form_frame, text="Random", variable=app.random_billing_address)
    chk.grid(row=row, column=1, sticky='w', pady=5)
    ttk.Label(form_frame, text="Billing Address:", font=('TkDefaultFont', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=5, padx=(0, 10))
    row += 1

    # Billing address fields
    app.customer_bill_addr1 = ttk.Entry(form_frame, width=50)
    ttk.Label(form_frame, text="  Street:").grid(row=row, column=0, sticky='w', pady=2, padx=(0, 10))
    app.customer_bill_addr1.grid(row=row, column=2, pady=2, padx=5, sticky='w')
    row += 1

    app.customer_bill_city = ttk.Entry(form_frame, width=50)
    ttk.Label(form_frame, text="  City:").grid(row=row, column=0, sticky='w', pady=2, padx=(0, 10))
    app.customer_bill_city.grid(row=row, column=2, pady=2, padx=5, sticky='w')
    row += 1

    app.customer_bill_state = ttk.Entry(form_frame, width=50)
    ttk.Label(form_frame, text="  State:").grid(row=row, column=0, sticky='w', pady=2, padx=(0, 10))
    app.customer_bill_state.grid(row=row, column=2, pady=2, padx=5, sticky='w')
    row += 1

    app.customer_bill_zip = ttk.Entry(form_frame, width=50)
    ttk.Label(form_frame, text="  Zip:").grid(row=row, column=0, sticky='w', pady=2, padx=(0, 10))
    app.customer_bill_zip.grid(row=row, column=2, pady=2, padx=5, sticky='w')
    row += 1

    # Bind billing address checkbox
    def toggle_billing(*args):
        state = 'disabled' if app.random_billing_address.get() else 'normal'
        app.customer_bill_addr1.config(state=state)
        app.customer_bill_city.config(state=state)
        app.customer_bill_state.config(state=state)
        app.customer_bill_zip.config(state=state)

    app.random_billing_address.trace_add('write', toggle_billing)
    toggle_billing()

    # Shipping Address section
    ttk.Separator(form_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky='ew', pady=10)
    row += 1

    # Shipping address checkbox
    app.random_shipping_address = tk.BooleanVar(value=True)
    chk = ttk.Checkbutton(form_frame, text="Random", variable=app.random_shipping_address)
    chk.grid(row=row, column=1, sticky='w', pady=5)
    ttk.Label(form_frame, text="Shipping Address:", font=('TkDefaultFont', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=5, padx=(0, 10))
    row += 1

    # Shipping address fields
    app.customer_ship_addr1 = ttk.Entry(form_frame, width=50)
    ttk.Label(form_frame, text="  Street:").grid(row=row, column=0, sticky='w', pady=2, padx=(0, 10))
    app.customer_ship_addr1.grid(row=row, column=2, pady=2, padx=5, sticky='w')
    row += 1

    app.customer_ship_city = ttk.Entry(form_frame, width=50)
    ttk.Label(form_frame, text="  City:").grid(row=row, column=0, sticky='w', pady=2, padx=(0, 10))
    app.customer_ship_city.grid(row=row, column=2, pady=2, padx=5, sticky='w')
    row += 1

    app.customer_ship_state = ttk.Entry(form_frame, width=50)
    ttk.Label(form_frame, text="  State:").grid(row=row, column=0, sticky='w', pady=2, padx=(0, 10))
    app.customer_ship_state.grid(row=row, column=2, pady=2, padx=5, sticky='w')
    row += 1

    app.customer_ship_zip = ttk.Entry(form_frame, width=50)
    ttk.Label(form_frame, text="  Zip:").grid(row=row, column=0, sticky='w', pady=2, padx=(0, 10))
    app.customer_ship_zip.grid(row=row, column=2, pady=2, padx=5, sticky='w')
    row += 1

    # Bind shipping address checkbox
    def toggle_shipping(*args):
        state = 'disabled' if app.random_shipping_address.get() else 'normal'
        app.customer_ship_addr1.config(state=state)
        app.customer_ship_city.config(state=state)
        app.customer_ship_state.config(state=state)
        app.customer_ship_zip.config(state=state)

    app.random_shipping_address.trace_add('write', toggle_shipping)
    toggle_shipping()

    # Buttons
    button_frame = ttk.Frame(content)
    button_frame.pack(pady=10)

    ttk.Button(button_frame, text="Select All Random", command=lambda: select_all_customer_fields(app)).pack(side='left', padx=5)
    ttk.Button(button_frame, text="Clear All Random", command=lambda: clear_all_customer_fields(app)).pack(side='left', padx=5)

    # Create button
    app.create_customer_btn = ttk.Button(
        content,
        text="Create New Customer",
        command=lambda: create_customer(app)
    )
    app.create_customer_btn.pack(pady=10)
