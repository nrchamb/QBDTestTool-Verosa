"""
Unified Transaction subtab for QuickBooks Desktop Test Tool.

Consolidates Invoice, Sales Receipt, and Statement Charge creation into a single interface.
"""

import tkinter as tk
from tkinter import ttk
from actions.transaction_actions import create_transaction
from .ui_utils import create_scrollable_frame


def setup_transaction_subtab(app):
    """
    Setup the unified Transaction subtab for batch creation of invoices, sales receipts, and charges.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    # Create scrollable frame
    canvas, scrollbar, container = create_scrollable_frame(app.transaction_subtab)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Content container with padding
    content = ttk.Frame(container, padding=20)
    content.pack(fill='x')

    # Instructions
    ttk.Label(
        content,
        text="Create batch transactions with randomized parameters",
        font=('TkDefaultFont', 10, 'bold')
    ).pack(pady=(0, 15))

    # Transaction Type Selector
    type_frame = ttk.LabelFrame(content, text="Transaction Type", padding=10)
    type_frame.pack(fill='x', pady=(0, 15))

    app.transaction_type = tk.StringVar(value="Invoice")

    def on_type_change():
        """Update field visibility based on transaction type."""
        txn_type = app.transaction_type.get()

        # Line items: Show for Invoice and Sales Receipt, hide for Charge
        if txn_type in ["Invoice", "SalesReceipt"]:
            line_items_label.grid()
            line_items_frame.grid()
        else:
            line_items_label.grid_remove()
            line_items_frame.grid_remove()

        # Invoice-specific fields: Show only for Invoice
        if txn_type == "Invoice":
            po_label.grid()
            app.txn_po_prefix.grid()
            terms_label.grid()
            app.txn_terms_combo.grid()
            class_label.grid()
            app.txn_class_combo.grid()
        else:
            po_label.grid_remove()
            app.txn_po_prefix.grid_remove()
            terms_label.grid_remove()
            app.txn_terms_combo.grid_remove()
            class_label.grid_remove()
            app.txn_class_combo.grid_remove()

        # Update button text
        if txn_type == "Invoice":
            app.create_transaction_btn.config(text="Create Invoices (Batch)")
        elif txn_type == "SalesReceipt":
            app.create_transaction_btn.config(text="Create Sales Receipts (Batch)")
        else:
            app.create_transaction_btn.config(text="Create Statement Charges (Batch)")

    # Create three radio buttons for transaction type
    ttk.Radiobutton(
        type_frame,
        text="Invoice",
        variable=app.transaction_type,
        value="Invoice",
        command=on_type_change
    ).pack(side='left', padx=10)

    ttk.Radiobutton(
        type_frame,
        text="Sales Receipt",
        variable=app.transaction_type,
        value="SalesReceipt",
        command=on_type_change
    ).pack(side='left', padx=10)

    ttk.Radiobutton(
        type_frame,
        text="Statement Charge",
        variable=app.transaction_type,
        value="Charge",
        command=on_type_change
    ).pack(side='left', padx=10)

    # Form
    form_frame = ttk.Frame(content)
    form_frame.pack(fill='x')

    row = 0

    # Customer selector
    ttk.Label(form_frame, text="Select Customer:").grid(row=row, column=0, sticky='w', pady=5, padx=5)
    app.txn_customer_combo = ttk.Combobox(form_frame, width=50, state='readonly')
    app.txn_customer_combo.grid(row=row, column=1, pady=5, padx=5, sticky='w')
    app.customer_combos.append(app.txn_customer_combo)
    row += 1

    # Number of transactions
    ttk.Label(form_frame, text="Number of Transactions:").grid(row=row, column=0, sticky='w', pady=5, padx=5)
    app.txn_count = ttk.Spinbox(form_frame, from_=1, to=100, width=10)
    app.txn_count.set(1)
    app.txn_count.grid(row=row, column=1, sticky='w', pady=5, padx=5)
    row += 1

    # Line items range (conditional - hidden for Statement Charge)
    line_items_label = ttk.Label(form_frame, text="Line Items Range:")
    line_items_label.grid(row=row, column=0, sticky='w', pady=5, padx=5)
    line_items_frame = ttk.Frame(form_frame)
    line_items_frame.grid(row=row, column=1, sticky='w', pady=5, padx=5)
    app.txn_lines_min = ttk.Spinbox(line_items_frame, from_=1, to=20, width=5)
    app.txn_lines_min.set(1)
    app.txn_lines_min.pack(side='left')
    ttk.Label(line_items_frame, text=" to ").pack(side='left', padx=5)
    app.txn_lines_max = ttk.Spinbox(line_items_frame, from_=1, to=20, width=5)
    app.txn_lines_max.set(5)
    app.txn_lines_max.pack(side='left')
    row += 1

    # Amount range
    ttk.Label(form_frame, text="Amount Range ($):").grid(row=row, column=0, sticky='w', pady=5, padx=5)
    amount_frame = ttk.Frame(form_frame)
    amount_frame.grid(row=row, column=1, sticky='w', pady=5, padx=5)
    app.txn_amount_min = ttk.Entry(amount_frame, width=10)
    app.txn_amount_min.insert(0, "100")
    app.txn_amount_min.pack(side='left')
    ttk.Label(amount_frame, text=" to ").pack(side='left', padx=5)
    app.txn_amount_max = ttk.Entry(amount_frame, width=10)
    app.txn_amount_max.insert(0, "5000")
    app.txn_amount_max.pack(side='left')
    row += 1

    # Date range
    ttk.Label(form_frame, text="Transaction Date Range:").grid(row=row, column=0, sticky='w', pady=5, padx=5)
    app.txn_date_range = ttk.Combobox(form_frame, width=15, state='readonly')
    app.txn_date_range['values'] = ('Today Only', 'Last 7 Days', 'Last 30 Days')
    app.txn_date_range.current(0)
    app.txn_date_range.grid(row=row, column=1, sticky='w', pady=5, padx=5)
    row += 1

    # PO Number Prefix (Invoice only - hidden for Sales Receipt and Statement Charge)
    po_label = ttk.Label(form_frame, text="PO Number Prefix:")
    po_label.grid(row=row, column=0, sticky='w', pady=5, padx=5)
    app.txn_po_prefix = ttk.Entry(form_frame, width=15)
    app.txn_po_prefix.insert(0, "PO-")
    app.txn_po_prefix.grid(row=row, column=1, sticky='w', pady=5, padx=5)
    row += 1

    # Terms (Invoice only - hidden for Sales Receipt and Statement Charge)
    terms_label = ttk.Label(form_frame, text="Terms (optional):")
    terms_label.grid(row=row, column=0, sticky='w', pady=5, padx=5)
    app.txn_terms_combo = ttk.Combobox(form_frame, width=30, state='readonly')
    app.txn_terms_combo['values'] = ['(None)']
    app.txn_terms_combo.current(0)
    app.txn_terms_combo.grid(row=row, column=1, sticky='w', pady=5, padx=5)
    row += 1

    # Class (Invoice only - hidden for Sales Receipt and Statement Charge)
    class_label = ttk.Label(form_frame, text="Class (optional):")
    class_label.grid(row=row, column=0, sticky='w', pady=5, padx=5)
    app.txn_class_combo = ttk.Combobox(form_frame, width=30, state='readonly')
    app.txn_class_combo['values'] = ['(None)']
    app.txn_class_combo.current(0)
    app.txn_class_combo.grid(row=row, column=1, sticky='w', pady=5, padx=5)
    row += 1

    # Create button
    app.create_transaction_btn = ttk.Button(
        content,
        text="Create Invoices (Batch)",
        command=lambda: create_transaction(app)
    )
    app.create_transaction_btn.pack(pady=15)

    # Initialize field visibility based on default transaction type
    on_type_change()
