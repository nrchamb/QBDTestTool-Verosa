"""
Sales Receipt creation worker for QuickBooks Desktop Test Tool.

Background worker for creating batch sales receipts in QuickBooks.
"""

from datetime import datetime
from tkinter import messagebox
from qb_ipc_client import QBIPCClient, disconnect_qb
from qbxml_builder import QBXMLBuilder
from qbxml_parser import QBXMLParser
from mock_generation import SalesReceiptGenerator
from store.state import SalesReceiptRecord
from store.actions import add_sales_receipt


def create_sales_receipt_worker(app, customer: dict, num_receipts: int,
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

        app.root.after(0, lambda: app._log_create(f"Starting batch creation of {num_receipts} sales receipt(s) for {customer['name']} ({date_range})..."))

        # Create QB client once for entire batch
        qb = QBIPCClient()

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
                receipt_data = SalesReceiptGenerator.generate_sales_receipt_data(
                    customer_ref=customer['list_id'],
                    num_line_items=num_lines,
                    total_amount=amount,
                    item_refs=item_refs,
                    txn_date=txn_date
                )

                # Log current progress
                receipt_num = i + 1
                app.root.after(0, lambda n=receipt_num, ref=receipt_data['ref_number']:
                              app._log_create(f"[{n}/{num_receipts}] Creating sales receipt Ref#: {ref}, Amount: ${amount:.2f}, Lines: {num_lines}"))

                # Build QBXML request
                request = QBXMLBuilder.build_sales_receipt_add(receipt_data)

                # DEBUG: Log the XML request
                receipt_num = i + 1
                app.root.after(0, lambda n=receipt_num, xml=request:
                              app._log_create(f"  [DEBUG {n}] QBXML Request:\n{xml}"))

                # Send to QuickBooks
                response_xml = qb.execute_request(request)

                # DEBUG: Log the XML response
                app.root.after(0, lambda n=receipt_num, xml=response_xml:
                              app._log_create(f"  [DEBUG {n}] QBXML Response:\n{xml}"))

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

                    app.store.dispatch(add_sales_receipt(receipt_record))
                    app.root.after(0, lambda n=receipt_num, ref=receipt_info['ref_number'], tid=receipt_info['txn_id']:
                                  app._log_create(f"  ✓ [{n}/{num_receipts}] Sales receipt created: {ref} (ID: {tid})"))
                    successful_count += 1

                else:
                    error_msg = parser_result.get('error', 'Unknown error')
                    app.root.after(0, lambda n=receipt_num, msg=error_msg:
                                  app._log_create(f"  ✗ [{n}/{num_receipts}] Error: {msg}"))
                    failed_count += 1

            except Exception as e:
                error_str = str(e)
                receipt_num = i + 1
                app.root.after(0, lambda n=receipt_num, msg=error_str:
                              app._log_create(f"  ✗ [{n}/{num_receipts}] Error: {msg}"))
                failed_count += 1

        # Final summary
        summary = f"Batch complete: {successful_count} succeeded, {failed_count} failed out of {num_receipts} total"
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
        app.root.after(0, lambda: app.create_sales_receipt_btn.config(state='normal'))
        app.root.after(0, lambda: app.status_bar.config(text="Ready"))


def query_sales_receipt_worker(app, txn_id: str):
    """Worker function to query sales receipt in background."""
    try:
        app.root.after(0, lambda: app._log_create(f"Querying sales receipt TxnID: {txn_id}"))

        # Build QBXML query request
        request = QBXMLBuilder.build_sales_receipt_query(txn_id=txn_id)

        # DEBUG: Log the XML request
        app.root.after(0, lambda xml=request:
                      app._log_create(f"  [DEBUG] Query Request:\n{xml}"))

        # Send to QuickBooks
        qb = QBIPCClient()
        response_xml = qb.execute_request(request)

        # DEBUG: Log the XML response
        app.root.after(0, lambda xml=response_xml:
                      app._log_create(f"  [DEBUG] Query Response:\n{xml}"))

        # Parse response
        parser_result = QBXMLParser.parse_response(response_xml)

        if parser_result['success']:
            receipts = parser_result['data'].get('sales_receipts', [])

            if receipts:
                receipt = receipts[0]
                app.root.after(0, lambda: app._log_create(f"✓ Sales receipt found!"))
                app.root.after(0, lambda: app._log_create(f"  Ref#: {receipt.get('ref_number')}"))
                app.root.after(0, lambda: app._log_create(f"  Customer: {receipt.get('customer_ref', {}).get('full_name')}"))
                app.root.after(0, lambda: app._log_create(f"  Total: ${receipt.get('total_amount', 0):.2f}"))
                app.root.after(0, lambda: app._log_create(f"  IsPending: {receipt.get('is_pending')}"))
                app.root.after(0, lambda: app._log_create(f"  IsToBePrinted: {receipt.get('is_to_be_printed')}"))
                app.root.after(0, lambda: app._log_create(f"  IsToBeEmailed: {receipt.get('is_to_be_emailed')}"))
                app.root.after(0, lambda: app._log_create(f"  TimeCreated: {receipt.get('time_created')}"))
                app.root.after(0, lambda: app._log_create(f"  TimeModified: {receipt.get('time_modified')}"))

                if 'deposit_account' in receipt:
                    app.root.after(0, lambda: app._log_create(f"  DepositTo: {receipt['deposit_account'].get('full_name')}"))
            else:
                app.root.after(0, lambda: app._log_create(f"✗ Sales receipt NOT FOUND in QB!"))
                app.root.after(0, lambda: messagebox.showwarning("Not Found",
                    "Sales receipt with this TxnID was not found in QuickBooks database!"))

        else:
            error_msg = parser_result.get('error', 'Unknown error')
            app.root.after(0, lambda: app._log_create(f"✗ Error: {error_msg}"))
            app.root.after(0, lambda: messagebox.showerror("Error", error_msg))

    except Exception as e:
        error_str = str(e)
        app.root.after(0, lambda: app._log_create(f"✗ Error: {error_str}"))
        app.root.after(0, lambda: messagebox.showerror("Error", error_str))
    finally:
        # Re-enable button and update status
        app.root.after(0, lambda: app.query_sr_btn.config(state='normal'))
        app.root.after(0, lambda: app.status_bar.config(text="Ready"))
