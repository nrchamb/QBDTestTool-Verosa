"""
Statement Charge subtab setup for QuickBooks Desktop Test Tool.


DEFUNCT: MARKED FOR DELETION
"""

from tkinter import ttk
from actions.charge_actions import create_charge
from .ui_utils import create_scrollable_frame


def setup_charge_subtab(app):
    """
    Setup the Statement Charge subtab for batch charge creation.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    # Create scrollable frame
    canvas, scrollbar, container = create_scrollable_frame(app.charge_subtab)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Content container with padding
    content = ttk.Frame(container, padding=20)
    content.pack(fill='x')

    # Instructions
    ttk.Label(
        content,
        text="Create batch statement charges with randomized parameters",
        font=('TkDefaultFont', 10, 'bold')
    ).pack(pady=(0, 15))

    # Form
    form_frame = ttk.Frame(content)
    form_frame.pack(fill='x')

    row = 0

    # Customer selector
    ttk.Label(form_frame, text="Select Customer:").grid(row=row, column=0, sticky='w', pady=5, padx=5)
    app.charge_customer_combo = ttk.Combobox(form_frame, width=50, state='readonly')
    app.charge_customer_combo.grid(row=row, column=1, pady=5, padx=5, sticky='w')
    app.customer_combos.append(app.charge_customer_combo)
    row += 1

    # Number of charges
    ttk.Label(form_frame, text="Number of Charges:").grid(row=row, column=0, sticky='w', pady=5, padx=5)
    app.num_charges = ttk.Spinbox(form_frame, from_=1, to=100, width=10)
    app.num_charges.set(1)
    app.num_charges.grid(row=row, column=1, sticky='w', pady=5, padx=5)
    row += 1

    # Amount range
    ttk.Label(form_frame, text="Amount Range ($):").grid(row=row, column=0, sticky='w', pady=5, padx=5)
    amount_frame = ttk.Frame(form_frame)
    amount_frame.grid(row=row, column=1, sticky='w', pady=5, padx=5)
    app.charge_amount_min = ttk.Entry(amount_frame, width=10)
    app.charge_amount_min.insert(0, "50")
    app.charge_amount_min.pack(side='left')
    ttk.Label(amount_frame, text=" to ").pack(side='left', padx=5)
    app.charge_amount_max = ttk.Entry(amount_frame, width=10)
    app.charge_amount_max.insert(0, "500")
    app.charge_amount_max.pack(side='left')
    row += 1

    # Date range
    ttk.Label(form_frame, text="Transaction Date Range:").grid(row=row, column=0, sticky='w', pady=5, padx=5)
    app.charge_date_range = ttk.Combobox(form_frame, width=15, state='readonly')
    app.charge_date_range['values'] = ('Today Only', 'Last 7 Days', 'Last 30 Days')
    app.charge_date_range.current(0)
    app.charge_date_range.grid(row=row, column=1, sticky='w', pady=5, padx=5)
    row += 1

    # Create button
    app.create_charge_btn = ttk.Button(
        content,
        text="Create Statement Charges (Batch)",
        command=lambda: create_charge(app)
    )
    app.create_charge_btn.pack(pady=15)
