"""
Invoice creation worker for QuickBooks Desktop Test Tool.

Background worker for creating batch invoices in QuickBooks.
"""

from datetime import datetime
from tkinter import messagebox
from qb_ipc_client import QBIPCClient, disconnect_qb
from qbxml_builder import QBXMLBuilder
from qbxml_parser import QBXMLParser
from mock_generation import InvoiceGenerator
from store.state import InvoiceRecord
from store.actions import add_invoice
from workers.monitor_worker import update_invoice_tree
from app_logging import LOG_NORMAL, LOG_VERBOSE, LOG_DEBUG


def create_invoice_worker(app, customer: dict, num_invoices: int,
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

        app.root.after(0, lambda: app._log_create(f"Starting batch creation of {num_invoices} invoice(s) for {customer['name']} ({date_range})..."))

        # Create QB client once for entire batch
        qb = QBIPCClient()

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
                invoice_data = InvoiceGenerator.generate_invoice_data(
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
                app.root.after(0, lambda n=invoice_num, ref=invoice_data['ref_number']:
                              app._log_create(f"[{n}/{num_invoices}] Creating invoice Ref#: {ref}, Amount: ${amount:.2f}, Lines: {num_lines}", LOG_VERBOSE))

                # Build QBXML request
                request = QBXMLBuilder.build_invoice_add(invoice_data)

                # DEBUG: Log the XML request
                app.root.after(0, lambda n=invoice_num, xml=request:
                              app._log_create(f"  [DEBUG {n}] QBXML Request:\n{xml}", LOG_DEBUG))

                # Send to QuickBooks
                response_xml = qb.execute_request(request)

                # DEBUG: Log the XML response
                app.root.after(0, lambda n=invoice_num, xml=response_xml:
                              app._log_create(f"  [DEBUG {n}] QBXML Response:\n{xml}", LOG_DEBUG))

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

                    app.store.dispatch(add_invoice(invoice_record))
                    app.root.after(0, lambda n=invoice_num, ref=invoice_info['ref_number'], tid=invoice_info['txn_id']:
                                  app._log_create(f"  ✓ [{n}/{num_invoices}] Invoice created: {ref} (ID: {tid})", LOG_VERBOSE))
                    app.root.after(0, lambda: update_invoice_tree(app))
                    successful_count += 1

                else:
                    error_msg = parser_result.get('error', 'Unknown error')
                    app.root.after(0, lambda n=invoice_num, msg=error_msg:
                                  app._log_create(f"  ✗ [{n}/{num_invoices}] Error: {msg}"))
                    failed_count += 1

            except Exception as e:
                error_str = str(e)
                invoice_num = i + 1
                app.root.after(0, lambda n=invoice_num, msg=error_str:
                              app._log_create(f"  ✗ [{n}/{num_invoices}] Error: {msg}"))
                failed_count += 1

        # Final summary
        summary = f"Batch complete: {successful_count} succeeded, {failed_count} failed out of {num_invoices} total"
        app.root.after(0, lambda s=summary: app._log_create(f"\n{s}"))

        if failed_count > 0 and successful_count > 0:
            app.root.after(0, lambda: messagebox.showwarning("Batch Complete", summary))
        elif failed_count > 0:
            app.root.after(0, lambda: messagebox.showerror("Batch Failed", summary))
        else:
            app.root.after(0, lambda: messagebox.showinfo("Batch Complete", summary))

    except Exception as e:
        error_str = str(e)
        app.root.after(0, lambda: app._log_create(f"✗ Batch error: {error_str}"))
        app.root.after(0, lambda: messagebox.showerror("Error", error_str))
    finally:
        # Disconnect from QuickBooks after batch operation completes
        disconnect_qb()
        # Re-enable button and update status
        app.root.after(0, lambda: app.create_transaction_btn.config(state='normal'))
        app.root.after(0, lambda: app.status_bar.config(text="Ready"))
