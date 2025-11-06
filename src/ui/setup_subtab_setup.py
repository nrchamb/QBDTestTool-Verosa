"""
Setup subtab setup for QuickBooks Desktop Test Tool.

Handles the Setup subtab for loading customers, items, terms, classes, and accounts.
"""

from tkinter import ttk
from config import AppConfig
from app_logging import LOG_LEVELS
from .ui_utils import create_scrollable_frame


def setup_setup_subtab(app):
    """
    Setup the Setup subtab for loading customers and items.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    # Create scrollable frame
    canvas, scrollbar, container = create_scrollable_frame(app.setup_subtab)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Content container with padding
    content = ttk.Frame(container, padding=20)
    content.pack(fill='x')

    # Welcome section
    welcome_text = "Initialize the test tool by loading existing customers and items from QuickBooks."
    ttk.Label(content, text=welcome_text, wraplength=600).pack(pady=(0, 15))

    # Grid for compact layout: Label | Button | Status
    grid_frame = ttk.Frame(content)
    grid_frame.pack(fill='x', pady=(0, 15))

    # Configure column weights - keep status column expandable for long messages
    grid_frame.columnconfigure(0, weight=0)  # Label column (fixed)
    grid_frame.columnconfigure(1, weight=0)  # Button column (fixed)
    grid_frame.columnconfigure(2, weight=1)  # Status column (expands for text)

    # Row 0: Customers
    ttk.Label(grid_frame, text="Customers:", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=0, sticky='w', padx=(0, 10), pady=5)
    app.load_customers_btn = ttk.Button(grid_frame, text="Load Existing Customers from QB", command=app._load_customers)
    app.load_customers_btn.grid(row=0, column=1, padx=5, pady=5)
    app.customers_status_label = ttk.Label(grid_frame, text="No customers loaded", foreground='red')
    app.customers_status_label.grid(row=0, column=2, sticky='w', padx=(10, 0), pady=5)

    # Row 1: Items
    ttk.Label(grid_frame, text="Items:", font=('TkDefaultFont', 9, 'bold')).grid(row=1, column=0, sticky='w', padx=(0, 10), pady=5)
    app.load_items_btn = ttk.Button(grid_frame, text="Load Items from QB", command=app._load_items)
    app.load_items_btn.grid(row=1, column=1, padx=5, pady=5)
    app.items_status_label = ttk.Label(grid_frame, text="No items loaded", foreground='red')
    app.items_status_label.grid(row=1, column=2, sticky='w', padx=(10, 0), pady=5)

    # Row 2: Terms (Optional)
    ttk.Label(grid_frame, text="Terms:", font=('TkDefaultFont', 9)).grid(row=2, column=0, sticky='w', padx=(0, 10), pady=5)
    app.load_terms_btn = ttk.Button(grid_frame, text="Load Terms from QB", command=app._load_terms)
    app.load_terms_btn.grid(row=2, column=1, padx=5, pady=5)
    app.terms_status_label = ttk.Label(grid_frame, text="No terms loaded (optional)", foreground='gray')
    app.terms_status_label.grid(row=2, column=2, sticky='w', padx=(10, 0), pady=5)

    # Row 3: Classes (Optional)
    ttk.Label(grid_frame, text="Classes:", font=('TkDefaultFont', 9)).grid(row=3, column=0, sticky='w', padx=(0, 10), pady=5)
    app.load_classes_btn = ttk.Button(grid_frame, text="Load Classes from QB", command=app._load_classes)
    app.load_classes_btn.grid(row=3, column=1, padx=5, pady=5)
    app.classes_status_label = ttk.Label(grid_frame, text="No classes loaded (optional)", foreground='gray')
    app.classes_status_label.grid(row=3, column=2, sticky='w', padx=(10, 0), pady=5)

    # Row 4: Accounts (Optional)
    ttk.Label(grid_frame, text="Accounts:", font=('TkDefaultFont', 9)).grid(row=4, column=0, sticky='w', padx=(0, 10), pady=5)
    app.load_accounts_btn = ttk.Button(grid_frame, text="Load Accounts from QB", command=app._load_accounts)
    app.load_accounts_btn.grid(row=4, column=1, padx=5, pady=5)
    app.accounts_status_label = ttk.Label(grid_frame, text="No accounts loaded (optional)", foreground='gray')
    app.accounts_status_label.grid(row=4, column=2, sticky='w', padx=(10, 0), pady=5)

    # Separator
    ttk.Separator(content, orient='horizontal').pack(fill='x', pady=15)

    # Load All button
    load_all_frame = ttk.Frame(content)
    load_all_frame.pack(fill='x', pady=(15, 0))
    app.load_all_btn = ttk.Button(load_all_frame, text="Load All / Initialize All", command=app._load_all, style='Accent.TButton')
    app.load_all_btn.pack()

    # Separator
    ttk.Separator(content, orient='horizontal').pack(fill='x', pady=15)

    # Status summary
    status_frame = ttk.Frame(content)
    status_frame.pack(fill='x')

    ttk.Label(status_frame, text="Status:", font=('TkDefaultFont', 9, 'bold')).pack(side='left', padx=(0, 10))
    app.setup_summary_label = ttk.Label(
        status_frame,
        text="Ready to load data from QuickBooks",
        font=('TkDefaultFont', 9)
    )
    app.setup_summary_label.pack(side='left')

    # Separator
    ttk.Separator(content, orient='horizontal').pack(fill='x', pady=15)

    # Settings section
    settings_frame = ttk.LabelFrame(content, text="Settings", padding=10)
    settings_frame.pack(fill='x', pady=(0, 10))

    # Log verbosity control
    log_control_frame = ttk.Frame(settings_frame)
    log_control_frame.pack(fill='x')

    ttk.Label(log_control_frame, text="Log Verbosity:").pack(side='left', padx=(0, 10))

    app.log_level_combo = ttk.Combobox(log_control_frame, width=15, state='readonly', values=LOG_LEVELS)
    app.log_level_combo.set(AppConfig.get_log_level())
    app.log_level_combo.pack(side='left', padx=5)

    def on_log_level_change(event=None):
        """Save log level when changed."""
        new_level = app.log_level_combo.get()
        AppConfig.save_log_level(new_level)

    app.log_level_combo.bind('<<ComboboxSelected>>', on_log_level_change)

    # Help text for log levels
    help_text = ttk.Label(
        settings_frame,
        text="• MINIMAL: Only summaries and errors\n"
             "• NORMAL: Operations, results, errors (default)\n"
             "• VERBOSE: Add progress per item\n"
             "• DEBUG: Add full QBXML request/response",
        font=('TkDefaultFont', 8),
        foreground='gray',
        justify='left'
    )
    help_text.pack(anchor='w', pady=(10, 0))
