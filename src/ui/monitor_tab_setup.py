"""
Monitor tab setup for QuickBooks Desktop Test Tool.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from actions.monitor_actions import (
    start_monitoring, stop_monitoring, set_expected_deposit_account, clear_search
)
from actions.monitor_search_actions import search_transactions


def setup_monitor_tab(app):
    """
    Setup the Monitor Invoices tab.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    control_frame = ttk.Frame(app.monitor_tab, padding=10)
    control_frame.pack(fill='x')

    app.start_monitor_btn = ttk.Button(control_frame, text="Start Monitoring", command=lambda: start_monitoring(app))
    app.start_monitor_btn.pack(side='left', padx=5)

    app.stop_monitor_btn = ttk.Button(control_frame, text="Stop Monitoring", command=lambda: stop_monitoring(app), state='disabled')
    app.stop_monitor_btn.pack(side='left', padx=5)

    ttk.Label(control_frame, text="Check interval (seconds):").pack(side='left', padx=5)
    app.check_interval = ttk.Spinbox(control_frame, from_=5, to=300, width=10)
    app.check_interval.set(30)
    app.check_interval.pack(side='left', padx=5)

    ttk.Label(control_frame, text="Expected Deposit Account:").pack(side='left', padx=(15, 5))
    app.expected_deposit_account_combo = ttk.Combobox(control_frame, width=30, state='readonly')
    app.expected_deposit_account_combo.pack(side='left', padx=5)

    ttk.Button(control_frame, text="Set", command=lambda: set_expected_deposit_account(app)).pack(side='left', padx=5)

    # Memo Change Detection Settings
    memo_validation_frame = ttk.LabelFrame(app.monitor_tab, text="Memo Change Detection", padding=10)
    memo_validation_frame.pack(fill='x', padx=10, pady=5)

    ttk.Label(
        memo_validation_frame,
        text="Check for memo updates from initial state (binary change detection):",
        font=('TkDefaultFont', 9)
    ).pack(anchor='w', pady=(0, 5))

    validation_options = ttk.Frame(memo_validation_frame)
    validation_options.pack(fill='x')

    app.check_transaction_memo_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(
        validation_options,
        text="Check Transaction Memo Changed",
        variable=app.check_transaction_memo_var
    ).pack(side='left', padx=5)

    app.check_payment_memo_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(
        validation_options,
        text="Check Payment Record Memo Changed",
        variable=app.check_payment_memo_var
    ).pack(side='left', padx=5)

    # Search section
    search_frame = ttk.LabelFrame(app.monitor_tab, text="Search Transactions", padding=10)
    search_frame.pack(fill='x', padx=10, pady=5)

    # Row 1: Text search and Transaction Type
    row1 = ttk.Frame(search_frame)
    row1.pack(fill='x', pady=2)

    ttk.Label(row1, text="Customer/Ref#:").pack(side='left', padx=5)
    app.search_text = ttk.Entry(row1, width=25)
    app.search_text.pack(side='left', padx=5)

    ttk.Label(row1, text="Transaction ID:").pack(side='left', padx=(15, 5))
    app.search_txn_id = ttk.Entry(row1, width=20)
    app.search_txn_id.pack(side='left', padx=5)

    ttk.Label(row1, text="Type:").pack(side='left', padx=(15, 5))
    app.search_txn_type = ttk.Combobox(row1, width=18, state='readonly',
                                        values=['All', 'Invoices', 'Sales Receipts', 'Statement Charges'])
    app.search_txn_type.set('All')
    app.search_txn_type.pack(side='left', padx=5)

    # Row 2: Date range
    row2 = ttk.Frame(search_frame)
    row2.pack(fill='x', pady=2)

    ttk.Label(row2, text="Date From:").pack(side='left', padx=5)
    app.search_date_from = ttk.Entry(row2, width=12)
    app.search_date_from.pack(side='left', padx=5)
    ttk.Label(row2, text="(YYYY-MM-DD)").pack(side='left')

    ttk.Label(row2, text="To:").pack(side='left', padx=(15, 5))
    app.search_date_to = ttk.Entry(row2, width=12)
    app.search_date_to.pack(side='left', padx=5)
    ttk.Label(row2, text="(YYYY-MM-DD)").pack(side='left')

    # Row 3: Amount range and buttons
    row3 = ttk.Frame(search_frame)
    row3.pack(fill='x', pady=2)

    ttk.Label(row3, text="Amount Min:").pack(side='left', padx=5)
    app.search_amount_min = ttk.Entry(row3, width=12)
    app.search_amount_min.pack(side='left', padx=5)

    ttk.Label(row3, text="Max:").pack(side='left', padx=(15, 5))
    app.search_amount_max = ttk.Entry(row3, width=12)
    app.search_amount_max.pack(side='left', padx=5)

    # Search and Clear buttons
    ttk.Button(row3, text="Search", command=lambda: search_transactions(app), style='Accent.TButton').pack(side='left', padx=(20, 5))
    ttk.Button(row3, text="Clear", command=lambda: clear_search(app)).pack(side='left', padx=5)

    # Search scope toggle
    app.search_scope_var = tk.BooleanVar(value=False)  # False = monitored only, True = all QB
    app.search_scope_check = ttk.Checkbutton(row3, text="Search all QB transactions",
                                               variable=app.search_scope_var)
    app.search_scope_check.pack(side='left', padx=(20, 5))

    # Toggle for display mode
    ttk.Label(row3, text="Results:").pack(side='left', padx=(15, 5))
    app.search_display_mode = ttk.Combobox(row3, width=12, state='readonly', values=['Table', 'Popup'])
    app.search_display_mode.set('Table')
    app.search_display_mode.pack(side='left', padx=5)

    # Transaction list
    list_frame = ttk.LabelFrame(app.monitor_tab, text="Tracked Transactions", padding=10)
    list_frame.pack(fill='both', expand=True, padx=10, pady=5)

    # Treeview for transactions
    columns = ('Type', 'Ref#', 'Customer', 'Amount', 'Status', 'Last Checked')
    app.invoice_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)

    for col in columns:
        app.invoice_tree.heading(col, text=col)
        app.invoice_tree.column(col, width=120)

    app.invoice_tree.pack(fill='both', expand=True)

    # Monitor log
    log_frame = ttk.LabelFrame(app.monitor_tab, text="Monitor Log", padding=10)
    log_frame.pack(fill='both', expand=True, padx=10, pady=5)

    app.monitor_log = scrolledtext.ScrolledText(log_frame, height=10, width=80)
    app.monitor_log.pack(fill='both', expand=True)
