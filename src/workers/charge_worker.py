"""
Statement Charge creation worker for QuickBooks Desktop Test Tool.

Background worker for creating batch statement charges in QuickBooks.
"""

from datetime import datetime
from tkinter import messagebox
from qb_ipc_client import QBIPCClient, disconnect_qb
from qbxml_builder import QBXMLBuilder
from qbxml_parser import QBXMLParser
from mock_generation import ChargeGenerator


def create_charge_worker(app, customer: dict, num_charges: int,
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

        app.root.after(0, lambda: app._log_create(f"Starting batch creation of {num_charges} statement charge(s) for {customer['name']} ({date_range})..."))

        # Select a random item to use for all charges
        # For statement charges, we typically use a generic service item
        charge_item = random.choice(items) if items else None

        # Create QB client once for entire batch
        qb = QBIPCClient()

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
                charge_data = ChargeGenerator.generate_statement_charge_data(
                    customer_ref=customer['list_id'],
                    amount=amount,
                    item_ref=charge_item['list_id'] if charge_item else None,
                    txn_date=txn_date
                )

                # Log current progress
                charge_num = i + 1
                app.root.after(0, lambda n=charge_num, amt=amount:
                              app._log_create(f"[{n}/{num_charges}] Creating statement charge: Amount: ${amt:.2f}"))

                # Build QBXML request
                request = QBXMLBuilder.build_charge_add(charge_data)

                # DEBUG: Log the XML request
                app.root.after(0, lambda n=charge_num, xml=request:
                              app._log_create(f"  [DEBUG {n}] QBXML Request:\n{xml}"))

                # Send to QuickBooks
                response_xml = qb.execute_request(request)

                # DEBUG: Log the XML response
                app.root.after(0, lambda n=charge_num, xml=response_xml:
                              app._log_create(f"  [DEBUG {n}] QBXML Response:\n{xml}"))

                # Parse response
                parser_result = QBXMLParser.parse_response(response_xml)

                if parser_result['success']:
                    charge_info = parser_result['data']

                    app.root.after(0, lambda n=charge_num, tid=charge_info['txn_id'], amt=charge_info.get('amount', amount):
                                  app._log_create(f"  ✓ [{n}/{num_charges}] Statement charge created: ${amt} (ID: {tid})"))
                    successful_count += 1

                else:
                    error_msg = parser_result.get('error', 'Unknown error')
                    app.root.after(0, lambda n=charge_num, msg=error_msg:
                                  app._log_create(f"  ✗ [{n}/{num_charges}] Error: {msg}"))
                    failed_count += 1

            except Exception as e:
                error_str = str(e)
                charge_num = i + 1
                app.root.after(0, lambda n=charge_num, msg=error_str:
                              app._log_create(f"  ✗ [{n}/{num_charges}] Error: {msg}"))
                failed_count += 1

        # Final summary
        summary = f"Batch complete: {successful_count} succeeded, {failed_count} failed out of {num_charges} total"
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
        app.root.after(0, lambda: app.create_charge_btn.config(state='normal'))
        app.root.after(0, lambda: app.status_bar.config(text="Ready"))
