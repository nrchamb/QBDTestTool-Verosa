"""
Main application entry point - Tkinter GUI for QBD Test Tool.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from datetime import datetime
from typing import Optional
import multiprocessing

from store import Store, AppState, InvoiceRecord, SalesReceiptRecord, StatementChargeRecord, add_customer, set_items, set_terms, set_classes, set_accounts, add_invoice, update_invoice, add_sales_receipt, update_sales_receipt, add_statement_charge, update_statement_charge, set_monitoring, add_verification_result, set_expected_deposit_account
from qb_connection import QBConnectionError
from qb_ipc_client import QBIPCClient, start_manager, stop_manager
from qbxml_builder import QBXMLBuilder
from qbxml_parser import QBXMLParser
from test_data import TestDataGenerator
from tray_icon import TrayIconManager


class QBDTestToolApp:
    """Main application class."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("QBD Test Tool - Verosa")
        self.root.geometry("900x700")

        # Initialize Redux store
        self.store = Store()
        self.store.subscribe(self._on_state_change)

        # Customer ListID mapping (to avoid index mismatch with nested jobs)
        self.customer_listid_map = {}  # Maps display_name -> list_id

        # Monitoring thread
        self.monitor_thread: Optional[threading.Thread] = None
        self.monitoring_stop_flag = False

        # Start connection manager process
        start_manager()

        # Initialize tray icon
        self.tray_icon = TrayIconManager(
            on_exit=self._on_closing,
            on_force_close=self._force_close
        )
        self.tray_icon.start()

        # Setup UI
        self._setup_ui()

        # Setup graceful shutdown handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_ui(self):
        """Setup the user interface."""
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Tab 1: Create Data
        self.create_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.create_tab, text='Create Data')
        self._setup_create_tab()

        # Tab 2: Monitor Transactions
        self.monitor_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.monitor_tab, text='Monitor Transactions')
        self._setup_monitor_tab()

        # Tab 3: Verification Results
        self.verify_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.verify_tab, text='Verification Results')
        self._setup_verify_tab()

        # Status bar
        self.status_bar = tk.Label(self.root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _setup_create_tab(self):
        """Setup the Create Data tab with nested subtabs."""
        # Initialize list to track customer comboboxes
        self.customer_combos = []

        # Create nested notebook for subtabs
        self.create_notebook = ttk.Notebook(self.create_tab)
        self.create_notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Create subtab frames
        self.setup_subtab = ttk.Frame(self.create_notebook)
        self.customer_subtab = ttk.Frame(self.create_notebook)
        self.invoice_subtab = ttk.Frame(self.create_notebook)
        self.sales_receipt_subtab = ttk.Frame(self.create_notebook)
        self.charge_subtab = ttk.Frame(self.create_notebook)

        # Add subtabs to notebook
        self.create_notebook.add(self.setup_subtab, text='Setup')
        self.create_notebook.add(self.customer_subtab, text='Customer')
        self.create_notebook.add(self.invoice_subtab, text='Invoice')
        self.create_notebook.add(self.sales_receipt_subtab, text='Sales Receipt')
        self.create_notebook.add(self.charge_subtab, text='Statement Charge')

        # Setup each subtab
        self._setup_setup_subtab()
        self._setup_customer_subtab()
        self._setup_invoice_subtab()
        self._setup_sales_receipt_subtab()
        self._setup_charge_subtab()

        # Activity log at bottom (outside subtabs, always visible)
        log_frame = ttk.LabelFrame(self.create_tab, text="Activity Log", padding=10)
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.create_log = scrolledtext.ScrolledText(log_frame, height=10, width=80)
        self.create_log.pack(fill='both', expand=True)

        # Add welcome message with instructions
        self._log_create("=== QBD Test Tool Ready ===")
        self._log_create("IMPORTANT: QuickBooks Desktop must be running with a company file open.")
        self._log_create("You may be prompted to authorize this application on first connection.")
        self._log_create("")

    def _create_scrollable_frame(self, parent):
        """
        Create a scrollable frame with canvas and scrollbar.

        Args:
            parent: Parent widget

        Returns:
            Tuple of (canvas, scrollbar, scrollable_frame)
        """
        # Create canvas and scrollbar
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        # Configure scrolling
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Mousewheel binding for smooth scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        # Bind mousewheel only when mouse is over this canvas
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        return canvas, scrollbar, scrollable_frame

    def _setup_setup_subtab(self):
        """Setup the Setup subtab for loading customers and items."""
        # Create scrollable frame
        canvas, scrollbar, container = self._create_scrollable_frame(self.setup_subtab)
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
        self.load_customers_btn = ttk.Button(grid_frame, text="Load Existing Customers from QB", command=self._load_customers)
        self.load_customers_btn.grid(row=0, column=1, padx=5, pady=5)
        self.customers_status_label = ttk.Label(grid_frame, text="No customers loaded", foreground='red')
        self.customers_status_label.grid(row=0, column=2, sticky='w', padx=(10, 0), pady=5)

        # Row 1: Items
        ttk.Label(grid_frame, text="Items:", font=('TkDefaultFont', 9, 'bold')).grid(row=1, column=0, sticky='w', padx=(0, 10), pady=5)
        self.load_items_btn = ttk.Button(grid_frame, text="Load Items from QB", command=self._load_items)
        self.load_items_btn.grid(row=1, column=1, padx=5, pady=5)
        self.items_status_label = ttk.Label(grid_frame, text="No items loaded", foreground='red')
        self.items_status_label.grid(row=1, column=2, sticky='w', padx=(10, 0), pady=5)

        # Row 2: Terms (Optional)
        ttk.Label(grid_frame, text="Terms:", font=('TkDefaultFont', 9)).grid(row=2, column=0, sticky='w', padx=(0, 10), pady=5)
        self.load_terms_btn = ttk.Button(grid_frame, text="Load Terms from QB", command=self._load_terms)
        self.load_terms_btn.grid(row=2, column=1, padx=5, pady=5)
        self.terms_status_label = ttk.Label(grid_frame, text="No terms loaded (optional)", foreground='gray')
        self.terms_status_label.grid(row=2, column=2, sticky='w', padx=(10, 0), pady=5)

        # Row 3: Classes (Optional)
        ttk.Label(grid_frame, text="Classes:", font=('TkDefaultFont', 9)).grid(row=3, column=0, sticky='w', padx=(0, 10), pady=5)
        self.load_classes_btn = ttk.Button(grid_frame, text="Load Classes from QB", command=self._load_classes)
        self.load_classes_btn.grid(row=3, column=1, padx=5, pady=5)
        self.classes_status_label = ttk.Label(grid_frame, text="No classes loaded (optional)", foreground='gray')
        self.classes_status_label.grid(row=3, column=2, sticky='w', padx=(10, 0), pady=5)

        # Row 4: Accounts (Optional)
        ttk.Label(grid_frame, text="Accounts:", font=('TkDefaultFont', 9)).grid(row=4, column=0, sticky='w', padx=(0, 10), pady=5)
        self.load_accounts_btn = ttk.Button(grid_frame, text="Load Accounts from QB", command=self._load_accounts)
        self.load_accounts_btn.grid(row=4, column=1, padx=5, pady=5)
        self.accounts_status_label = ttk.Label(grid_frame, text="No accounts loaded (optional)", foreground='gray')
        self.accounts_status_label.grid(row=4, column=2, sticky='w', padx=(10, 0), pady=5)

        # Load All button
        load_all_frame = ttk.Frame(content)
        load_all_frame.pack(fill='x', pady=(15, 0))
        self.load_all_btn = ttk.Button(load_all_frame, text="Load All / Initialize All", command=self._load_all, style='Accent.TButton')
        self.load_all_btn.pack()

        # Separator
        ttk.Separator(content, orient='horizontal').pack(fill='x', pady=15)

        # Status summary
        status_frame = ttk.Frame(content)
        status_frame.pack(fill='x')

        ttk.Label(status_frame, text="Status:", font=('TkDefaultFont', 9, 'bold')).pack(side='left', padx=(0, 10))
        self.setup_summary_label = ttk.Label(
            status_frame,
            text="Ready to load data from QuickBooks",
            font=('TkDefaultFont', 9)
        )
        self.setup_summary_label.pack(side='left')

    def _setup_customer_subtab(self):
        """Setup the Customer subtab for creating new customers."""
        # Create scrollable frame
        canvas, scrollbar, container = self._create_scrollable_frame(self.customer_subtab)
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
        self.customer_email = ttk.Entry(form_frame, width=50)
        self.customer_email.grid(row=row, column=2, pady=5, padx=5, sticky='w')
        row += 1

        # Separator
        ttk.Separator(form_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky='ew', pady=10)
        row += 1

        # Jobs configuration
        ttk.Label(form_frame, text="Jobs:", font=('TkDefaultFont', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=5, padx=(0, 10))
        self.num_jobs = tk.Spinbox(form_frame, from_=0, to=10, width=10)
        self.num_jobs.delete(0, tk.END)
        self.num_jobs.insert(0, "0")
        self.num_jobs.grid(row=row, column=2, pady=5, padx=5, sticky='w')
        row += 1

        # Sub-jobs per job configuration
        ttk.Label(form_frame, text="Sub-jobs per Job:", font=('TkDefaultFont', 9)).grid(row=row, column=0, sticky='w', pady=5, padx=(0, 10))
        self.num_subjobs = tk.Spinbox(form_frame, from_=0, to=10, width=10)
        self.num_subjobs.delete(0, tk.END)
        self.num_subjobs.insert(0, "0")
        self.num_subjobs.grid(row=row, column=2, pady=5, padx=5, sticky='w')
        row += 1

        # Calculation display
        self.customer_calc_label = ttk.Label(form_frame, text="Will create: 1 customer", foreground='gray')
        self.customer_calc_label.grid(row=row, column=0, columnspan=3, sticky='w', pady=5, padx=(0, 10))
        row += 1

        # Bind spinboxes to update calculation
        def update_calculation(*args):
            try:
                jobs = int(self.num_jobs.get() or 0)
                subjobs = int(self.num_subjobs.get() or 0)
                total = 1 + jobs + (jobs * subjobs)

                parts = [f"1 customer"]
                if jobs > 0:
                    parts.append(f"{jobs} job{'s' if jobs > 1 else ''}")
                if jobs > 0 and subjobs > 0:
                    total_subjobs = jobs * subjobs
                    parts.append(f"{total_subjobs} sub-job{'s' if total_subjobs > 1 else ''}")

                self.customer_calc_label.config(text=f"Will create: {' + '.join(parts)} = {total} total")
            except ValueError:
                self.customer_calc_label.config(text="Will create: 1 customer")

        self.num_jobs.config(command=update_calculation)
        self.num_subjobs.config(command=update_calculation)

        # Separator
        ttk.Separator(form_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky='ew', pady=10)
        row += 1

        # Helper function to create field row
        def create_field_row(label_text, var_name, entry_name, default_random=True):
            nonlocal row
            # Checkbox
            var = tk.BooleanVar(value=default_random)
            setattr(self, var_name, var)

            chk = ttk.Checkbutton(form_frame, text="Random", variable=var)
            chk.grid(row=row, column=1, sticky='w', pady=5)

            # Label
            ttk.Label(form_frame, text=label_text).grid(row=row, column=0, sticky='w', pady=5, padx=(0, 10))

            # Entry
            entry = ttk.Entry(form_frame, width=50)
            entry.grid(row=row, column=2, pady=5, padx=5, sticky='w')
            setattr(self, entry_name, entry)

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
        self.random_billing_address = tk.BooleanVar(value=True)
        chk = ttk.Checkbutton(form_frame, text="Random", variable=self.random_billing_address)
        chk.grid(row=row, column=1, sticky='w', pady=5)
        ttk.Label(form_frame, text="Billing Address:", font=('TkDefaultFont', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=5, padx=(0, 10))
        row += 1

        # Billing address fields
        self.customer_bill_addr1 = ttk.Entry(form_frame, width=50)
        ttk.Label(form_frame, text="  Street:").grid(row=row, column=0, sticky='w', pady=2, padx=(0, 10))
        self.customer_bill_addr1.grid(row=row, column=2, pady=2, padx=5, sticky='w')
        row += 1

        self.customer_bill_city = ttk.Entry(form_frame, width=50)
        ttk.Label(form_frame, text="  City:").grid(row=row, column=0, sticky='w', pady=2, padx=(0, 10))
        self.customer_bill_city.grid(row=row, column=2, pady=2, padx=5, sticky='w')
        row += 1

        self.customer_bill_state = ttk.Entry(form_frame, width=50)
        ttk.Label(form_frame, text="  State:").grid(row=row, column=0, sticky='w', pady=2, padx=(0, 10))
        self.customer_bill_state.grid(row=row, column=2, pady=2, padx=5, sticky='w')
        row += 1

        self.customer_bill_zip = ttk.Entry(form_frame, width=50)
        ttk.Label(form_frame, text="  Zip:").grid(row=row, column=0, sticky='w', pady=2, padx=(0, 10))
        self.customer_bill_zip.grid(row=row, column=2, pady=2, padx=5, sticky='w')
        row += 1

        # Bind billing address checkbox
        def toggle_billing(*args):
            state = 'disabled' if self.random_billing_address.get() else 'normal'
            self.customer_bill_addr1.config(state=state)
            self.customer_bill_city.config(state=state)
            self.customer_bill_state.config(state=state)
            self.customer_bill_zip.config(state=state)

        self.random_billing_address.trace_add('write', toggle_billing)
        toggle_billing()

        # Shipping Address section
        ttk.Separator(form_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky='ew', pady=10)
        row += 1

        # Shipping address checkbox
        self.random_shipping_address = tk.BooleanVar(value=True)
        chk = ttk.Checkbutton(form_frame, text="Random", variable=self.random_shipping_address)
        chk.grid(row=row, column=1, sticky='w', pady=5)
        ttk.Label(form_frame, text="Shipping Address:", font=('TkDefaultFont', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=5, padx=(0, 10))
        row += 1

        # Shipping address fields
        self.customer_ship_addr1 = ttk.Entry(form_frame, width=50)
        ttk.Label(form_frame, text="  Street:").grid(row=row, column=0, sticky='w', pady=2, padx=(0, 10))
        self.customer_ship_addr1.grid(row=row, column=2, pady=2, padx=5, sticky='w')
        row += 1

        self.customer_ship_city = ttk.Entry(form_frame, width=50)
        ttk.Label(form_frame, text="  City:").grid(row=row, column=0, sticky='w', pady=2, padx=(0, 10))
        self.customer_ship_city.grid(row=row, column=2, pady=2, padx=5, sticky='w')
        row += 1

        self.customer_ship_state = ttk.Entry(form_frame, width=50)
        ttk.Label(form_frame, text="  State:").grid(row=row, column=0, sticky='w', pady=2, padx=(0, 10))
        self.customer_ship_state.grid(row=row, column=2, pady=2, padx=5, sticky='w')
        row += 1

        self.customer_ship_zip = ttk.Entry(form_frame, width=50)
        ttk.Label(form_frame, text="  Zip:").grid(row=row, column=0, sticky='w', pady=2, padx=(0, 10))
        self.customer_ship_zip.grid(row=row, column=2, pady=2, padx=5, sticky='w')
        row += 1

        # Bind shipping address checkbox
        def toggle_shipping(*args):
            state = 'disabled' if self.random_shipping_address.get() else 'normal'
            self.customer_ship_addr1.config(state=state)
            self.customer_ship_city.config(state=state)
            self.customer_ship_state.config(state=state)
            self.customer_ship_zip.config(state=state)

        self.random_shipping_address.trace_add('write', toggle_shipping)
        toggle_shipping()

        # Buttons
        button_frame = ttk.Frame(content)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Select All Random", command=self._select_all_customer_fields).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Clear All Random", command=self._clear_all_customer_fields).pack(side='left', padx=5)

        # Create button
        self.create_customer_btn = ttk.Button(
            content,
            text="Create New Customer",
            command=self._create_customer
        )
        self.create_customer_btn.pack(pady=10)

    def _setup_invoice_subtab(self):
        """Setup the Invoice subtab for batch invoice creation."""
        # Create scrollable frame
        canvas, scrollbar, container = self._create_scrollable_frame(self.invoice_subtab)
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
        self.customer_combo = ttk.Combobox(form_frame, width=50, state='readonly')
        self.customer_combo.grid(row=row, column=1, pady=5, padx=5, sticky='w')
        self.customer_combos.append(self.customer_combo)
        row += 1

        # Number of invoices
        ttk.Label(form_frame, text="Number of Invoices:").grid(row=row, column=0, sticky='w', pady=5, padx=5)
        self.num_invoices = ttk.Spinbox(form_frame, from_=1, to=100, width=10)
        self.num_invoices.set(1)
        self.num_invoices.grid(row=row, column=1, sticky='w', pady=5, padx=5)
        row += 1

        # Line items range
        ttk.Label(form_frame, text="Line Items Range:").grid(row=row, column=0, sticky='w', pady=5, padx=5)
        line_items_frame = ttk.Frame(form_frame)
        line_items_frame.grid(row=row, column=1, sticky='w', pady=5, padx=5)
        self.num_lines_min = ttk.Spinbox(line_items_frame, from_=1, to=20, width=5)
        self.num_lines_min.set(1)
        self.num_lines_min.pack(side='left')
        ttk.Label(line_items_frame, text=" to ").pack(side='left', padx=5)
        self.num_lines_max = ttk.Spinbox(line_items_frame, from_=1, to=20, width=5)
        self.num_lines_max.set(5)
        self.num_lines_max.pack(side='left')
        row += 1

        # Amount range
        ttk.Label(form_frame, text="Amount Range ($):").grid(row=row, column=0, sticky='w', pady=5, padx=5)
        amount_frame = ttk.Frame(form_frame)
        amount_frame.grid(row=row, column=1, sticky='w', pady=5, padx=5)
        self.amount_min = ttk.Entry(amount_frame, width=10)
        self.amount_min.insert(0, "100")
        self.amount_min.pack(side='left')
        ttk.Label(amount_frame, text=" to ").pack(side='left', padx=5)
        self.amount_max = ttk.Entry(amount_frame, width=10)
        self.amount_max.insert(0, "5000")
        self.amount_max.pack(side='left')
        row += 1

        # Date range
        ttk.Label(form_frame, text="Transaction Date Range:").grid(row=row, column=0, sticky='w', pady=5, padx=5)
        self.invoice_date_range = ttk.Combobox(form_frame, width=15, state='readonly')
        self.invoice_date_range['values'] = ('Today Only', 'Last 7 Days', 'Last 30 Days')
        self.invoice_date_range.current(0)
        self.invoice_date_range.grid(row=row, column=1, sticky='w', pady=5, padx=5)
        row += 1

        # PO Number Prefix (optional)
        ttk.Label(form_frame, text="PO Number Prefix:").grid(row=row, column=0, sticky='w', pady=5, padx=5)
        self.invoice_po_prefix = ttk.Entry(form_frame, width=15)
        self.invoice_po_prefix.insert(0, "PO-")
        self.invoice_po_prefix.grid(row=row, column=1, sticky='w', pady=5, padx=5)
        row += 1

        # Terms (optional)
        ttk.Label(form_frame, text="Terms (optional):").grid(row=row, column=0, sticky='w', pady=5, padx=5)
        self.invoice_terms_combo = ttk.Combobox(form_frame, width=30, state='readonly')
        self.invoice_terms_combo['values'] = ['(None)']
        self.invoice_terms_combo.current(0)
        self.invoice_terms_combo.grid(row=row, column=1, sticky='w', pady=5, padx=5)
        row += 1

        # Class (optional)
        ttk.Label(form_frame, text="Class (optional):").grid(row=row, column=0, sticky='w', pady=5, padx=5)
        self.invoice_class_combo = ttk.Combobox(form_frame, width=30, state='readonly')
        self.invoice_class_combo['values'] = ['(None)']
        self.invoice_class_combo.current(0)
        self.invoice_class_combo.grid(row=row, column=1, sticky='w', pady=5, padx=5)
        row += 1

        # Create button
        self.create_invoice_btn = ttk.Button(
            content,
            text="Create Invoices (Batch)",
            command=self._create_invoice
        )
        self.create_invoice_btn.pack(pady=15)

    def _setup_sales_receipt_subtab(self):
        """Setup the Sales Receipt subtab for batch sales receipt creation."""
        # Create scrollable frame
        canvas, scrollbar, container = self._create_scrollable_frame(self.sales_receipt_subtab)
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
        self.sr_customer_combo = ttk.Combobox(form_frame, width=50, state='readonly')
        self.sr_customer_combo.grid(row=row, column=1, pady=5, padx=5, sticky='w')
        self.customer_combos.append(self.sr_customer_combo)
        row += 1

        # Number of sales receipts
        ttk.Label(form_frame, text="Number of Sales Receipts:").grid(row=row, column=0, sticky='w', pady=5, padx=5)
        self.num_sales_receipts = ttk.Spinbox(form_frame, from_=1, to=100, width=10)
        self.num_sales_receipts.set(1)
        self.num_sales_receipts.grid(row=row, column=1, sticky='w', pady=5, padx=5)
        row += 1

        # Line items range
        ttk.Label(form_frame, text="Line Items Range:").grid(row=row, column=0, sticky='w', pady=5, padx=5)
        line_items_frame = ttk.Frame(form_frame)
        line_items_frame.grid(row=row, column=1, sticky='w', pady=5, padx=5)
        self.num_sr_lines_min = ttk.Spinbox(line_items_frame, from_=1, to=20, width=5)
        self.num_sr_lines_min.set(1)
        self.num_sr_lines_min.pack(side='left')
        ttk.Label(line_items_frame, text=" to ").pack(side='left', padx=5)
        self.num_sr_lines_max = ttk.Spinbox(line_items_frame, from_=1, to=20, width=5)
        self.num_sr_lines_max.set(3)
        self.num_sr_lines_max.pack(side='left')
        row += 1

        # Amount range
        ttk.Label(form_frame, text="Amount Range ($):").grid(row=row, column=0, sticky='w', pady=5, padx=5)
        amount_frame = ttk.Frame(form_frame)
        amount_frame.grid(row=row, column=1, sticky='w', pady=5, padx=5)
        self.sr_amount_min = ttk.Entry(amount_frame, width=10)
        self.sr_amount_min.insert(0, "100")
        self.sr_amount_min.pack(side='left')
        ttk.Label(amount_frame, text=" to ").pack(side='left', padx=5)
        self.sr_amount_max = ttk.Entry(amount_frame, width=10)
        self.sr_amount_max.insert(0, "1000")
        self.sr_amount_max.pack(side='left')
        row += 1

        # Date range
        ttk.Label(form_frame, text="Transaction Date Range:").grid(row=row, column=0, sticky='w', pady=5, padx=5)
        self.sr_date_range = ttk.Combobox(form_frame, width=15, state='readonly')
        self.sr_date_range['values'] = ('Today Only', 'Last 7 Days', 'Last 30 Days')
        self.sr_date_range.current(0)
        self.sr_date_range.grid(row=row, column=1, sticky='w', pady=5, padx=5)
        row += 1

        # Create button
        self.create_sales_receipt_btn = ttk.Button(
            content,
            text="Create Sales Receipts (Batch)",
            command=self._create_sales_receipt
        )
        self.create_sales_receipt_btn.pack(pady=15)

        # Debug query section
        debug_frame = ttk.LabelFrame(content, text="Debug Tools", padding=10)
        debug_frame.pack(fill='x', pady=(10, 0))

        query_frame = ttk.Frame(debug_frame)
        query_frame.pack(fill='x')

        ttk.Label(query_frame, text="Query TxnID:").pack(side='left', padx=5)
        self.query_txn_id = ttk.Entry(query_frame, width=30)
        self.query_txn_id.pack(side='left', padx=5)
        self.query_sr_btn = ttk.Button(
            query_frame,
            text="Query Sales Receipt",
            command=self._query_sales_receipt
        )
        self.query_sr_btn.pack(side='left', padx=5)

    def _setup_charge_subtab(self):
        """Setup the Statement Charge subtab for batch charge creation."""
        # Create scrollable frame
        canvas, scrollbar, container = self._create_scrollable_frame(self.charge_subtab)
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
        self.charge_customer_combo = ttk.Combobox(form_frame, width=50, state='readonly')
        self.charge_customer_combo.grid(row=row, column=1, pady=5, padx=5, sticky='w')
        self.customer_combos.append(self.charge_customer_combo)
        row += 1

        # Number of charges
        ttk.Label(form_frame, text="Number of Charges:").grid(row=row, column=0, sticky='w', pady=5, padx=5)
        self.num_charges = ttk.Spinbox(form_frame, from_=1, to=100, width=10)
        self.num_charges.set(1)
        self.num_charges.grid(row=row, column=1, sticky='w', pady=5, padx=5)
        row += 1

        # Amount range
        ttk.Label(form_frame, text="Amount Range ($):").grid(row=row, column=0, sticky='w', pady=5, padx=5)
        amount_frame = ttk.Frame(form_frame)
        amount_frame.grid(row=row, column=1, sticky='w', pady=5, padx=5)
        self.charge_amount_min = ttk.Entry(amount_frame, width=10)
        self.charge_amount_min.insert(0, "50")
        self.charge_amount_min.pack(side='left')
        ttk.Label(amount_frame, text=" to ").pack(side='left', padx=5)
        self.charge_amount_max = ttk.Entry(amount_frame, width=10)
        self.charge_amount_max.insert(0, "500")
        self.charge_amount_max.pack(side='left')
        row += 1

        # Date range
        ttk.Label(form_frame, text="Transaction Date Range:").grid(row=row, column=0, sticky='w', pady=5, padx=5)
        self.charge_date_range = ttk.Combobox(form_frame, width=15, state='readonly')
        self.charge_date_range['values'] = ('Today Only', 'Last 7 Days', 'Last 30 Days')
        self.charge_date_range.current(0)
        self.charge_date_range.grid(row=row, column=1, sticky='w', pady=5, padx=5)
        row += 1

        # Create button
        self.create_charge_btn = ttk.Button(
            content,
            text="Create Statement Charges (Batch)",
            command=self._create_charge
        )
        self.create_charge_btn.pack(pady=15)

    def _setup_monitor_tab(self):
        """Setup the Monitor Invoices tab."""
        control_frame = ttk.Frame(self.monitor_tab, padding=10)
        control_frame.pack(fill='x')

        self.start_monitor_btn = ttk.Button(control_frame, text="Start Monitoring", command=self._start_monitoring)
        self.start_monitor_btn.pack(side='left', padx=5)

        self.stop_monitor_btn = ttk.Button(control_frame, text="Stop Monitoring", command=self._stop_monitoring, state='disabled')
        self.stop_monitor_btn.pack(side='left', padx=5)

        ttk.Label(control_frame, text="Check interval (seconds):").pack(side='left', padx=5)
        self.check_interval = ttk.Spinbox(control_frame, from_=5, to=300, width=10)
        self.check_interval.set(30)
        self.check_interval.pack(side='left', padx=5)

        ttk.Label(control_frame, text="Expected Deposit Account:").pack(side='left', padx=(15, 5))
        self.expected_deposit_account_combo = ttk.Combobox(control_frame, width=30, state='readonly')
        self.expected_deposit_account_combo.pack(side='left', padx=5)

        ttk.Button(control_frame, text="Set", command=self._set_expected_deposit_account).pack(side='left', padx=5)

        # Search section
        search_frame = ttk.LabelFrame(self.monitor_tab, text="Search Transactions", padding=10)
        search_frame.pack(fill='x', padx=10, pady=5)

        # Row 1: Text search and Transaction Type
        row1 = ttk.Frame(search_frame)
        row1.pack(fill='x', pady=2)

        ttk.Label(row1, text="Customer/Ref#:").pack(side='left', padx=5)
        self.search_text = ttk.Entry(row1, width=25)
        self.search_text.pack(side='left', padx=5)

        ttk.Label(row1, text="Transaction ID:").pack(side='left', padx=(15, 5))
        self.search_txn_id = ttk.Entry(row1, width=20)
        self.search_txn_id.pack(side='left', padx=5)

        ttk.Label(row1, text="Type:").pack(side='left', padx=(15, 5))
        self.search_txn_type = ttk.Combobox(row1, width=18, state='readonly',
                                            values=['All', 'Invoices', 'Sales Receipts', 'Statement Charges'])
        self.search_txn_type.set('All')
        self.search_txn_type.pack(side='left', padx=5)

        # Row 2: Date range
        row2 = ttk.Frame(search_frame)
        row2.pack(fill='x', pady=2)

        ttk.Label(row2, text="Date From:").pack(side='left', padx=5)
        self.search_date_from = ttk.Entry(row2, width=12)
        self.search_date_from.pack(side='left', padx=5)
        ttk.Label(row2, text="(YYYY-MM-DD)").pack(side='left')

        ttk.Label(row2, text="To:").pack(side='left', padx=(15, 5))
        self.search_date_to = ttk.Entry(row2, width=12)
        self.search_date_to.pack(side='left', padx=5)
        ttk.Label(row2, text="(YYYY-MM-DD)").pack(side='left')

        # Row 3: Amount range and buttons
        row3 = ttk.Frame(search_frame)
        row3.pack(fill='x', pady=2)

        ttk.Label(row3, text="Amount Min:").pack(side='left', padx=5)
        self.search_amount_min = ttk.Entry(row3, width=12)
        self.search_amount_min.pack(side='left', padx=5)

        ttk.Label(row3, text="Max:").pack(side='left', padx=(15, 5))
        self.search_amount_max = ttk.Entry(row3, width=12)
        self.search_amount_max.pack(side='left', padx=5)

        # Search and Clear buttons
        ttk.Button(row3, text="Search", command=self._search_transactions, style='Accent.TButton').pack(side='left', padx=(20, 5))
        ttk.Button(row3, text="Clear", command=self._clear_search).pack(side='left', padx=5)

        # Search scope toggle
        self.search_scope_var = tk.BooleanVar(value=False)  # False = monitored only, True = all QB
        self.search_scope_check = ttk.Checkbutton(row3, text="Search all QB transactions",
                                                   variable=self.search_scope_var)
        self.search_scope_check.pack(side='left', padx=(20, 5))

        # Toggle for display mode
        ttk.Label(row3, text="Results:").pack(side='left', padx=(15, 5))
        self.search_display_mode = ttk.Combobox(row3, width=12, state='readonly', values=['Table', 'Popup'])
        self.search_display_mode.set('Table')
        self.search_display_mode.pack(side='left', padx=5)

        # Transaction list
        list_frame = ttk.LabelFrame(self.monitor_tab, text="Tracked Transactions", padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Treeview for transactions
        columns = ('Type', 'Ref#', 'Customer', 'Amount', 'Status', 'Last Checked')
        self.invoice_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)

        for col in columns:
            self.invoice_tree.heading(col, text=col)
            self.invoice_tree.column(col, width=120)

        self.invoice_tree.pack(fill='both', expand=True)

        # Monitor log
        log_frame = ttk.LabelFrame(self.monitor_tab, text="Monitor Log", padding=10)
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.monitor_log = scrolledtext.ScrolledText(log_frame, height=10, width=80)
        self.monitor_log.pack(fill='both', expand=True)

    def _setup_verify_tab(self):
        """Setup the Verification Results tab."""
        # Results tree
        tree_frame = ttk.Frame(self.verify_tab, padding=10)
        tree_frame.pack(fill='both', expand=True)

        columns = ('Timestamp', 'Type', 'Txn Ref#', 'Result', 'Details')
        self.verify_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=20)

        # Set column widths
        self.verify_tree.heading('Timestamp', text='Timestamp')
        self.verify_tree.column('Timestamp', width=150)

        self.verify_tree.heading('Type', text='Type')
        self.verify_tree.column('Type', width=120)

        self.verify_tree.heading('Txn Ref#', text='Txn Ref#')
        self.verify_tree.column('Txn Ref#', width=100)

        self.verify_tree.heading('Result', text='Result')
        self.verify_tree.column('Result', width=80)

        self.verify_tree.heading('Details', text='Details')
        self.verify_tree.column('Details', width=600)

        self.verify_tree.pack(fill='both', expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.verify_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.verify_tree.configure(yscrollcommand=scrollbar.set)

    def _log_create(self, message: str):
        """Log message to create tab."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.create_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.create_log.see(tk.END)

    def _log_monitor(self, message: str):
        """Log message to monitor tab."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.monitor_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.monitor_log.see(tk.END)

    def _select_all_customer_fields(self):
        """Select all customer field checkboxes."""
        self.random_first_name.set(True)
        self.random_last_name.set(True)
        self.random_company.set(True)
        self.random_phone.set(True)
        self.random_billing_address.set(True)
        self.random_shipping_address.set(True)

    def _clear_all_customer_fields(self):
        """Clear all customer field checkboxes."""
        self.random_first_name.set(False)
        self.random_last_name.set(False)
        self.random_company.set(False)
        self.random_phone.set(False)
        self.random_billing_address.set(False)
        self.random_shipping_address.set(False)

    def _create_customer(self):
        """Create a customer in QuickBooks (wrapper - launches background thread)."""
        email = self.customer_email.get().strip()

        if not email:
            messagebox.showerror("Error", "Email is required!")
            return

        # Collect field enable states (True = random, False = manual)
        field_config = {
            'first_name': self.random_first_name.get(),
            'last_name': self.random_last_name.get(),
            'company': self.random_company.get(),
            'phone': self.random_phone.get(),
            'billing_address': self.random_billing_address.get(),
            'shipping_address': self.random_shipping_address.get()
        }

        # Collect manual values (only used when field_config[field] is False)
        manual_values = {
            'first_name': self.customer_first_name.get().strip() if not self.random_first_name.get() else None,
            'last_name': self.customer_last_name.get().strip() if not self.random_last_name.get() else None,
            'company': self.customer_company.get().strip() if not self.random_company.get() else None,
            'phone': self.customer_phone.get().strip() if not self.random_phone.get() else None,
        }

        # Collect billing address if not random
        if not self.random_billing_address.get():
            bill_addr1 = self.customer_bill_addr1.get().strip()
            bill_city = self.customer_bill_city.get().strip()
            bill_state = self.customer_bill_state.get().strip()
            bill_zip = self.customer_bill_zip.get().strip()

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
        if not self.random_shipping_address.get():
            ship_addr1 = self.customer_ship_addr1.get().strip()
            ship_city = self.customer_ship_city.get().strip()
            ship_state = self.customer_ship_state.get().strip()
            ship_zip = self.customer_ship_zip.get().strip()

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
            num_jobs = int(self.num_jobs.get() or 0)
            num_subjobs = int(self.num_subjobs.get() or 0)
        except ValueError:
            messagebox.showerror("Error", "Invalid job count values!")
            return

        # Disable button and update status
        self.create_customer_btn.config(state='disabled')
        total_records = 1 + num_jobs + (num_jobs * num_subjobs)
        self.status_bar.config(text=f"Creating {total_records} record(s)...")

        # Launch background thread
        thread = threading.Thread(
            target=self._create_customer_worker,
            args=(email, field_config, manual_values, num_jobs, num_subjobs),
            daemon=True
        )
        thread.start()

    def _create_customer_worker(self, email: str, field_config: dict, manual_values: dict,
                                 num_jobs: int = 0, num_subjobs: int = 0):
        """Worker function to create customer and jobs in background."""
        try:
            # Step 1: Create the parent customer
            self.root.after(0, lambda: self._log_create(f"Generating customer data with email: {email}"))

            customer_data = TestDataGenerator.generate_customer(
                email=email,
                field_config=field_config,
                manual_values=manual_values
            )

            self.root.after(0, lambda: self._log_create(f"Creating customer: {customer_data['name']}"))

            # Build QBXML request
            request = QBXMLBuilder.build_customer_add(customer_data)

            # Send to QuickBooks
            qb = QBIPCClient()
            response_xml = qb.execute_request(request)

            # Parse response
            parser_result = QBXMLParser.parse_response(response_xml)

            if not parser_result['success']:
                error_msg = parser_result.get('error', 'Unknown error')
                self.root.after(0, lambda: self._log_create(f"✗ Customer creation failed: {error_msg}"))
                self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
                return

            # Customer created successfully
            customer_info = parser_result['data']
            customer_list_id = customer_info['list_id']
            customer_data['list_id'] = customer_list_id
            customer_data['full_name'] = customer_info['full_name']
            customer_data['created_by_app'] = True
            self.store.dispatch(add_customer(customer_data))

            self.root.after(0, lambda: self._log_create(f"✓ Customer created: {customer_info['full_name']}"))
            self.root.after(0, self._update_customer_combo)

            # Step 2: Create jobs if requested
            if num_jobs > 0:
                self.root.after(0, lambda: self._log_create(f"Creating {num_jobs} job(s)..."))

                for job_idx in range(num_jobs):
                    try:
                        # Generate job data
                        job_data = TestDataGenerator.generate_job(
                            parent_customer_ref=customer_list_id,
                            email=email,
                            is_subjob=False
                        )

                        job_num = job_idx + 1
                        self.root.after(0, lambda n=job_num, total=num_jobs, name=job_data['name']:
                                      self._log_create(f"  Creating job {n}/{total}: {name}"))

                        # Build and send QBXML request
                        request = QBXMLBuilder.build_customer_add(job_data)
                        response_xml = qb.execute_request(request)
                        parser_result = QBXMLParser.parse_response(response_xml)

                        if not parser_result['success']:
                            error_msg = parser_result.get('error', 'Unknown error')
                            self.root.after(0, lambda n=job_num, err=error_msg:
                                          self._log_create(f"  ✗ Job {n} failed: {err}"))
                            continue

                        # Job created successfully
                        job_info = parser_result['data']
                        job_list_id = job_info['list_id']
                        self.root.after(0, lambda n=job_num, name=job_info['full_name']:
                                      self._log_create(f"  ✓ Job {n}/{num_jobs} created: {name}"))

                        # Step 3: Create sub-jobs for this job if requested
                        if num_subjobs > 0:
                            for subjob_idx in range(num_subjobs):
                                try:
                                    # Generate sub-job data
                                    subjob_data = TestDataGenerator.generate_job(
                                        parent_customer_ref=job_list_id,
                                        email=email,
                                        is_subjob=True
                                    )

                                    subjob_num = subjob_idx + 1
                                    self.root.after(0, lambda jn=job_num, sn=subjob_num, total=num_subjobs, name=subjob_data['name']:
                                                  self._log_create(f"    Creating sub-job {sn}/{total} for job {jn}: {name}"))

                                    # Build and send QBXML request
                                    request = QBXMLBuilder.build_customer_add(subjob_data)
                                    response_xml = qb.execute_request(request)
                                    parser_result = QBXMLParser.parse_response(response_xml)

                                    if not parser_result['success']:
                                        error_msg = parser_result.get('error', 'Unknown error')
                                        self.root.after(0, lambda sn=subjob_num, err=error_msg:
                                                      self._log_create(f"    ✗ Sub-job {sn} failed: {err}"))
                                        continue

                                    # Sub-job created successfully
                                    subjob_info = parser_result['data']
                                    self.root.after(0, lambda sn=subjob_num, name=subjob_info['full_name']:
                                                  self._log_create(f"    ✓ Sub-job {sn}/{num_subjobs} created: {name}"))

                                except Exception as e:
                                    error_str = str(e)
                                    self.root.after(0, lambda sn=subjob_idx+1, err=error_str:
                                                  self._log_create(f"    ✗ Sub-job {sn} error: {err}"))

                    except Exception as e:
                        error_str = str(e)
                        self.root.after(0, lambda n=job_idx+1, err=error_str:
                                      self._log_create(f"  ✗ Job {n} error: {err}"))

                # Summary
                total_created = 1 + num_jobs + (num_jobs * num_subjobs)
                self.root.after(0, lambda t=total_created:
                              self._log_create(f"✓ All done! Created {t} total record(s)"))
            else:
                self.root.after(0, lambda: self._log_create(f"✓ Customer creation complete!"))

        except QBConnectionError as e:
            error_str = str(e)
            self.root.after(0, lambda: self._log_create(f"✗ QB Connection Error: {error_str}"))
            self.root.after(0, lambda: messagebox.showerror("QB Connection Error", error_str))
        except Exception as e:
            error_str = str(e)
            self.root.after(0, lambda: self._log_create(f"✗ Unexpected Error: {error_str}"))
            self.root.after(0, lambda: messagebox.showerror("Error", error_str))
        finally:
            # Re-enable button and update status
            self.root.after(0, lambda: self.create_customer_btn.config(state='normal'))
            self.root.after(0, lambda: self.status_bar.config(text="Ready"))

    def _load_items(self):
        """Load items from QuickBooks (wrapper - launches background thread)."""
        # Disable button
        self.load_items_btn.config(state='disabled')
        self.status_bar.config(text="Loading items from QuickBooks...")
        self.items_status_label.config(text="Loading...", foreground='orange')

        # Launch background thread
        thread = threading.Thread(target=self._load_items_worker, daemon=True)
        thread.start()

    def _load_items_worker(self):
        """Worker function to load items in background."""
        try:
            self.root.after(0, lambda: self._log_create("Loading items from QuickBooks..."))

            # Build item query request
            request = QBXMLBuilder.build_item_query()

            # Send to QuickBooks
            qb = QBIPCClient()
            response_xml = qb.execute_request(request)

            # Parse response
            parser_result = QBXMLParser.parse_response(response_xml)

            if parser_result['success']:
                items = parser_result['data']['items']
                self.store.dispatch(set_items(items))

                count = len(items)
                self.root.after(0, lambda: self._log_create(f"✓ Loaded {count} items from QuickBooks"))
                self.root.after(0, lambda: self.items_status_label.config(
                    text=f"{count} item{'s' if count != 1 else ''} loaded", foreground='green'
                ))
                # Update setup summary - only show ready when BOTH are loaded
                state = self.store.get_state()
                num_customers = len(state.customers)
                if num_customers > 0 and count > 0:
                    self.root.after(0, lambda: self.setup_summary_label.config(
                        text=f"{num_customers} customers, {count} items loaded - Ready to create transactions"
                    ))
                else:
                    self.root.after(0, lambda: self.setup_summary_label.config(
                        text=f"{num_customers} customers, {count} items loaded - Load both to begin"
                    ))
            else:
                error_msg = parser_result.get('error', 'Unknown error')
                self.root.after(0, lambda: self._log_create(f"✗ Error loading items: {error_msg}"))
                self.root.after(0, lambda: messagebox.showerror("Error", error_msg))

        except QBConnectionError as e:
            error_str = str(e)
            self.root.after(0, lambda: self._log_create(f"✗ QB Connection Error: {error_str}"))
            self.root.after(0, lambda: messagebox.showerror("QB Connection Error", error_str))
        except Exception as e:
            error_str = str(e)
            self.root.after(0, lambda: self._log_create(f"✗ Error: {error_str}"))
            self.root.after(0, lambda: messagebox.showerror("Error", error_str))
        finally:
            self.root.after(0, lambda: self.load_items_btn.config(state='normal'))
            self.root.after(0, lambda: self.status_bar.config(text="Ready"))

    def _load_terms(self):
        """Load terms from QuickBooks (wrapper - launches background thread)."""
        # Disable button
        self.load_terms_btn.config(state='disabled')
        self.status_bar.config(text="Loading terms from QuickBooks...")

        # Launch background thread
        thread = threading.Thread(target=self._load_terms_worker, daemon=True)
        thread.start()

    def _load_terms_worker(self):
        """Worker function to load terms in background."""
        try:
            self.root.after(0, lambda: self._log_create("Loading terms from QuickBooks..."))

            # Build terms query request
            request = QBXMLBuilder.build_terms_query()

            # Send to QuickBooks
            qb = QBIPCClient()
            response_xml = qb.execute_request(request)

            # Parse response
            parser_result = QBXMLParser.parse_response(response_xml)

            if parser_result['success']:
                terms = parser_result['data']['terms']
                self.store.dispatch(set_terms(terms))

                count = len(terms)
                self.root.after(0, lambda: self._log_create(f"✓ Loaded {count} terms from QuickBooks"))
                self.root.after(0, lambda: self.terms_status_label.config(
                    text=f"{count} term{'s' if count != 1 else ''} loaded", foreground='green'
                ))
                # Update invoice terms dropdown
                term_names = ['(None)'] + [term['name'] for term in terms]
                self.root.after(0, lambda: self.invoice_terms_combo.config(values=term_names))
            else:
                error_msg = parser_result.get('error', 'Unknown error')
                self.root.after(0, lambda: self._log_create(f"✗ Error loading terms: {error_msg}"))
                self.root.after(0, lambda: messagebox.showerror("Error", error_msg))

        except QBConnectionError as e:
            error_str = str(e)
            self.root.after(0, lambda: self._log_create(f"✗ QB Connection Error: {error_str}"))
            self.root.after(0, lambda: messagebox.showerror("QB Connection Error", error_str))
        except Exception as e:
            error_str = str(e)
            self.root.after(0, lambda: self._log_create(f"✗ Error: {error_str}"))
            self.root.after(0, lambda: messagebox.showerror("Error", error_str))
        finally:
            self.root.after(0, lambda: self.load_terms_btn.config(state='normal'))
            self.root.after(0, lambda: self.status_bar.config(text="Ready"))

    def _load_classes(self):
        """Load classes from QuickBooks (wrapper - launches background thread)."""
        # Disable button
        self.load_classes_btn.config(state='disabled')
        self.status_bar.config(text="Loading classes from QuickBooks...")

        # Launch background thread
        thread = threading.Thread(target=self._load_classes_worker, daemon=True)
        thread.start()

    def _load_classes_worker(self):
        """Worker function to load classes in background."""
        try:
            self.root.after(0, lambda: self._log_create("Loading classes from QuickBooks..."))

            # Build class query request
            request = QBXMLBuilder.build_class_query()

            # Send to QuickBooks
            qb = QBIPCClient()
            response_xml = qb.execute_request(request)

            # Parse response
            parser_result = QBXMLParser.parse_response(response_xml)

            if parser_result['success']:
                classes = parser_result['data']['classes']
                self.store.dispatch(set_classes(classes))

                count = len(classes)
                self.root.after(0, lambda: self._log_create(f"✓ Loaded {count} classes from QuickBooks"))
                self.root.after(0, lambda: self.classes_status_label.config(
                    text=f"{count} class{'es' if count != 1 else ''} loaded", foreground='green'
                ))
                # Update invoice class dropdown
                class_names = ['(None)'] + [cls['full_name'] for cls in classes]
                self.root.after(0, lambda: self.invoice_class_combo.config(values=class_names))
            else:
                error_msg = parser_result.get('error', 'Unknown error')
                self.root.after(0, lambda: self._log_create(f"✗ Error loading classes: {error_msg}"))
                self.root.after(0, lambda: messagebox.showerror("Error", error_msg))

        except QBConnectionError as e:
            error_str = str(e)
            self.root.after(0, lambda: self._log_create(f"✗ QB Connection Error: {error_str}"))
            self.root.after(0, lambda: messagebox.showerror("QB Connection Error", error_str))
        except Exception as e:
            error_str = str(e)
            self.root.after(0, lambda: self._log_create(f"✗ Error: {error_str}"))
            self.root.after(0, lambda: messagebox.showerror("Error", error_str))
        finally:
            self.root.after(0, lambda: self.load_classes_btn.config(state='normal'))
            self.root.after(0, lambda: self.status_bar.config(text="Ready"))

    def _load_accounts(self):
        """Load accounts from QuickBooks (wrapper - launches background thread)."""
        # Disable button
        self.load_accounts_btn.config(state='disabled')
        self.status_bar.config(text="Loading accounts from QuickBooks...")
        self.accounts_status_label.config(text="Loading...", foreground='orange')

        # Launch background thread
        thread = threading.Thread(target=self._load_accounts_worker, daemon=True)
        thread.start()

    def _load_accounts_worker(self):
        """Worker function to load accounts in background."""
        try:
            self.root.after(0, lambda: self._log_create("Loading accounts from QuickBooks..."))

            # Build account query request (filter for deposit-type accounts)
            request = QBXMLBuilder.build_account_query()

            # Send to QuickBooks
            qb = QBIPCClient()
            response_xml = qb.execute_request(request)

            # Parse response
            parser_result = QBXMLParser.parse_response(response_xml)

            if parser_result['success']:
                # Filter for Bank accounts (typical deposit accounts)
                all_accounts = parser_result['data']['accounts']
                deposit_accounts = [acc for acc in all_accounts if acc.get('account_type') in ['Bank', 'OtherCurrentAsset']]

                self.store.dispatch(set_accounts(deposit_accounts))

                count = len(deposit_accounts)
                self.root.after(0, lambda: self._log_create(f"✓ Loaded {count} deposit accounts from QuickBooks"))
                self.root.after(0, lambda: self.accounts_status_label.config(
                    text=f"{count} account{'s' if count != 1 else ''} loaded", foreground='green'
                ))

                # Update deposit account dropdown in Monitor tab
                self.root.after(0, self._update_accounts_combo)
            else:
                error_msg = parser_result.get('error', 'Unknown error')
                self.root.after(0, lambda: self._log_create(f"✗ Error loading accounts: {error_msg}"))
                self.root.after(0, lambda: messagebox.showerror("Error", error_msg))

        except QBConnectionError as e:
            error_str = str(e)
            self.root.after(0, lambda: self._log_create(f"✗ QB Connection Error: {error_str}"))
            self.root.after(0, lambda: messagebox.showerror("QB Connection Error", error_str))
        except Exception as e:
            error_str = str(e)
            self.root.after(0, lambda: self._log_create(f"✗ Error: {error_str}"))
            self.root.after(0, lambda: messagebox.showerror("Error", error_str))
        finally:
            self.root.after(0, lambda: self.load_accounts_btn.config(state='normal'))
            self.root.after(0, lambda: self.status_bar.config(text="Ready"))

    def _load_all(self):
        """Load all data from QuickBooks (customers, items, terms, classes, accounts)."""
        # Disable Load All button
        self.load_all_btn.config(state='disabled')
        self.status_bar.config(text="Loading all data from QuickBooks...")

        # Launch background thread
        thread = threading.Thread(target=self._load_all_worker, daemon=True)
        thread.start()

    def _load_all_worker(self):
        """Worker function to load all data sequentially in background."""
        try:
            # Load customers
            self._log_create("Starting Load All...")
            self._load_customers_sync()

            # Load items
            self._load_items_sync()

            # Load terms
            self._load_terms_sync()

            # Load classes
            self._load_classes_sync()

            # Load accounts
            self._load_accounts_sync()

            self.root.after(0, lambda: self._log_create("✓ Load All complete!"))
            self.root.after(0, lambda: messagebox.showinfo("Success", "All data loaded successfully!"))

        except Exception as e:
            error_str = str(e)
            self.root.after(0, lambda: self._log_create(f"✗ Error during Load All: {error_str}"))
            self.root.after(0, lambda: messagebox.showerror("Error", error_str))
        finally:
            self.root.after(0, lambda: self.load_all_btn.config(state='normal'))
            self.root.after(0, lambda: self.status_bar.config(text="Ready"))

    def _load_customers_sync(self):
        """Synchronous version of load customers (for use in Load All)."""
        self.root.after(0, lambda: self._log_create("Loading customers..."))
        self.root.after(0, lambda: self.customers_status_label.config(text="Loading...", foreground='orange'))

        request = QBXMLBuilder.build_customer_query()
        qb = QBIPCClient()
        response_xml = qb.execute_request(request)
        parser_result = QBXMLParser.parse_response(response_xml)

        if parser_result['success']:
            customers = parser_result['data']['customers']
            # Mark as loaded (not created by app)
            for customer in customers:
                customer['created_by_app'] = False

            self.store.dispatch({'type': 'SET_CUSTOMERS', 'payload': customers})
            count = len(customers)
            self.root.after(0, lambda: self._log_create(f"✓ Loaded {count} customers"))
            # IMPORTANT: Update customer combos and build ListID map
            self.root.after(0, self._update_customer_combo)
        else:
            error_msg = parser_result.get('error', 'Unknown error')
            self.root.after(0, lambda: self._log_create(f"✗ Error loading customers: {error_msg}"))
            raise Exception(f"Error loading customers: {error_msg}")

    def _load_items_sync(self):
        """Synchronous version of load items (for use in Load All)."""
        self.root.after(0, lambda: self._log_create("Loading items..."))
        self.root.after(0, lambda: self.items_status_label.config(text="Loading...", foreground='orange'))

        request = QBXMLBuilder.build_item_query()
        qb = QBIPCClient()
        response_xml = qb.execute_request(request)
        parser_result = QBXMLParser.parse_response(response_xml)

        if parser_result['success']:
            items = parser_result['data']['items']
            self.store.dispatch(set_items(items))
            count = len(items)
            self.root.after(0, lambda: self._log_create(f"✓ Loaded {count} items"))
            self.root.after(0, lambda: self.items_status_label.config(
                text=f"{count} item{'s' if count != 1 else ''} loaded", foreground='green'))
        else:
            error_msg = parser_result.get('error', 'Unknown error')
            self.root.after(0, lambda: self._log_create(f"✗ Error loading items: {error_msg}"))
            raise Exception(f"Error loading items: {error_msg}")

    def _load_terms_sync(self):
        """Synchronous version of load terms (for use in Load All)."""
        self.root.after(0, lambda: self._log_create("Loading terms..."))
        self.root.after(0, lambda: self.terms_status_label.config(text="Loading...", foreground='orange'))

        request = QBXMLBuilder.build_terms_query()
        qb = QBIPCClient()
        response_xml = qb.execute_request(request)
        parser_result = QBXMLParser.parse_response(response_xml)

        if parser_result['success']:
            terms = parser_result['data']['terms']
            self.store.dispatch(set_terms(terms))
            count = len(terms)
            self.root.after(0, lambda: self._log_create(f"✓ Loaded {count} terms"))
            self.root.after(0, lambda: self.terms_status_label.config(
                text=f"{count} term{'s' if count != 1 else ''} loaded", foreground='green'))
            # IMPORTANT: Update invoice terms dropdown
            term_names = ['(None)'] + [term['name'] for term in terms]
            self.root.after(0, lambda: self.invoice_terms_combo.config(values=term_names))
        else:
            error_msg = parser_result.get('error', 'Unknown error')
            self.root.after(0, lambda: self._log_create(f"✗ Error loading terms: {error_msg}"))
            raise Exception(f"Error loading terms: {error_msg}")

    def _load_classes_sync(self):
        """Synchronous version of load classes (for use in Load All)."""
        self.root.after(0, lambda: self._log_create("Loading classes..."))
        self.root.after(0, lambda: self.classes_status_label.config(text="Loading...", foreground='orange'))

        request = QBXMLBuilder.build_class_query()
        qb = QBIPCClient()
        response_xml = qb.execute_request(request)
        parser_result = QBXMLParser.parse_response(response_xml)

        if parser_result['success']:
            classes = parser_result['data']['classes']
            self.store.dispatch(set_classes(classes))
            count = len(classes)
            self.root.after(0, lambda: self._log_create(f"✓ Loaded {count} classes"))
            self.root.after(0, lambda: self.classes_status_label.config(
                text=f"{count} class{'es' if count != 1 else ''} loaded", foreground='green'))
            # Update invoice class dropdown
            class_names = ['(None)'] + [cls['full_name'] for cls in classes]
            self.root.after(0, lambda: self.invoice_class_combo.config(values=class_names))
        else:
            error_msg = parser_result.get('error', 'Unknown error')
            self.root.after(0, lambda: self._log_create(f"✗ Error loading classes: {error_msg}"))
            raise Exception(f"Error loading classes: {error_msg}")

    def _load_accounts_sync(self):
        """Synchronous version of load accounts (for use in Load All)."""
        self.root.after(0, lambda: self._log_create("Loading accounts..."))
        self.root.after(0, lambda: self.accounts_status_label.config(text="Loading...", foreground='orange'))

        request = QBXMLBuilder.build_account_query()
        qb = QBIPCClient()
        response_xml = qb.execute_request(request)
        parser_result = QBXMLParser.parse_response(response_xml)

        if parser_result['success']:
            all_accounts = parser_result['data']['accounts']
            deposit_accounts = [acc for acc in all_accounts if acc.get('account_type') in ['Bank', 'OtherCurrentAsset']]
            self.store.dispatch(set_accounts(deposit_accounts))
            count = len(deposit_accounts)
            self.root.after(0, lambda: self._log_create(f"✓ Loaded {count} deposit accounts"))
            self.root.after(0, lambda: self.accounts_status_label.config(
                text=f"{count} account{'s' if count != 1 else ''} loaded", foreground='green'))
            # Update deposit account dropdown
            self.root.after(0, self._update_accounts_combo)
        else:
            error_msg = parser_result.get('error', 'Unknown error')
            self.root.after(0, lambda: self._log_create(f"✗ Error loading accounts: {error_msg}"))
            raise Exception(f"Error loading accounts: {error_msg}")

    def _load_customers(self):
        """Load customers from QuickBooks (wrapper - launches background thread)."""
        # Disable button
        self.load_customers_btn.config(state='disabled')
        self.status_bar.config(text="Loading customers from QuickBooks...")

        # Launch background thread
        thread = threading.Thread(target=self._load_customers_worker, daemon=True)
        thread.start()

    def _load_customers_worker(self):
        """Worker function to load customers in background."""
        try:
            self.root.after(0, lambda: self._log_create("Loading customers from QuickBooks..."))

            # Build customer query request
            request = QBXMLBuilder.build_customer_query()

            # Send to QuickBooks
            qb = QBIPCClient()
            response_xml = qb.execute_request(request)

            # Parse response
            parser_result = QBXMLParser.parse_response(response_xml)

            if parser_result['success']:
                loaded_customers = parser_result['data']['customers']

                # Get current state and merge loaded customers with created ones
                state = self.store.get_state()

                # Add loaded customers to store (will replace existing list)
                # But we need to preserve created customers too
                all_customers = loaded_customers + [c for c in state.customers if c.get('created_by_app')]

                # For now, just replace with loaded customers
                # Mark them as loaded (not created by app)
                for customer in loaded_customers:
                    customer['created_by_app'] = False

                self.store.dispatch({'type': 'SET_CUSTOMERS', 'payload': loaded_customers})

                count = len(loaded_customers)
                self.root.after(0, lambda: self._log_create(f"✓ Loaded {count} customers from QuickBooks"))
                self.root.after(0, self._update_customer_combo)
            else:
                error_msg = parser_result.get('error', 'Unknown error')
                self.root.after(0, lambda: self._log_create(f"✗ Error loading customers: {error_msg}"))
                self.root.after(0, lambda: messagebox.showerror("Error", error_msg))

        except QBConnectionError as e:
            error_str = str(e)
            self.root.after(0, lambda: self._log_create(f"✗ QB Connection Error: {error_str}"))
            self.root.after(0, lambda: messagebox.showerror("QB Connection Error", error_str))
        except Exception as e:
            error_str = str(e)
            self.root.after(0, lambda: self._log_create(f"✗ Error: {error_str}"))
            self.root.after(0, lambda: messagebox.showerror("Error", error_str))
        finally:
            self.root.after(0, lambda: self.load_customers_btn.config(state='normal'))
            self.root.after(0, lambda: self.status_bar.config(text="Ready"))

    def _create_invoice(self):
        """Create invoices in QuickBooks (batch wrapper - launches background thread)."""
        if not self.customer_combo.get():
            messagebox.showerror("Error", "Please select a customer!")
            return

        try:
            # Get selected customer and parameters
            state = self.store.get_state()

            # Check if items are loaded
            if not state.items:
                messagebox.showerror("Error", "Please load items from QuickBooks first!\n\nClick 'Load Items from QB' button.")
                return

            # Get customer by ListID (not index) to avoid mismatch with nested jobs
            selected_display_name = self.customer_combo.get()
            customer_list_id = self.customer_listid_map.get(selected_display_name)
            if not customer_list_id:
                messagebox.showerror("Error", "Selected customer not found. Please reload customers.")
                return

            # Find customer by ListID
            customer = next((c for c in state.customers if c['list_id'] == customer_list_id), None)
            if not customer:
                messagebox.showerror("Error", "Customer data not found. Please reload customers.")
                return

            # Get batch parameters
            num_invoices = int(self.num_invoices.get())
            line_items_min = int(self.num_lines_min.get())
            line_items_max = int(self.num_lines_max.get())
            amount_min = float(self.amount_min.get())
            amount_max = float(self.amount_max.get())
            date_range = self.invoice_date_range.get()

            # Get optional fields
            po_prefix = self.invoice_po_prefix.get().strip()
            if not po_prefix:
                po_prefix = None  # Don't use empty string

            # Get selected terms and look up list_id
            terms_ref = None
            selected_terms = self.invoice_terms_combo.get()
            if selected_terms and selected_terms != '(None)':
                # Find the terms in state by name
                for term in state.terms:
                    if term['name'] == selected_terms:
                        terms_ref = term['list_id']
                        break

            # Get selected class and look up list_id
            class_ref = None
            selected_class = self.invoice_class_combo.get()
            if selected_class and selected_class != '(None)':
                # Find the class in state by full_name
                for cls in state.classes:
                    if cls['full_name'] == selected_class:
                        class_ref = cls['list_id']
                        break

            # Validate ranges
            if line_items_max < line_items_min:
                messagebox.showerror("Error", "Line items max must be >= min")
                return
            if amount_max < amount_min:
                messagebox.showerror("Error", "Amount max must be >= min")
                return

            # Disable button and update status
            self.create_invoice_btn.config(state='disabled')
            plural = "s" if num_invoices > 1 else ""
            self.status_bar.config(text=f"Creating {num_invoices} invoice{plural}...")

            # Launch background thread
            thread = threading.Thread(
                target=self._create_invoice_worker,
                args=(customer, num_invoices, line_items_min, line_items_max,
                      amount_min, amount_max, date_range, state.items,
                      po_prefix, terms_ref, class_ref),
                daemon=True
            )
            thread.start()

        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")

    def _create_invoice_worker(self, customer: dict, num_invoices: int,
                              line_items_min: int, line_items_max: int,
                              amount_min: float, amount_max: float, date_range: str, items: list,
                              po_prefix: str = None, terms_ref: str = None, class_ref: str = None):
        """Worker function to create batch invoices in background."""
        successful_count = 0
        failed_count = 0

        try:
            import random
            from datetime import timedelta

            # Calculate date range based on selection
            today = datetime.now()
            if date_range == 'Today Only':
                days_back = 0
            elif date_range == 'Last 7 Days':
                days_back = 7
            elif date_range == 'Last 30 Days':
                days_back = 30
            else:
                days_back = 0  # Default to today

            self.root.after(0, lambda: self._log_create(f"Starting batch creation of {num_invoices} invoice(s) for {customer['name']} ({date_range})..."))

            # Create multiple invoices
            for i in range(num_invoices):
                try:
                    # Randomize parameters within specified ranges
                    num_lines = random.randint(line_items_min, line_items_max)
                    amount = round(random.uniform(amount_min, amount_max), 2)

                    # Randomize transaction date within range
                    if days_back > 0:
                        random_days = random.randint(0, days_back)
                        txn_date = (today - timedelta(days=random_days)).strftime('%Y-%m-%d')
                    else:
                        txn_date = today.strftime('%Y-%m-%d')

                    # Select random items for invoice line items
                    selected_items = random.sample(items, min(num_lines, len(items)))
                    item_refs = [item['list_id'] for item in selected_items]

                    # Generate invoice data
                    invoice_data = TestDataGenerator.generate_invoice_data(
                        customer_ref=customer['list_id'],
                        num_line_items=num_lines,
                        total_amount=amount,
                        item_refs=item_refs,
                        txn_date=txn_date,
                        po_prefix=po_prefix,
                        terms_ref=terms_ref,
                        class_ref=class_ref
                    )

                    # Log current progress
                    invoice_num = i + 1
                    self.root.after(0, lambda n=invoice_num, ref=invoice_data['ref_number']:
                                  self._log_create(f"[{n}/{num_invoices}] Creating invoice Ref#: {ref}, Amount: ${amount:.2f}, Lines: {num_lines}"))

                    # Build QBXML request
                    request = QBXMLBuilder.build_invoice_add(invoice_data)

                    # DEBUG: Log the XML request
                    self.root.after(0, lambda n=invoice_num, xml=request:
                                  self._log_create(f"  [DEBUG {n}] QBXML Request:\n{xml}"))

                    # Send to QuickBooks
                    qb = QBIPCClient()
                    response_xml = qb.execute_request(request)

                    # DEBUG: Log the XML response
                    self.root.after(0, lambda n=invoice_num, xml=response_xml:
                                  self._log_create(f"  [DEBUG {n}] QBXML Response:\n{xml}"))

                    # Parse response
                    parser_result = QBXMLParser.parse_response(response_xml)

                    if parser_result['success']:
                        invoice_info = parser_result['data']

                        # Create invoice record
                        invoice_record = InvoiceRecord(
                            txn_id=invoice_info['txn_id'],
                            ref_number=invoice_info['ref_number'],
                            customer_name=customer['name'],
                            amount=float(invoice_info['balance_remaining']),
                            status='open' if not invoice_info['is_paid'] else 'closed',
                            created_at=datetime.now()
                        )

                        self.store.dispatch(add_invoice(invoice_record))
                        self.root.after(0, lambda n=invoice_num, ref=invoice_info['ref_number'], tid=invoice_info['txn_id']:
                                      self._log_create(f"  ✓ [{n}/{num_invoices}] Invoice created: {ref} (ID: {tid})"))
                        self.root.after(0, self._update_invoice_tree)
                        successful_count += 1

                    else:
                        error_msg = parser_result.get('error', 'Unknown error')
                        self.root.after(0, lambda n=invoice_num, msg=error_msg:
                                      self._log_create(f"  ✗ [{n}/{num_invoices}] Error: {msg}"))
                        failed_count += 1

                except Exception as e:
                    error_str = str(e)
                    invoice_num = i + 1
                    self.root.after(0, lambda n=invoice_num, msg=error_str:
                                  self._log_create(f"  ✗ [{n}/{num_invoices}] Error: {msg}"))
                    failed_count += 1

            # Final summary
            summary = f"Batch complete: {successful_count} succeeded, {failed_count} failed out of {num_invoices} total"
            self.root.after(0, lambda s=summary: self._log_create(f"\n{s}"))

            if failed_count > 0 and successful_count > 0:
                self.root.after(0, lambda: messagebox.showwarning("Batch Complete", summary))
            elif failed_count > 0:
                self.root.after(0, lambda: messagebox.showerror("Batch Failed", summary))
            else:
                self.root.after(0, lambda: messagebox.showinfo("Batch Complete", summary))

        except Exception as e:
            error_str = str(e)
            self.root.after(0, lambda: self._log_create(f"✗ Batch error: {error_str}"))
            self.root.after(0, lambda: messagebox.showerror("Error", error_str))
        finally:
            # Re-enable button and update status
            self.root.after(0, lambda: self.create_invoice_btn.config(state='normal'))
            self.root.after(0, lambda: self.status_bar.config(text="Ready"))

    def _create_sales_receipt(self):
        """Create sales receipt(s) in batch."""
        state = self.store.get_state()

        # Validate customer selection
        if not self.sr_customer_combo.get():
            messagebox.showerror("Error", "Please select a customer first!")
            return

        if not state.items:
            messagebox.showerror("Error", "Please load items from QB first!")
            return

        # Get customer by ListID (not index) to avoid mismatch with nested jobs
        selected_display_name = self.sr_customer_combo.get()
        customer_list_id = self.customer_listid_map.get(selected_display_name)
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
            num_receipts = int(self.num_sales_receipts.get())
            line_items_min = int(self.num_sr_lines_min.get())
            line_items_max = int(self.num_sr_lines_max.get())
            amount_min = float(self.sr_amount_min.get())
            amount_max = float(self.sr_amount_max.get())
            date_range = self.sr_date_range.get()

            if line_items_min > line_items_max:
                raise ValueError("Line items min cannot be greater than max")
            if amount_min > amount_max:
                raise ValueError("Amount min cannot be greater than max")
            if num_receipts < 1:
                raise ValueError("Number of sales receipts must be at least 1")

        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")
            return

        # Disable button and update status
        self.create_sales_receipt_btn.config(state='disabled')
        self.status_bar.config(text="Creating sales receipts...")

        # Start worker thread
        thread = threading.Thread(
            target=self._create_sales_receipt_worker,
            args=(customer, num_receipts, line_items_min, line_items_max,
                  amount_min, amount_max, date_range, state.items),
            daemon=True
        )
        thread.start()

    def _create_sales_receipt_worker(self, customer: dict, num_receipts: int,
                                     line_items_min: int, line_items_max: int,
                                     amount_min: float, amount_max: float, date_range: str, items: list):
        """Worker function to create batch sales receipts in background."""
        successful_count = 0
        failed_count = 0

        try:
            import random
            from datetime import timedelta

            # Calculate date range based on selection
            today = datetime.now()
            if date_range == 'Today Only':
                days_back = 0
            elif date_range == 'Last 7 Days':
                days_back = 7
            elif date_range == 'Last 30 Days':
                days_back = 30
            else:
                days_back = 0  # Default to today

            self.root.after(0, lambda: self._log_create(f"Starting batch creation of {num_receipts} sales receipt(s) for {customer['name']} ({date_range})..."))

            # Create multiple sales receipts
            for i in range(num_receipts):
                try:
                    # Randomize parameters within specified ranges
                    num_lines = random.randint(line_items_min, line_items_max)
                    amount = round(random.uniform(amount_min, amount_max), 2)

                    # Randomize transaction date within range
                    if days_back > 0:
                        random_days = random.randint(0, days_back)
                        txn_date = (today - timedelta(days=random_days)).strftime('%Y-%m-%d')
                    else:
                        txn_date = today.strftime('%Y-%m-%d')

                    # Select random items for sales receipt line items
                    selected_items = random.sample(items, min(num_lines, len(items)))
                    item_refs = [item['list_id'] for item in selected_items]

                    # Generate sales receipt data
                    receipt_data = TestDataGenerator.generate_sales_receipt_data(
                        customer_ref=customer['list_id'],
                        num_line_items=num_lines,
                        total_amount=amount,
                        item_refs=item_refs,
                        txn_date=txn_date
                    )

                    # Log current progress
                    receipt_num = i + 1
                    self.root.after(0, lambda n=receipt_num, ref=receipt_data['ref_number']:
                                  self._log_create(f"[{n}/{num_receipts}] Creating sales receipt Ref#: {ref}, Amount: ${amount:.2f}, Lines: {num_lines}"))

                    # Build QBXML request
                    request = QBXMLBuilder.build_sales_receipt_add(receipt_data)

                    # DEBUG: Log the XML request
                    receipt_num = i + 1
                    self.root.after(0, lambda n=receipt_num, xml=request:
                                  self._log_create(f"  [DEBUG {n}] QBXML Request:\n{xml}"))

                    # Send to QuickBooks
                    qb = QBIPCClient()
                    response_xml = qb.execute_request(request)

                    # DEBUG: Log the XML response
                    self.root.after(0, lambda n=receipt_num, xml=response_xml:
                                  self._log_create(f"  [DEBUG {n}] QBXML Response:\n{xml}"))

                    # Parse response
                    parser_result = QBXMLParser.parse_response(response_xml)

                    if parser_result['success']:
                        receipt_info = parser_result['data']

                        # Create sales receipt record
                        # Safely extract amounts (handle None values)
                        balance_remaining = receipt_info.get('balance_remaining')
                        total_amount_str = receipt_info.get('total_amount')

                        # Convert to float, defaulting to the generated amount if not in response
                        if balance_remaining:
                            balance = float(balance_remaining)
                        else:
                            balance = amount  # Default to generated amount

                        if total_amount_str:
                            total_amt = float(total_amount_str)
                        else:
                            total_amt = amount  # Default to generated amount

                        # Determine status - if no balance_remaining, assume open (unpaid)
                        status = 'open' if balance > 0 else 'closed'

                        receipt_record = SalesReceiptRecord(
                            txn_id=receipt_info['txn_id'],
                            ref_number=receipt_info['ref_number'],
                            customer_name=customer['name'],
                            amount=total_amt,
                            status=status,
                            created_at=datetime.now()
                        )

                        self.store.dispatch(add_sales_receipt(receipt_record))
                        self.root.after(0, lambda n=receipt_num, ref=receipt_info['ref_number'], tid=receipt_info['txn_id']:
                                      self._log_create(f"  ✓ [{n}/{num_receipts}] Sales receipt created: {ref} (ID: {tid})"))
                        successful_count += 1

                    else:
                        error_msg = parser_result.get('error', 'Unknown error')
                        self.root.after(0, lambda n=receipt_num, msg=error_msg:
                                      self._log_create(f"  ✗ [{n}/{num_receipts}] Error: {msg}"))
                        failed_count += 1

                except Exception as e:
                    error_str = str(e)
                    receipt_num = i + 1
                    self.root.after(0, lambda n=receipt_num, msg=error_str:
                                  self._log_create(f"  ✗ [{n}/{num_receipts}] Error: {msg}"))
                    failed_count += 1

            # Final summary
            summary = f"Batch complete: {successful_count} succeeded, {failed_count} failed out of {num_receipts} total"
            self.root.after(0, lambda s=summary: self._log_create(f"\n{s}"))

            if failed_count > 0 and successful_count > 0:
                self.root.after(0, lambda: messagebox.showwarning("Batch Complete", summary))
            elif failed_count > 0:
                self.root.after(0, lambda: messagebox.showerror("Batch Failed", summary))
            else:
                self.root.after(0, lambda: messagebox.showinfo("Batch Complete", summary))

        except Exception as e:
            error_str = str(e)
            self.root.after(0, lambda: self._log_create(f"✗ Batch error: {error_str}"))
            self.root.after(0, lambda: messagebox.showerror("Error", error_str))
        finally:
            # Re-enable button and update status
            self.root.after(0, lambda: self.create_sales_receipt_btn.config(state='normal'))
            self.root.after(0, lambda: self.status_bar.config(text="Ready"))

    def _query_sales_receipt(self):
        """Query a sales receipt by TxnID to debug visibility issue."""
        txn_id = self.query_txn_id.get().strip()

        if not txn_id:
            messagebox.showerror("Error", "Please enter a TxnID to query!")
            return

        # Disable button and update status
        self.query_sr_btn.config(state='disabled')
        self.status_bar.config(text="Querying sales receipt...")

        # Start worker thread
        thread = threading.Thread(
            target=self._query_sales_receipt_worker,
            args=(txn_id,),
            daemon=True
        )
        thread.start()

    def _query_sales_receipt_worker(self, txn_id: str):
        """Worker function to query sales receipt in background."""
        try:
            self.root.after(0, lambda: self._log_create(f"Querying sales receipt TxnID: {txn_id}"))

            # Build QBXML query request
            request = QBXMLBuilder.build_sales_receipt_query(txn_id=txn_id)

            # DEBUG: Log the XML request
            self.root.after(0, lambda xml=request:
                          self._log_create(f"  [DEBUG] Query Request:\n{xml}"))

            # Send to QuickBooks
            qb = QBIPCClient()
            response_xml = qb.execute_request(request)

            # DEBUG: Log the XML response
            self.root.after(0, lambda xml=response_xml:
                          self._log_create(f"  [DEBUG] Query Response:\n{xml}"))

            # Parse response
            parser_result = QBXMLParser.parse_response(response_xml)

            if parser_result['success']:
                receipts = parser_result['data'].get('sales_receipts', [])

                if receipts:
                    receipt = receipts[0]
                    self.root.after(0, lambda: self._log_create(f"✓ Sales receipt found!"))
                    self.root.after(0, lambda: self._log_create(f"  Ref#: {receipt.get('ref_number')}"))
                    self.root.after(0, lambda: self._log_create(f"  Customer: {receipt.get('customer_ref', {}).get('full_name')}"))
                    self.root.after(0, lambda: self._log_create(f"  Total: ${receipt.get('total_amount', 0):.2f}"))
                    self.root.after(0, lambda: self._log_create(f"  IsPending: {receipt.get('is_pending')}"))
                    self.root.after(0, lambda: self._log_create(f"  IsToBePrinted: {receipt.get('is_to_be_printed')}"))
                    self.root.after(0, lambda: self._log_create(f"  IsToBeEmailed: {receipt.get('is_to_be_emailed')}"))
                    self.root.after(0, lambda: self._log_create(f"  TimeCreated: {receipt.get('time_created')}"))
                    self.root.after(0, lambda: self._log_create(f"  TimeModified: {receipt.get('time_modified')}"))

                    if 'deposit_account' in receipt:
                        self.root.after(0, lambda: self._log_create(f"  DepositTo: {receipt['deposit_account'].get('full_name')}"))
                else:
                    self.root.after(0, lambda: self._log_create(f"✗ Sales receipt NOT FOUND in QB!"))
                    self.root.after(0, lambda: messagebox.showwarning("Not Found",
                        "Sales receipt with this TxnID was not found in QuickBooks database!"))

            else:
                error_msg = parser_result.get('error', 'Unknown error')
                self.root.after(0, lambda: self._log_create(f"✗ Error: {error_msg}"))
                self.root.after(0, lambda: messagebox.showerror("Error", error_msg))

        except Exception as e:
            error_str = str(e)
            self.root.after(0, lambda: self._log_create(f"✗ Error: {error_str}"))
            self.root.after(0, lambda: messagebox.showerror("Error", error_str))
        finally:
            # Re-enable button and update status
            self.root.after(0, lambda: self.query_sr_btn.config(state='normal'))
            self.root.after(0, lambda: self.status_bar.config(text="Ready"))

    def _create_charge(self):
        """Create statement charge(s) in batch."""
        state = self.store.get_state()

        # Validate customer selection
        if not self.charge_customer_combo.get():
            messagebox.showerror("Error", "Please select a customer first!")
            return

        if not state.items:
            messagebox.showerror("Error", "Please load items from QB first!")
            return

        # Get customer by ListID (not index) to avoid mismatch with nested jobs
        selected_display_name = self.charge_customer_combo.get()
        customer_list_id = self.customer_listid_map.get(selected_display_name)
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
            num_charges = int(self.num_charges.get())
            amount_min = float(self.charge_amount_min.get())
            amount_max = float(self.charge_amount_max.get())
            date_range = self.charge_date_range.get()

            if amount_min > amount_max:
                raise ValueError("Amount min cannot be greater than max")
            if num_charges < 1:
                raise ValueError("Number of charges must be at least 1")

        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")
            return

        # Disable button and update status
        self.create_charge_btn.config(state='disabled')
        self.status_bar.config(text="Creating statement charges...")

        # Start worker thread
        thread = threading.Thread(
            target=self._create_charge_worker,
            args=(customer, num_charges, amount_min, amount_max, date_range, state.items),
            daemon=True
        )
        thread.start()

    def _create_charge_worker(self, customer: dict, num_charges: int,
                              amount_min: float, amount_max: float, date_range: str, items: list):
        """Worker function to create batch statement charges in background."""
        successful_count = 0
        failed_count = 0

        try:
            import random
            from datetime import timedelta

            # Calculate date range based on selection
            today = datetime.now()
            if date_range == 'Today Only':
                days_back = 0
            elif date_range == 'Last 7 Days':
                days_back = 7
            elif date_range == 'Last 30 Days':
                days_back = 30
            else:
                days_back = 0  # Default to today

            self.root.after(0, lambda: self._log_create(f"Starting batch creation of {num_charges} statement charge(s) for {customer['name']} ({date_range})..."))

            # Select a random item to use for all charges
            # For statement charges, we typically use a generic service item
            charge_item = random.choice(items) if items else None

            # Create multiple statement charges
            for i in range(num_charges):
                try:
                    # Randomize amount within specified range
                    amount = round(random.uniform(amount_min, amount_max), 2)

                    # Randomize transaction date within range
                    if days_back > 0:
                        random_days = random.randint(0, days_back)
                        txn_date = (today - timedelta(days=random_days)).strftime('%Y-%m-%d')
                    else:
                        txn_date = today.strftime('%Y-%m-%d')

                    # Generate charge data
                    charge_data = TestDataGenerator.generate_statement_charge_data(
                        customer_ref=customer['list_id'],
                        amount=amount,
                        item_ref=charge_item['list_id'] if charge_item else None,
                        txn_date=txn_date
                    )

                    # Log current progress
                    charge_num = i + 1
                    self.root.after(0, lambda n=charge_num, amt=amount:
                                  self._log_create(f"[{n}/{num_charges}] Creating statement charge: Amount: ${amt:.2f}"))

                    # Build QBXML request
                    request = QBXMLBuilder.build_charge_add(charge_data)

                    # DEBUG: Log the XML request
                    self.root.after(0, lambda n=charge_num, xml=request:
                                  self._log_create(f"  [DEBUG {n}] QBXML Request:\n{xml}"))

                    # Send to QuickBooks
                    qb = QBIPCClient()
                    response_xml = qb.execute_request(request)

                    # DEBUG: Log the XML response
                    self.root.after(0, lambda n=charge_num, xml=response_xml:
                                  self._log_create(f"  [DEBUG {n}] QBXML Response:\n{xml}"))

                    # Parse response
                    parser_result = QBXMLParser.parse_response(response_xml)

                    if parser_result['success']:
                        charge_info = parser_result['data']

                        self.root.after(0, lambda n=charge_num, tid=charge_info['txn_id'], amt=charge_info.get('amount', amount):
                                      self._log_create(f"  ✓ [{n}/{num_charges}] Statement charge created: ${amt} (ID: {tid})"))
                        successful_count += 1

                    else:
                        error_msg = parser_result.get('error', 'Unknown error')
                        self.root.after(0, lambda n=charge_num, msg=error_msg:
                                      self._log_create(f"  ✗ [{n}/{num_charges}] Error: {msg}"))
                        failed_count += 1

                except Exception as e:
                    error_str = str(e)
                    charge_num = i + 1
                    self.root.after(0, lambda n=charge_num, msg=error_str:
                                  self._log_create(f"  ✗ [{n}/{num_charges}] Error: {msg}"))
                    failed_count += 1

            # Final summary
            summary = f"Batch complete: {successful_count} succeeded, {failed_count} failed out of {num_charges} total"
            self.root.after(0, lambda s=summary: self._log_create(f"\n{s}"))

            if failed_count > 0 and successful_count > 0:
                self.root.after(0, lambda: messagebox.showwarning("Batch Complete", summary))
            elif failed_count > 0:
                self.root.after(0, lambda: messagebox.showerror("Batch Failed", summary))
            else:
                self.root.after(0, lambda: messagebox.showinfo("Batch Complete", summary))

        except Exception as e:
            error_str = str(e)
            self.root.after(0, lambda: self._log_create(f"✗ Batch error: {error_str}"))
            self.root.after(0, lambda: messagebox.showerror("Error", error_str))
        finally:
            # Re-enable button and update status
            self.root.after(0, lambda: self.create_charge_btn.config(state='normal'))
            self.root.after(0, lambda: self.status_bar.config(text="Ready"))

    def _set_expected_deposit_account(self):
        """Set the expected deposit account for validation."""
        account_name = self.expected_deposit_account_combo.get().strip()
        if account_name:
            self.store.dispatch(set_expected_deposit_account(account_name))
            messagebox.showinfo("Success", f"Expected deposit account set to: {account_name}")
        else:
            self.store.dispatch(set_expected_deposit_account(None))
            messagebox.showinfo("Info", "Expected deposit account cleared")

    def _clear_search(self):
        """Clear all search fields."""
        self.search_text.delete(0, tk.END)
        self.search_txn_id.delete(0, tk.END)
        self.search_date_from.delete(0, tk.END)
        self.search_date_to.delete(0, tk.END)
        self.search_amount_min.delete(0, tk.END)
        self.search_amount_max.delete(0, tk.END)
        self.search_txn_type.set('All')

    def _search_transactions(self):
        """Search transactions based on search criteria."""
        # Get search parameters
        search_text = self.search_text.get().strip().lower()
        txn_id = self.search_txn_id.get().strip()
        txn_type = self.search_txn_type.get()
        date_from = self.search_date_from.get().strip()
        date_to = self.search_date_to.get().strip()
        amount_min = self.search_amount_min.get().strip()
        amount_max = self.search_amount_max.get().strip()
        display_mode = self.search_display_mode.get()
        search_all_qb = self.search_scope_var.get()

        # Validate date format if provided
        if date_from and not self._validate_date_format(date_from):
            messagebox.showerror("Error", "Invalid 'Date From' format. Use YYYY-MM-DD")
            return
        if date_to and not self._validate_date_format(date_to):
            messagebox.showerror("Error", "Invalid 'Date To' format. Use YYYY-MM-DD")
            return

        # Validate amount format if provided
        try:
            amount_min_float = float(amount_min) if amount_min else None
            amount_max_float = float(amount_max) if amount_max else None
        except ValueError:
            messagebox.showerror("Error", "Invalid amount format. Use numeric values.")
            return

        # Build date range filter
        txn_date_range = {}
        if date_from:
            txn_date_range['from_txn_date'] = date_from
        if date_to:
            txn_date_range['to_txn_date'] = date_to

        # Execute search
        if search_all_qb:
            # Search all QB transactions in background thread
            threading.Thread(
                target=self._execute_search_query,
                args=(txn_id, search_text, txn_type, txn_date_range, amount_min_float, amount_max_float, display_mode),
                daemon=True
            ).start()
            self._log_monitor("Executing search query on all QB transactions...")
        else:
            # Search monitored transactions (no thread needed, it's fast)
            self._search_monitored_transactions(search_text, txn_id, txn_type, date_from, date_to,
                                               amount_min_float, amount_max_float, display_mode)

    def _search_monitored_transactions(self, search_text: str, txn_id: str, txn_type: str,
                                       date_from: str, date_to: str, amount_min: float,
                                       amount_max: float, display_mode: str):
        """Search monitored transactions from Redux store."""
        state = self.store.get_state()
        results = []

        # Determine which transaction types to search
        query_types = []
        if txn_type == 'All':
            query_types = ['Invoices', 'Sales Receipts', 'Statement Charges']
        else:
            query_types = [txn_type]

        # Search invoices
        if 'Invoices' in query_types:
            for inv in state.invoices:
                result = {
                    'type': 'Invoice',
                    'txn_id': inv.txn_id,
                    'ref_number': inv.ref_number,
                    'customer_name': inv.customer_name,
                    'amount': inv.amount,
                    'status': inv.status,
                    'txn_date': inv.created_at.strftime('%Y-%m-%d') if inv.created_at else ''
                }
                if self._match_search_criteria(result, search_text, txn_id, date_from, date_to,
                                               amount_min, amount_max):
                    results.append(result)

        # Search sales receipts
        if 'Sales Receipts' in query_types:
            for sr in state.sales_receipts:
                result = {
                    'type': 'Sales Receipt',
                    'txn_id': sr.txn_id,
                    'ref_number': sr.ref_number,
                    'customer_name': sr.customer_name,
                    'amount': sr.amount,
                    'status': sr.status,
                    'txn_date': sr.created_at.strftime('%Y-%m-%d') if sr.created_at else ''
                }
                if self._match_search_criteria(result, search_text, txn_id, date_from, date_to,
                                               amount_min, amount_max):
                    results.append(result)

        # Search statement charges
        if 'Statement Charges' in query_types:
            for charge in state.statement_charges:
                result = {
                    'type': 'Statement Charge',
                    'txn_id': charge.txn_id,
                    'ref_number': charge.ref_number,
                    'customer_name': charge.customer_name,
                    'amount': charge.amount,
                    'status': charge.status,
                    'txn_date': charge.created_at.strftime('%Y-%m-%d') if charge.created_at else ''
                }
                if self._match_search_criteria(result, search_text, txn_id, date_from, date_to,
                                               amount_min, amount_max):
                    results.append(result)

        # Display results
        self._display_search_results(results, display_mode)
        self._log_monitor(f"Search complete: {len(results)} monitored transaction(s) found")

    def _match_search_criteria(self, result: dict, search_text: str, txn_id: str,
                               date_from: str, date_to: str, amount_min: float,
                               amount_max: float) -> bool:
        """Check if a transaction matches search criteria."""
        # Filter by transaction ID
        if txn_id and result.get('txn_id', '') != txn_id:
            return False

        # Filter by customer name or ref number
        if search_text:
            customer_name = result.get('customer_name', '').lower()
            ref_number = result.get('ref_number', '').lower()
            if search_text not in customer_name and search_text not in ref_number:
                return False

        # Filter by date range
        txn_date = result.get('txn_date', '')
        if date_from and txn_date < date_from:
            return False
        if date_to and txn_date > date_to:
            return False

        # Filter by amount range
        amount = float(result.get('amount', 0))
        if amount_min is not None and amount < amount_min:
            return False
        if amount_max is not None and amount > amount_max:
            return False

        return True

    def _validate_date_format(self, date_str: str) -> bool:
        """Validate date format (YYYY-MM-DD)."""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def _execute_search_query(self, txn_id: str, search_text: str, txn_type: str,
                              txn_date_range: dict, amount_min: float, amount_max: float,
                              display_mode: str):
        """Execute the actual search query in background thread."""
        try:
            results = []

            # Determine which transaction types to query
            query_types = []
            if txn_type == 'All':
                query_types = ['Invoices', 'Sales Receipts', 'Statement Charges']
            else:
                query_types = [txn_type]

            # Query each type
            for qtype in query_types:
                if qtype == 'Invoices':
                    results.extend(self._query_invoices(txn_id, txn_date_range))
                elif qtype == 'Sales Receipts':
                    results.extend(self._query_sales_receipts(txn_id, txn_date_range))
                elif qtype == 'Statement Charges':
                    results.extend(self._query_statement_charges(txn_id, txn_date_range))

            # Filter results based on search criteria
            filtered_results = self._filter_search_results(
                results, search_text, amount_min, amount_max
            )

            # Display results based on mode
            self.root.after(0, lambda: self._display_search_results(filtered_results, display_mode))

        except Exception as e:
            error_msg = f"Search error: {str(e)}"
            self.root.after(0, lambda: self._log_monitor(error_msg))
            self.root.after(0, lambda: messagebox.showerror("Search Error", error_msg))
        finally:
            pass

    def _query_invoices(self, txn_id: str, txn_date_range: dict) -> list:
        """Query invoices from QuickBooks."""
        request = QBXMLBuilder.build_invoice_query(
            txn_id=txn_id if txn_id else None,
            txn_date_range=txn_date_range if txn_date_range else None,
            max_returned=100
        )
        response = QBIPCClient.execute_request(request)
        parser_result = QBXMLParser.parse_response(response)

        if parser_result['success'] and 'invoices' in parser_result['data']:
            invoices = parser_result['data']['invoices']
            results = []
            for inv in invoices:
                # Transform to expected format
                results.append({
                    'type': 'Invoice',
                    'txn_id': inv.get('txn_id', ''),
                    'ref_number': inv.get('ref_number', ''),
                    'customer_name': inv.get('customer_ref', {}).get('full_name', ''),
                    'amount': float(inv.get('subtotal', 0)),
                    'status': 'Paid' if inv.get('is_paid') else 'Open',
                    'txn_date': inv.get('txn_date', '')
                })
            return results
        return []

    def _query_sales_receipts(self, txn_id: str, txn_date_range: dict) -> list:
        """Query sales receipts from QuickBooks."""
        request = QBXMLBuilder.build_sales_receipt_query(
            txn_id=txn_id if txn_id else None,
            txn_date_range=txn_date_range if txn_date_range else None,
            max_returned=100
        )
        response = QBIPCClient.execute_request(request)
        parser_result = QBXMLParser.parse_response(response)

        if parser_result['success'] and 'sales_receipts' in parser_result['data']:
            receipts = parser_result['data']['sales_receipts']
            results = []
            for sr in receipts:
                # Transform to expected format
                results.append({
                    'type': 'Sales Receipt',
                    'txn_id': sr.get('txn_id', ''),
                    'ref_number': sr.get('ref_number', ''),
                    'customer_name': sr.get('customer_ref', {}).get('full_name', ''),
                    'amount': float(sr.get('total_amount', 0)),
                    'status': 'Complete',
                    'txn_date': sr.get('txn_date', '')
                })
            return results
        return []

    def _query_statement_charges(self, txn_id: str, txn_date_range: dict) -> list:
        """Query statement charges from QuickBooks."""
        request = QBXMLBuilder.build_charge_query(
            txn_id=txn_id if txn_id else None,
            txn_date_range=txn_date_range if txn_date_range else None,
            max_returned=100
        )
        response = QBIPCClient.execute_request(request)
        parser_result = QBXMLParser.parse_response(response)

        if parser_result['success'] and 'charges' in parser_result['data']:
            charges = parser_result['data']['charges']
            results = []
            for charge in charges:
                # Transform to expected format
                results.append({
                    'type': 'Statement Charge',
                    'txn_id': charge.get('txn_id', ''),
                    'ref_number': charge.get('ref_number', ''),
                    'customer_name': charge.get('customer_ref', {}).get('full_name', ''),
                    'amount': float(charge.get('amount', 0)),
                    'status': 'Complete',
                    'txn_date': charge.get('txn_date', '')
                })
            return results
        return []

    def _filter_search_results(self, results: list, search_text: str,
                               amount_min: float, amount_max: float) -> list:
        """Filter search results based on criteria."""
        filtered = []

        for result in results:
            # Filter by customer name or ref number
            if search_text:
                customer_name = result.get('customer_name', '').lower()
                ref_number = result.get('ref_number', '').lower()
                if search_text not in customer_name and search_text not in ref_number:
                    continue

            # Filter by amount range
            amount = float(result.get('amount', 0))
            if amount_min is not None and amount < amount_min:
                continue
            if amount_max is not None and amount > amount_max:
                continue

            filtered.append(result)

        return filtered

    def _display_search_results(self, results: list, display_mode: str):
        """Display search results based on mode."""
        if display_mode == 'Table':
            self._display_results_in_table(results)
        else:
            self._display_results_in_popup(results)

    def _display_results_in_table(self, results: list):
        """Display search results in the main table."""
        # Clear existing entries in the table
        for item in self.invoice_tree.get_children():
            self.invoice_tree.delete(item)

        # Add search results to table
        for result in results:
            txn_type = result.get('type', '')
            ref_number = result.get('ref_number', '')
            customer_name = result.get('customer_name', '')
            amount = result.get('amount', 0)
            status = result.get('status', 'Unknown')
            last_checked = result.get('txn_date', '')

            self.invoice_tree.insert('', 'end', values=(
                txn_type, ref_number, customer_name, f"${amount:.2f}",
                status, last_checked
            ))

        self._log_monitor(f"Search complete: {len(results)} result(s) displayed in table")

    def _display_results_in_popup(self, results: list):
        """Display search results in a popup window."""
        popup = tk.Toplevel(self.root)
        popup.title("Search Results")
        popup.geometry("900x500")

        # Results frame
        frame = ttk.Frame(popup, padding=10)
        frame.pack(fill='both', expand=True)

        # Treeview
        columns = ('Type', 'Ref#', 'Customer', 'Amount', 'Status', 'Date')
        tree = ttk.Treeview(frame, columns=columns, show='headings', height=20)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=140)

        tree.pack(fill='both', expand=True, side='left')

        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        scrollbar.pack(side='right', fill='y')
        tree.configure(yscrollcommand=scrollbar.set)

        # Add results
        for result in results:
            txn_type = result.get('type', '')
            ref_number = result.get('ref_number', '')
            customer_name = result.get('customer_name', '')
            amount = result.get('amount', 0)
            status = result.get('status', 'Unknown')
            txn_date = result.get('txn_date', '')

            tree.insert('', 'end', values=(
                txn_type, ref_number, customer_name, f"${amount:.2f}",
                status, txn_date
            ))

        # Close button
        ttk.Button(popup, text="Close", command=popup.destroy).pack(pady=10)

        self._log_monitor(f"Search complete: {len(results)} result(s) displayed in popup")

    def _start_monitoring(self):
        """Start monitoring transactions."""
        state = self.store.get_state()

        total_transactions = len(state.invoices) + len(state.sales_receipts) + len(state.statement_charges)
        if total_transactions == 0:
            messagebox.showwarning("Warning", "No transactions to monitor! Create some invoices, sales receipts, or statement charges first.")
            return

        self.monitoring_stop_flag = False
        self.store.dispatch(set_monitoring(True))

        self.start_monitor_btn.config(state='disabled')
        self.stop_monitor_btn.config(state='normal')

        self._log_monitor(f"Starting monitoring for {len(state.invoices)} invoice(s), {len(state.sales_receipts)} sales receipt(s), {len(state.statement_charges)} charge(s)...")

        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def _stop_monitoring(self):
        """Stop monitoring invoices."""
        self.monitoring_stop_flag = True
        self.store.dispatch(set_monitoring(False))

        self.start_monitor_btn.config(state='normal')
        self.stop_monitor_btn.config(state='disabled')

        self._log_monitor("Monitoring stopped.")

    def _monitor_loop(self):
        """Monitoring loop (runs in separate thread)."""
        try:
            interval = int(self.check_interval.get())

            while not self.monitoring_stop_flag:
                try:
                    self._check_all_transactions()
                except Exception as e:
                    self.root.after(0, lambda: self._log_monitor(f"✗ Error during check: {str(e)}"))

                # Wait for interval (check stop flag frequently)
                for _ in range(interval):
                    if self.monitoring_stop_flag:
                        break
                    time.sleep(1)
        finally:
            pass

    def _check_all_transactions(self):
        """Check all tracked transactions (invoices, sales receipts, charges)."""
        self._check_invoices()
        self._check_sales_receipts()
        self._check_statement_charges()

    def _check_invoices(self):
        """Check all tracked invoices for updates."""
        state = self.store.get_state()

        for invoice in state.invoices:
            try:
                # Query invoice
                request = QBXMLBuilder.build_invoice_query(txn_id=invoice.txn_id)
                qb = QBIPCClient()
                response_xml = qb.execute_request(request)

                parser_result = QBXMLParser.parse_response(response_xml)

                if parser_result['success'] and parser_result['data']['invoices']:
                    qb_invoice = parser_result['data']['invoices'][0]

                    # Check for status change
                    new_status = 'closed' if qb_invoice['is_paid'] else 'open'
                    old_status = invoice.status

                    if new_status != old_status:
                        self.root.after(0, lambda i=invoice, ns=new_status, os=old_status:
                                      self._log_monitor(f"Status change detected: {i.ref_number} ({os} → {ns})"))

                        # Verify transaction
                        self._verify_transaction(invoice, qb_invoice, 'Invoice')

                    # Update invoice record
                    updated_invoice = InvoiceRecord(
                        txn_id=invoice.txn_id,
                        ref_number=invoice.ref_number,
                        customer_name=invoice.customer_name,
                        amount=invoice.amount,
                        status=new_status,
                        created_at=invoice.created_at,
                        last_checked=datetime.now(),
                        deposit_account=qb_invoice.get('deposit_account', {}).get('full_name') if 'deposit_account' in qb_invoice else None,
                        payment_info=qb_invoice.get('linked_transactions', [])
                    )

                    self.store.dispatch(update_invoice(updated_invoice))
                    self.root.after(0, self._update_invoice_tree)

            except Exception as e:
                self.root.after(0, lambda inv=invoice, err=str(e):
                              self._log_monitor(f"✗ Error checking {inv.ref_number}: {err}"))

    def _check_sales_receipts(self):
        """Check all tracked sales receipts for updates."""
        state = self.store.get_state()

        for sr in state.sales_receipts:
            try:
                request = QBXMLBuilder.build_sales_receipt_query(txn_id=sr.txn_id)
                qb = QBIPCClient()
                response_xml = qb.execute_request(request)
                parser_result = QBXMLParser.parse_response(response_xml)

                if parser_result['success'] and parser_result['data']['sales_receipts']:
                    qb_sr = parser_result['data']['sales_receipts'][0]
                    new_status = 'closed' if qb_sr.get('is_paid') else 'open'
                    old_status = sr.status

                    if new_status != old_status:
                        self.root.after(0, lambda s=sr, ns=new_status, os=old_status:
                                      self._log_monitor(f"Status change detected: {s.ref_number} (Sales Receipt) ({os} → {ns})"))

                        # Verify transaction
                        self._verify_transaction(sr, qb_sr, 'Sales Receipt')

                    updated_sr = SalesReceiptRecord(
                        txn_id=sr.txn_id,
                        ref_number=sr.ref_number,
                        customer_name=sr.customer_name,
                        amount=sr.amount,
                        status=new_status,
                        created_at=sr.created_at,
                        last_checked=datetime.now(),
                        deposit_account=qb_sr.get('deposit_to_account_ref', {}).get('full_name'),
                        payment_info=qb_sr.get('linked_transactions', [])
                    )

                    self.store.dispatch(update_sales_receipt(updated_sr))
                    self.root.after(0, self._update_invoice_tree)

            except Exception as e:
                self.root.after(0, lambda s=sr, err=str(e):
                              self._log_monitor(f"✗ Error checking {s.ref_number}: {err}"))

    def _check_statement_charges(self):
        """Check all tracked statement charges for updates."""
        state = self.store.get_state()

        for charge in state.statement_charges:
            try:
                request = QBXMLBuilder.build_charge_query(txn_id=charge.txn_id)
                qb = QBIPCClient()
                response_xml = qb.execute_request(request)
                parser_result = QBXMLParser.parse_response(response_xml)

                if parser_result['success'] and parser_result['data']['charges']:
                    qb_charge = parser_result['data']['charges'][0]

                    # Verify transaction on first check
                    if charge.last_checked is None:
                        self._verify_transaction(charge, qb_charge, 'Statement Charge')

                    updated_charge = StatementChargeRecord(
                        txn_id=charge.txn_id,
                        ref_number=charge.ref_number,
                        customer_name=charge.customer_name,
                        amount=charge.amount,
                        status='completed',
                        created_at=charge.created_at,
                        last_checked=datetime.now()
                    )

                    self.store.dispatch(update_statement_charge(updated_charge))
                    self.root.after(0, self._update_invoice_tree)

            except Exception as e:
                self.root.after(0, lambda c=charge, err=str(e):
                              self._log_monitor(f"✗ Error checking {c.ref_number}: {err}"))

    def _verify_transaction(self, transaction, qb_data: dict, txn_type: str):
        """
        Verify transaction payment posting and related fields.

        Args:
            transaction: InvoiceRecord, SalesReceiptRecord, or StatementChargeRecord
            qb_data: QuickBooks data from query response
            txn_type: 'Invoice', 'Sales Receipt', or 'Statement Charge'
        """
        state = self.store.get_state()
        verification = {
            'timestamp': datetime.now(),
            'txn_type': txn_type,
            'txn_ref': transaction.ref_number,
            'result': 'PASS',
            'details': []
        }

        # Get transaction total and balance
        txn_total = transaction.amount
        balance_remaining = qb_data.get('balance_remaining', 0)

        # Check transaction memo (display only, not validation)
        if 'memo' in qb_data:
            verification['details'].append(f"Transaction memo: {qb_data.get('memo', 'N/A')}")

        # Check payment transactions
        linked_txns = qb_data.get('linked_transactions', [])

        # Detect if any payment is cash (case-insensitive check)
        has_cash_payment = any(
            'payment_method' in txn and
            txn.get('payment_method', '').lower() in ['cash', 'check']
            for txn in linked_txns
        )

        if not linked_txns:
            # No payments found
            if balance_remaining == 0:
                # Paid but no linked transactions - might be cash or sales receipt
                verification['details'].append('✓ No linked payment transactions (may be direct cash payment or sales receipt)')
            else:
                verification['result'] = 'FAIL'
                verification['details'].append('✗ No payment transactions found and balance > 0')
        else:
            # Calculate total payment amount
            total_payment = sum(float(txn.get('amount', 0)) for txn in linked_txns)
            verification['details'].append(f"Found {len(linked_txns)} payment transaction(s), Total: ${total_payment:.2f}")

            # Display payment details (method and memo)
            for i, payment_txn in enumerate(linked_txns):
                payment_method = payment_txn.get('payment_method', 'Not specified')
                payment_memo = payment_txn.get('memo', 'N/A')
                verification['details'].append(f"Payment #{i+1}: Method={payment_method}, Memo={payment_memo}")

            # Note if cash payment detected
            if has_cash_payment:
                verification['details'].append("ℹ Cash/Check payment detected - relaxed validation")

            # Validate payment amount vs transaction total
            if abs(total_payment - txn_total) < 0.01:
                # Fully paid
                if balance_remaining == 0:
                    verification['details'].append(f"✓ Payment amount matches total (${txn_total:.2f}), Status: CLOSED")
                else:
                    verification['result'] = 'FAIL'
                    verification['details'].append(f"✗ Payment matches total but balance is ${balance_remaining:.2f} (should be $0)")
            elif total_payment < txn_total:
                # Partial payment
                expected_balance = txn_total - total_payment
                if abs(balance_remaining - expected_balance) < 0.01:
                    verification['details'].append(f"✓ Partial payment: ${total_payment:.2f} of ${txn_total:.2f}, Balance: ${balance_remaining:.2f}")
                else:
                    verification['result'] = 'FAIL'
                    verification['details'].append(f"✗ Payment: ${total_payment:.2f}, Expected balance: ${expected_balance:.2f}, Actual: ${balance_remaining:.2f}")
            else:
                # Overpayment
                verification['result'] = 'WARN'
                verification['details'].append(f"⚠ Overpayment: ${total_payment:.2f} > ${txn_total:.2f}")

        # Check deposit account
        if 'deposit_account' in qb_data and qb_data['deposit_account']:
            actual_deposit = qb_data['deposit_account'].get('full_name', 'Unknown')
            expected_deposit = state.expected_deposit_account

            if expected_deposit:
                if actual_deposit == expected_deposit:
                    verification['details'].append(f"✓ Deposit account matches: {actual_deposit}")
                else:
                    verification['result'] = 'FAIL'
                    verification['details'].append(f"✗ Deposit account mismatch - Expected: {expected_deposit}, Actual: {actual_deposit}")
            else:
                verification['details'].append(f"Deposit account: {actual_deposit} (no expected account set)")
        else:
            verification['details'].append('No deposit account information')

        self.store.dispatch(add_verification_result(verification))
        self.root.after(0, self._update_verify_tree)

    def _update_customer_combo(self):
        """Update all customer dropdowns."""
        state = self.store.get_state()
        customer_names = [f"{c['name']} ({c.get('email', 'no email')})" for c in state.customers]

        # Build ListID mapping (display_name -> list_id)
        self.customer_listid_map = {}
        for c in state.customers:
            display_name = f"{c['name']} ({c.get('email', 'no email')})"
            self.customer_listid_map[display_name] = c['list_id']

        # Update all customer comboboxes
        for combo in self.customer_combos:
            combo['values'] = customer_names
            if customer_names:
                combo.current(len(customer_names) - 1)

        # Update status label on Setup subtab
        count = len(state.customers)
        items_count = len(state.items)

        if count > 0:
            self.customers_status_label.config(
                text=f"{count} customer{'s' if count != 1 else ''} loaded",
                foreground='green'
            )
        else:
            self.customers_status_label.config(
                text="No customers loaded",
                foreground='red'
            )

        # Update summary - only show ready when BOTH customers and items are loaded
        if count > 0 and items_count > 0:
            self.setup_summary_label.config(
                text=f"{count} customers, {items_count} items loaded - Ready to create transactions"
            )
        elif count > 0 or items_count > 0:
            self.setup_summary_label.config(
                text=f"{count} customers, {items_count} items loaded - Load both to begin"
            )
        else:
            self.setup_summary_label.config(
                text="Load customers and items from QuickBooks to begin"
            )

    def _update_accounts_combo(self):
        """Update deposit account dropdown in Monitor tab."""
        state = self.store.get_state()
        account_names = [acc['full_name'] for acc in state.accounts]

        # Update the deposit account combobox
        if hasattr(self, 'expected_deposit_account_combo'):
            self.expected_deposit_account_combo['values'] = account_names

    def _update_invoice_tree(self):
        """Update invoice tree view with all transaction types."""
        # Clear tree
        for item in self.invoice_tree.get_children():
            self.invoice_tree.delete(item)

        state = self.store.get_state()

        # Collect all transactions with type info
        all_transactions = []

        # Add invoices
        for invoice in state.invoices:
            last_checked = invoice.last_checked.strftime('%H:%M:%S') if invoice.last_checked else 'Never'
            all_transactions.append({
                'type': 'Invoice',
                'ref_number': invoice.ref_number,
                'customer_name': invoice.customer_name,
                'amount': invoice.amount,
                'status': invoice.status.upper(),
                'last_checked': last_checked,
                'created_at': invoice.created_at
            })

        # Add sales receipts
        for sr in state.sales_receipts:
            last_checked = sr.last_checked.strftime('%H:%M:%S') if sr.last_checked else 'Never'
            all_transactions.append({
                'type': 'Sales Receipt',
                'ref_number': sr.ref_number,
                'customer_name': sr.customer_name,
                'amount': sr.amount,
                'status': sr.status.upper(),
                'last_checked': last_checked,
                'created_at': sr.created_at
            })

        # Add statement charges
        for charge in state.statement_charges:
            last_checked = charge.last_checked.strftime('%H:%M:%S') if charge.last_checked else 'Never'
            all_transactions.append({
                'type': 'Statement Charge',
                'ref_number': charge.ref_number,
                'customer_name': charge.customer_name,
                'amount': charge.amount,
                'status': charge.status.upper(),
                'last_checked': last_checked,
                'created_at': charge.created_at
            })

        # Sort by created_at (most recent first)
        all_transactions.sort(key=lambda x: x['created_at'], reverse=True)

        # Insert all transactions into tree
        for txn in all_transactions:
            self.invoice_tree.insert('', 'end', values=(
                txn['type'],
                txn['ref_number'],
                txn['customer_name'],
                f"${txn['amount']:.2f}",
                txn['status'],
                txn['last_checked']
            ))

    def _update_verify_tree(self):
        """Update verification results tree."""
        # Clear tree
        for item in self.verify_tree.get_children():
            self.verify_tree.delete(item)

        # Add results
        state = self.store.get_state()
        for result in state.verification_results:
            self.verify_tree.insert('', 'end', values=(
                result['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                result.get('txn_type', 'Invoice'),  # Default to 'Invoice' for old records
                result.get('txn_ref', result.get('invoice_ref', 'N/A')),  # Support old format
                result['result'],
                '; '.join(result['details'])
            ))

    def _on_state_change(self):
        """Called when store state changes."""
        state = self.store.get_state()
        status_text = (f"Customers: {len(state.customers)} | "
                      f"Invoices: {len(state.invoices)} | "
                      f"Sales Receipts: {len(state.sales_receipts)} | "
                      f"Statement Charges: {len(state.statement_charges)}")
        if state.monitoring_active:
            status_text += " | MONITORING ACTIVE"
        self.status_bar.config(text=status_text)

        # Update monitor tab transaction list
        self._update_invoice_tree()

    def _on_closing(self):
        """Handle graceful application shutdown."""
        # Set tray icon to yellow (shutting down)
        if hasattr(self, 'tray_icon'):
            self.tray_icon.set_state('yellow')

        # Stop monitoring if active
        if self.monitoring_stop_flag is False and hasattr(self, 'monitor_thread'):
            self.monitoring_stop_flag = True
            if self.monitor_thread and self.monitor_thread.is_alive():
                print("Waiting for monitoring thread to stop...")
                self.monitor_thread.join(timeout=5.0)

        # Stop connection manager
        print("Stopping connection manager...")
        stop_manager()

        # Stop tray icon
        if hasattr(self, 'tray_icon'):
            self.tray_icon.stop()

        # Destroy window
        self.root.destroy()

    def _force_close(self):
        """Force close connection manager and exit immediately."""
        print("Force closing connection manager...")

        # Set tray icon to yellow
        if hasattr(self, 'tray_icon'):
            self.tray_icon.set_state('yellow')

        # Import for process termination
        from qb_ipc_client import _manager_process

        # Kill manager process immediately
        if _manager_process and _manager_process.is_alive():
            print(f"Terminating manager process (PID: {_manager_process.pid})")
            _manager_process.terminate()
            _manager_process.join(timeout=2.0)

            if _manager_process.is_alive():
                print("Manager still alive, killing forcefully...")
                _manager_process.kill()

        # Stop tray icon
        if hasattr(self, 'tray_icon'):
            self.tray_icon.stop()

        # Destroy window
        self.root.destroy()


def main():
    """Main entry point."""
    root = tk.Tk()
    app = QBDTestToolApp(root)
    root.mainloop()


if __name__ == '__main__':
    # Required for multiprocessing with PyInstaller
    multiprocessing.freeze_support()
    main()
