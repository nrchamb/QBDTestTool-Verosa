"""
Invoice subtab setup for QuickBooks Desktop Test Tool.


DEFUNCT: MARKED FOR DELETION
"""

from tkinter import ttk
from actions.invoice_actions import create_invoice
from .ui_utils import create_scrollable_frame


def setup_invoice_subtab(app):
    """
    Setup the Invoice subtab for batch invoice creation.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    # Create scrollable frame
    canvas, scrollbar, container = create_scrollable_frame(app.invoice_subtab)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Content container with padding
    content = ttk.Frame(container, padding=20)
    content.pack(fill='x')

    # Instructions
    ttk.Label(
        content,
        text="Create batch invoices with randomized parameters",
        font=('TkDefaultFont', 10, 'bold')
    ).pack(pady=(0, 15))

    # Form
    form_frame = ttk.Frame(content)
    form_frame.pack(fill='x')

    row = 0

    # Customer selector
    ttk.Label(form_frame, text="Select Customer:").grid(row=row, column=0, sticky='w', pady=5, padx=5)
    app.customer_combo = ttk.Combobox(form_frame, width=50, state='readonly')
    app.customer_combo.grid(row=row, column=1, pady=5, padx=5, sticky='w')
    app.customer_combos.append(app.customer_combo)
    row += 1

    # Number of invoices
    ttk.Label(form_frame, text="Number of Invoices:").grid(row=row, column=0, sticky='w', pady=5, padx=5)
    app.num_invoices = ttk.Spinbox(form_frame, from_=1, to=100, width=10)
    app.num_invoices.set(1)
    app.num_invoices.grid(row=row, column=1, sticky='w', pady=5, padx=5)
    row += 1

    # Line items range
    ttk.Label(form_frame, text="Line Items Range:").grid(row=row, column=0, sticky='w', pady=5, padx=5)
    line_items_frame = ttk.Frame(form_frame)
    line_items_frame.grid(row=row, column=1, sticky='w', pady=5, padx=5)
    app.num_lines_min = ttk.Spinbox(line_items_frame, from_=1, to=20, width=5)
    app.num_lines_min.set(1)
    app.num_lines_min.pack(side='left')
    ttk.Label(line_items_frame, text=" to ").pack(side='left', padx=5)
    app.num_lines_max = ttk.Spinbox(line_items_frame, from_=1, to=20, width=5)
    app.num_lines_max.set(5)
    app.num_lines_max.pack(side='left')
    row += 1

    # Amount range
    ttk.Label(form_frame, text="Amount Range ($):").grid(row=row, column=0, sticky='w', pady=5, padx=5)
    amount_frame = ttk.Frame(form_frame)
    amount_frame.grid(row=row, column=1, sticky='w', pady=5, padx=5)
    app.amount_min = ttk.Entry(amount_frame, width=10)
    app.amount_min.insert(0, "100")
    app.amount_min.pack(side='left')
    ttk.Label(amount_frame, text=" to ").pack(side='left', padx=5)
    app.amount_max = ttk.Entry(amount_frame, width=10)
    app.amount_max.insert(0, "5000")
    app.amount_max.pack(side='left')
    row += 1

    # Date range
    ttk.Label(form_frame, text="Transaction Date Range:").grid(row=row, column=0, sticky='w', pady=5, padx=5)
    app.invoice_date_range = ttk.Combobox(form_frame, width=15, state='readonly')
    app.invoice_date_range['values'] = ('Today Only', 'Last 7 Days', 'Last 30 Days')
    app.invoice_date_range.current(0)
    app.invoice_date_range.grid(row=row, column=1, sticky='w', pady=5, padx=5)
    row += 1

    # PO Number Prefix (optional)
    ttk.Label(form_frame, text="PO Number Prefix:").grid(row=row, column=0, sticky='w', pady=5, padx=5)
    app.invoice_po_prefix = ttk.Entry(form_frame, width=15)
    app.invoice_po_prefix.insert(0, "PO-")
    app.invoice_po_prefix.grid(row=row, column=1, sticky='w', pady=5, padx=5)
    row += 1

    # Terms (optional)
    ttk.Label(form_frame, text="Terms (optional):").grid(row=row, column=0, sticky='w', pady=5, padx=5)
    app.invoice_terms_combo = ttk.Combobox(form_frame, width=30, state='readonly')
    app.invoice_terms_combo['values'] = ['(None)']
    app.invoice_terms_combo.current(0)
    app.invoice_terms_combo.grid(row=row, column=1, sticky='w', pady=5, padx=5)
    row += 1

    # Class (optional)
    ttk.Label(form_frame, text="Class (optional):").grid(row=row, column=0, sticky='w', pady=5, padx=5)
    app.invoice_class_combo = ttk.Combobox(form_frame, width=30, state='readonly')
    app.invoice_class_combo['values'] = ['(None)']
    app.invoice_class_combo.current(0)
    app.invoice_class_combo.grid(row=row, column=1, sticky='w', pady=5, padx=5)
    row += 1

    # Create button
    app.create_invoice_btn = ttk.Button(
        content,
        text="Create Invoices (Batch)",
        command=lambda: create_invoice(app)
    )
    app.create_invoice_btn.pack(pady=15)
