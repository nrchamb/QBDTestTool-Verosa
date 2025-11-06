"""
Sales Receipt subtab setup for QuickBooks Desktop Test Tool.


DEFUNCT: MARKED FOR DELETION
"""

from tkinter import ttk
from actions.sales_receipt_actions import create_sales_receipt, query_sales_receipt
from .ui_utils import create_scrollable_frame


def setup_sales_receipt_subtab(app):
    """
    Setup the Sales Receipt subtab for batch sales receipt creation.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    # Create scrollable frame
    canvas, scrollbar, container = create_scrollable_frame(app.sales_receipt_subtab)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Content container with padding
    content = ttk.Frame(container, padding=20)
    content.pack(fill='x')

    # Instructions
    ttk.Label(
        content,
        text="Create batch sales receipts with randomized parameters",
        font=('TkDefaultFont', 10, 'bold')
    ).pack(pady=(0, 15))

    # Form
    form_frame = ttk.Frame(content)
    form_frame.pack(fill='x')

    row = 0

    # Customer selector
    ttk.Label(form_frame, text="Select Customer:").grid(row=row, column=0, sticky='w', pady=5, padx=5)
    app.sr_customer_combo = ttk.Combobox(form_frame, width=50, state='readonly')
    app.sr_customer_combo.grid(row=row, column=1, pady=5, padx=5, sticky='w')
    app.customer_combos.append(app.sr_customer_combo)
    row += 1

    # Number of sales receipts
    ttk.Label(form_frame, text="Number of Sales Receipts:").grid(row=row, column=0, sticky='w', pady=5, padx=5)
    app.num_sales_receipts = ttk.Spinbox(form_frame, from_=1, to=100, width=10)
    app.num_sales_receipts.set(1)
    app.num_sales_receipts.grid(row=row, column=1, sticky='w', pady=5, padx=5)
    row += 1

    # Line items range
    ttk.Label(form_frame, text="Line Items Range:").grid(row=row, column=0, sticky='w', pady=5, padx=5)
    line_items_frame = ttk.Frame(form_frame)
    line_items_frame.grid(row=row, column=1, sticky='w', pady=5, padx=5)
    app.num_sr_lines_min = ttk.Spinbox(line_items_frame, from_=1, to=20, width=5)
    app.num_sr_lines_min.set(1)
    app.num_sr_lines_min.pack(side='left')
    ttk.Label(line_items_frame, text=" to ").pack(side='left', padx=5)
    app.num_sr_lines_max = ttk.Spinbox(line_items_frame, from_=1, to=20, width=5)
    app.num_sr_lines_max.set(3)
    app.num_sr_lines_max.pack(side='left')
    row += 1

    # Amount range
    ttk.Label(form_frame, text="Amount Range ($):").grid(row=row, column=0, sticky='w', pady=5, padx=5)
    amount_frame = ttk.Frame(form_frame)
    amount_frame.grid(row=row, column=1, sticky='w', pady=5, padx=5)
    app.sr_amount_min = ttk.Entry(amount_frame, width=10)
    app.sr_amount_min.insert(0, "100")
    app.sr_amount_min.pack(side='left')
    ttk.Label(amount_frame, text=" to ").pack(side='left', padx=5)
    app.sr_amount_max = ttk.Entry(amount_frame, width=10)
    app.sr_amount_max.insert(0, "1000")
    app.sr_amount_max.pack(side='left')
    row += 1

    # Date range
    ttk.Label(form_frame, text="Transaction Date Range:").grid(row=row, column=0, sticky='w', pady=5, padx=5)
    app.sr_date_range = ttk.Combobox(form_frame, width=15, state='readonly')
    app.sr_date_range['values'] = ('Today Only', 'Last 7 Days', 'Last 30 Days')
    app.sr_date_range.current(0)
    app.sr_date_range.grid(row=row, column=1, sticky='w', pady=5, padx=5)
    row += 1

    # Create button
    app.create_sales_receipt_btn = ttk.Button(
        content,
        text="Create Sales Receipts (Batch)",
        command=lambda: create_sales_receipt(app)
    )
    app.create_sales_receipt_btn.pack(pady=15)

    # Debug query section
    debug_frame = ttk.LabelFrame(content, text="Debug Tools", padding=10)
    debug_frame.pack(fill='x', pady=(10, 0))

    query_frame = ttk.Frame(debug_frame)
    query_frame.pack(fill='x')

    ttk.Label(query_frame, text="Query TxnID:").pack(side='left', padx=5)
    app.query_txn_id = ttk.Entry(query_frame, width=30)
    app.query_txn_id.pack(side='left', padx=5)
    app.query_sr_btn = ttk.Button(
        query_frame,
        text="Query Sales Receipt",
        command=lambda: query_sales_receipt(app)
    )
    app.query_sr_btn.pack(side='left', padx=5)
