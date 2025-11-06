"""
Monitor worker for QuickBooks Desktop Test Tool.

Background worker for monitoring transactions and verifying payment posting.
"""

import time
from datetime import datetime
from qb_ipc_client import QBIPCClient
from qbxml_builder import QBXMLBuilder
from qbxml_parser import QBXMLParser
from store import (
    InvoiceRecord, SalesReceiptRecord, StatementChargeRecord,
    update_invoice, update_sales_receipt, update_statement_charge, add_verification_result
)


def monitor_loop_worker(app):
    """
    Monitoring loop (runs in separate thread).

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    try:
        interval = int(app.check_interval.get())

        while not app.monitoring_stop_flag:
            try:
                check_all_transactions(app)
            except Exception as e:
                app.root.after(0, lambda: app._log_monitor(f"✗ Error during check: {str(e)}"))

            # Wait for interval (check stop flag frequently)
            for _ in range(interval):
                if app.monitoring_stop_flag:
                    break
                time.sleep(1)
    finally:
        pass


def check_all_transactions(app):
    """
    Check all tracked transactions (invoices, sales receipts, charges).

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    check_invoices(app)
    check_sales_receipts(app)
    check_statement_charges(app)


def check_invoices(app):
    """
    Check all tracked invoices for updates.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    state = app.store.get_state()

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
                    app.root.after(0, lambda i=invoice, ns=new_status, os=old_status:
                                  app._log_monitor(f"Status change detected: {i.ref_number} ({os} → {ns})"))

                    # Verify transaction
                    verify_transaction(app, invoice, qb_invoice, 'Invoice')

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

                app.store.dispatch(update_invoice(updated_invoice))
                app.root.after(0, lambda: update_invoice_tree(app))

        except Exception as e:
            app.root.after(0, lambda inv=invoice, err=str(e):
                          app._log_monitor(f"✗ Error checking {inv.ref_number}: {err}"))


def check_sales_receipts(app):
    """
    Check all tracked sales receipts for updates.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    state = app.store.get_state()

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
                    app.root.after(0, lambda s=sr, ns=new_status, os=old_status:
                                  app._log_monitor(f"Status change detected: {s.ref_number} (Sales Receipt) ({os} → {ns})"))

                    # Verify transaction
                    verify_transaction(app, sr, qb_sr, 'Sales Receipt')

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

                app.store.dispatch(update_sales_receipt(updated_sr))
                app.root.after(0, lambda: update_invoice_tree(app))

        except Exception as e:
            app.root.after(0, lambda s=sr, err=str(e):
                          app._log_monitor(f"✗ Error checking {s.ref_number}: {err}"))


def check_statement_charges(app):
    """
    Check all tracked statement charges for updates.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    state = app.store.get_state()

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
                    verify_transaction(app, charge, qb_charge, 'Statement Charge')

                updated_charge = StatementChargeRecord(
                    txn_id=charge.txn_id,
                    ref_number=charge.ref_number,
                    customer_name=charge.customer_name,
                    amount=charge.amount,
                    status='completed',
                    created_at=charge.created_at,
                    last_checked=datetime.now()
                )

                app.store.dispatch(update_statement_charge(updated_charge))
                app.root.after(0, lambda: update_invoice_tree(app))

        except Exception as e:
            app.root.after(0, lambda c=charge, err=str(e):
                          app._log_monitor(f"✗ Error checking {c.ref_number}: {err}"))


def verify_transaction(app, transaction, qb_data: dict, txn_type: str):
    """
    Verify transaction payment posting and related fields.

    Args:
        app: Reference to the main QBDTestToolApp instance
        transaction: InvoiceRecord, SalesReceiptRecord, or StatementChargeRecord
        qb_data: QuickBooks data from query response
        txn_type: 'Invoice', 'Sales Receipt', or 'Statement Charge'
    """
    state = app.store.get_state()
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

    # Check transaction memo for changes
    if 'memo' in qb_data:
        current_memo = qb_data.get('memo', '')
        verification['details'].append(f"Transaction memo: {current_memo if current_memo else '(empty)'}")

        # Binary check: has memo changed from initial state?
        if app.check_transaction_memo_var.get():
            initial_memo = getattr(transaction, 'initial_memo', None)

            if initial_memo is not None:
                if current_memo != initial_memo:
                    verification['details'].append(f"✓ Transaction memo changed (was: '{initial_memo}')")
                else:
                    verification['details'].append(f"⚠ Transaction memo unchanged from initial state")
                    verification['result'] = 'WARN'
            else:
                verification['details'].append(f"ℹ No initial memo recorded for comparison")

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
            payment_memo = payment_txn.get('memo', '')
            verification['details'].append(f"Payment #{i+1}: Method={payment_method}, Memo={payment_memo if payment_memo else '(empty)'}")

        # Binary check: has payment memo changed from initial state?
        if app.check_payment_memo_var.get() and linked_txns:
            initial_memo = getattr(transaction, 'initial_memo', None)

            if initial_memo is not None:
                # Check each payment memo for changes
                for i, payment_txn in enumerate(linked_txns):
                    payment_memo = payment_txn.get('memo', '')

                    if payment_memo and payment_memo != initial_memo:
                        verification['details'].append(f"✓ Payment #{i+1} memo has been updated")
                    elif not payment_memo:
                        verification['details'].append(f"⚠ Payment #{i+1} memo is empty")
                        verification['result'] = 'WARN'
                    else:
                        verification['details'].append(f"⚠ Payment #{i+1} memo unchanged from initial")
                        verification['result'] = 'WARN'
            else:
                verification['details'].append(f"ℹ No initial memo recorded for payment comparison")

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

    app.store.dispatch(add_verification_result(verification))
    app.root.after(0, lambda: update_verify_tree(app))


def update_invoice_tree(app):
    """
    Update invoice tree view with all transaction types.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    # Clear tree
    for item in app.invoice_tree.get_children():
        app.invoice_tree.delete(item)

    state = app.store.get_state()

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
        app.invoice_tree.insert('', 'end', values=(
            txn['type'],
            txn['ref_number'],
            txn['customer_name'],
            f"${txn['amount']:.2f}",
            txn['status'],
            txn['last_checked']
        ))


def update_verify_tree(app):
    """
    Update verification results tree.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    # Clear tree
    for item in app.verify_tree.get_children():
        app.verify_tree.delete(item)

    # Add results
    state = app.store.get_state()
    for result in state.verification_results:
        app.verify_tree.insert('', 'end', values=(
            result['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            result.get('txn_type', 'Invoice'),  # Default to 'Invoice' for old records
            result.get('txn_ref', result.get('invoice_ref', 'N/A')),  # Support old format
            result['result'],
            '; '.join(result['details'])
        ))
