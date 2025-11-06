"""
Monitor search actions for QuickBooks Desktop Test Tool.

Handles transaction search and display functionality.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime
from qb_ipc_client import QBIPCClient
from qbxml_builder import QBXMLBuilder
from qbxml_parser import QBXMLParser


def search_transactions(app):
    """
    Search transactions based on search criteria.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    # Get search parameters
    search_text = app.search_text.get().strip().lower()
    txn_id = app.search_txn_id.get().strip()
    txn_type = app.search_txn_type.get()
    date_from = app.search_date_from.get().strip()
    date_to = app.search_date_to.get().strip()
    amount_min = app.search_amount_min.get().strip()
    amount_max = app.search_amount_max.get().strip()
    display_mode = app.search_display_mode.get()
    search_all_qb = app.search_scope_var.get()

    # Validate date format if provided
    if date_from and not validate_date_format(date_from):
        messagebox.showerror("Error", "Invalid 'Date From' format. Use YYYY-MM-DD")
        return
    if date_to and not validate_date_format(date_to):
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
            target=execute_search_query,
            args=(app, txn_id, search_text, txn_type, txn_date_range, amount_min_float, amount_max_float, display_mode),
            daemon=True
        ).start()
        app._log_monitor("Executing search query on all QB transactions...")
    else:
        # Search monitored transactions (no thread needed, it's fast)
        search_monitored_transactions(app, search_text, txn_id, txn_type, date_from, date_to,
                                      amount_min_float, amount_max_float, display_mode)


def search_monitored_transactions(app, search_text: str, txn_id: str, txn_type: str,
                                   date_from: str, date_to: str, amount_min: float,
                                   amount_max: float, display_mode: str):
    """
    Search monitored transactions from Redux store.

    Args:
        app: Reference to the main QBDTestToolApp instance
        search_text: Text to search in customer name or ref number
        txn_id: Transaction ID to filter by
        txn_type: Transaction type filter
        date_from: Start date (YYYY-MM-DD)
        date_to: End date (YYYY-MM-DD)
        amount_min: Minimum amount
        amount_max: Maximum amount
        display_mode: Display mode ('Table' or 'Popup')
    """
    state = app.store.get_state()
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
            if match_search_criteria(result, search_text, txn_id, date_from, date_to,
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
            if match_search_criteria(result, search_text, txn_id, date_from, date_to,
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
            if match_search_criteria(result, search_text, txn_id, date_from, date_to,
                                     amount_min, amount_max):
                results.append(result)

    # Display results
    display_search_results(app, results, display_mode)
    app._log_monitor(f"Search complete: {len(results)} monitored transaction(s) found")


def match_search_criteria(result: dict, search_text: str, txn_id: str,
                          date_from: str, date_to: str, amount_min: float,
                          amount_max: float) -> bool:
    """
    Check if a transaction matches search criteria.

    Args:
        result: Transaction data dictionary
        search_text: Text to search for
        txn_id: Transaction ID
        date_from: Start date
        date_to: End date
        amount_min: Minimum amount
        amount_max: Maximum amount

    Returns:
        True if transaction matches criteria
    """
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


def validate_date_format(date_str: str) -> bool:
    """
    Validate date format (YYYY-MM-DD).

    Args:
        date_str: Date string to validate

    Returns:
        True if valid format
    """
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def execute_search_query(app, txn_id: str, search_text: str, txn_type: str,
                         txn_date_range: dict, amount_min: float, amount_max: float,
                         display_mode: str):
    """
    Execute the actual search query in background thread.

    Args:
        app: Reference to the main QBDTestToolApp instance
        txn_id: Transaction ID filter
        search_text: Text search filter
        txn_type: Transaction type filter
        txn_date_range: Date range dictionary
        amount_min: Minimum amount
        amount_max: Maximum amount
        display_mode: Display mode
    """
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
                results.extend(query_invoices(txn_id, txn_date_range))
            elif qtype == 'Sales Receipts':
                results.extend(query_sales_receipts(txn_id, txn_date_range))
            elif qtype == 'Statement Charges':
                results.extend(query_statement_charges(txn_id, txn_date_range))

        # Filter results based on search criteria
        filtered_results = filter_search_results(
            results, search_text, amount_min, amount_max
        )

        # Display results based on mode
        app.root.after(0, lambda: display_search_results(app, filtered_results, display_mode))

    except Exception as e:
        error_msg = f"Search error: {str(e)}"
        app.root.after(0, lambda: app._log_monitor(error_msg))
        app.root.after(0, lambda: messagebox.showerror("Search Error", error_msg))


def query_invoices(txn_id: str, txn_date_range: dict) -> list:
    """
    Query invoices from QuickBooks.

    Args:
        txn_id: Transaction ID filter
        txn_date_range: Date range filter

    Returns:
        List of invoice dictionaries
    """
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


def query_sales_receipts(txn_id: str, txn_date_range: dict) -> list:
    """
    Query sales receipts from QuickBooks.

    Args:
        txn_id: Transaction ID filter
        txn_date_range: Date range filter

    Returns:
        List of sales receipt dictionaries
    """
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


def query_statement_charges(txn_id: str, txn_date_range: dict) -> list:
    """
    Query statement charges from QuickBooks.

    Args:
        txn_id: Transaction ID filter
        txn_date_range: Date range filter

    Returns:
        List of statement charge dictionaries
    """
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


def filter_search_results(results: list, search_text: str,
                          amount_min: float, amount_max: float) -> list:
    """
    Filter search results based on criteria.

    Args:
        results: List of transaction results
        search_text: Text to search for
        amount_min: Minimum amount
        amount_max: Maximum amount

    Returns:
        Filtered list of results
    """
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


def display_search_results(app, results: list, display_mode: str):
    """
    Display search results based on mode.

    Args:
        app: Reference to the main QBDTestToolApp instance
        results: List of search results
        display_mode: Display mode ('Table' or 'Popup')
    """
    if display_mode == 'Table':
        display_results_in_table(app, results)
    else:
        display_results_in_popup(app, results)


def display_results_in_table(app, results: list):
    """
    Display search results in the main table.

    Args:
        app: Reference to the main QBDTestToolApp instance
        results: List of search results
    """
    # Clear existing entries in the table
    for item in app.invoice_tree.get_children():
        app.invoice_tree.delete(item)

    # Add search results to table
    for result in results:
        txn_type = result.get('type', '')
        ref_number = result.get('ref_number', '')
        customer_name = result.get('customer_name', '')
        amount = result.get('amount', 0)
        status = result.get('status', 'Unknown')
        last_checked = result.get('txn_date', '')

        app.invoice_tree.insert('', 'end', values=(
            txn_type, ref_number, customer_name, f"${amount:.2f}",
            status, last_checked
        ))

    app._log_monitor(f"Search complete: {len(results)} result(s) displayed in table")


def display_results_in_popup(app, results: list):
    """
    Display search results in a popup window.

    Args:
        app: Reference to the main QBDTestToolApp instance
        results: List of search results
    """
    popup = tk.Toplevel(app.root)
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

    app._log_monitor(f"Search complete: {len(results)} result(s) displayed in popup")
