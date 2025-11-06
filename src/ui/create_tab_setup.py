import tkinter as tk
from tkinter import ttk, scrolledtext

from .setup_subtab_setup import setup_setup_subtab
from .customer_subtab_setup import setup_customer_subtab
from .transaction_subtab_setup import setup_transaction_subtab
from app_logging import log_create


def setup_create_tab(app):
    """
    Setup the Create Data tab with nested subtabs.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    # Initialize list to track customer comboboxes
    app.customer_combos = []

    # Create nested notebook for subtabs
    app.create_notebook = ttk.Notebook(app.create_tab)
    app.create_notebook.pack(fill='both', expand=True, padx=5, pady=5)

    # Create subtab frames
    app.setup_subtab = ttk.Frame(app.create_notebook)
    app.customer_subtab = ttk.Frame(app.create_notebook)
    app.transaction_subtab = ttk.Frame(app.create_notebook)

    # Add subtabs to notebook
    app.create_notebook.add(app.setup_subtab, text='Setup')
    app.create_notebook.add(app.customer_subtab, text='Customer')
    app.create_notebook.add(app.transaction_subtab, text='Transactions')

    # Setup each subtab
    setup_setup_subtab(app)
    setup_customer_subtab(app)
    setup_transaction_subtab(app)

    # Activity log at bottom (outside subtabs, always visible)
    log_frame = ttk.LabelFrame(app.create_tab, text="Activity Log", padding=10)
    log_frame.pack(fill='both', expand=True, padx=10, pady=5)

    app.create_log = scrolledtext.ScrolledText(log_frame, height=10, width=80)
    app.create_log.pack(fill='both', expand=True)

    # Add welcome message with instructions
    log_create(app, "=== QBD Test Tool Ready ===")
    log_create(app, "IMPORTANT: QuickBooks Desktop must be running with a company file open.")
    log_create(app, "You may be prompted to authorize this application on first connection.")
    log_create(app, "")
