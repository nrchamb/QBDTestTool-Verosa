"""
Customer creation worker for QuickBooks Desktop Test Tool.

Background worker for creating customers, jobs, and sub-jobs in QuickBooks.
"""

from tkinter import messagebox
from qb_ipc_client import QBIPCClient, disconnect_qb
from qb_connection import QBConnectionError
from qbxml_builder import QBXMLBuilder
from qbxml_parser import QBXMLParser
from mock_generation import CustomerGenerator
from store import add_customer


def create_customer_worker(app, email: str, field_config: dict, manual_values: dict,
                           num_jobs: int = 0, num_subjobs: int = 0):
    """
    Worker function to create customer and jobs in background.

    Args:
        app: Reference to the main application instance
        email: Customer email address
        field_config: Configuration for random vs manual fields
        manual_values: Manual field values when not using random
        num_jobs: Number of jobs to create under the customer
        num_subjobs: Number of sub-jobs to create under each job
    """
    try:
        # Step 1: Create the parent customer
        app.root.after(0, lambda: app._log_create(f"Generating customer data with email: {email}"))

        customer_data = CustomerGenerator.generate_customer(
            email=email,
            field_config=field_config,
            manual_values=manual_values
        )

        app.root.after(0, lambda: app._log_create(f"Creating customer: {customer_data['name']}"))

        # Build QBXML request
        request = QBXMLBuilder.build_customer_add(customer_data)

        # Send to QuickBooks
        qb = QBIPCClient()
        response_xml = qb.execute_request(request)

        # Parse response
        parser_result = QBXMLParser.parse_response(response_xml)

        if not parser_result['success']:
            error_msg = parser_result.get('error', 'Unknown error')
            app.root.after(0, lambda: app._log_create(f"✗ Customer creation failed: {error_msg}"))
            app.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            return

        # Customer created successfully
        customer_info = parser_result['data']
        customer_list_id = customer_info['list_id']
        customer_data['list_id'] = customer_list_id
        customer_data['full_name'] = customer_info['full_name']
        customer_data['created_by_app'] = True
        app.store.dispatch(add_customer(customer_data))

        app.root.after(0, lambda: app._log_create(f"✓ Customer created: {customer_info['full_name']}"))
        app.root.after(0, app._update_customer_combo)

        # Step 2: Create jobs if requested
        if num_jobs > 0:
            app.root.after(0, lambda: app._log_create(f"Creating {num_jobs} job(s)..."))

            for job_idx in range(num_jobs):
                try:
                    # Generate job data
                    job_data = CustomerGenerator.generate_job(
                        parent_customer_ref=customer_list_id,
                        email=email,
                        is_subjob=False
                    )

                    job_num = job_idx + 1
                    app.root.after(0, lambda n=job_num, total=num_jobs, name=job_data['name']:
                                  app._log_create(f"  Creating job {n}/{total}: {name}"))

                    # Build and send QBXML request
                    request = QBXMLBuilder.build_customer_add(job_data)
                    response_xml = qb.execute_request(request)
                    parser_result = QBXMLParser.parse_response(response_xml)

                    if not parser_result['success']:
                        error_msg = parser_result.get('error', 'Unknown error')
                        app.root.after(0, lambda n=job_num, err=error_msg:
                                      app._log_create(f"  ✗ Job {n} failed: {err}"))
                        continue

                    # Job created successfully
                    job_info = parser_result['data']
                    job_list_id = job_info['list_id']
                    app.root.after(0, lambda n=job_num, name=job_info['full_name']:
                                  app._log_create(f"  ✓ Job {n}/{num_jobs} created: {name}"))

                    # Step 3: Create sub-jobs for this job if requested
                    if num_subjobs > 0:
                        for subjob_idx in range(num_subjobs):
                            try:
                                # Generate sub-job data
                                subjob_data = CustomerGenerator.generate_job(
                                    parent_customer_ref=job_list_id,
                                    email=email,
                                    is_subjob=True
                                )

                                subjob_num = subjob_idx + 1
                                app.root.after(0, lambda jn=job_num, sn=subjob_num, total=num_subjobs, name=subjob_data['name']:
                                              app._log_create(f"    Creating sub-job {sn}/{total} for job {jn}: {name}"))

                                # Build and send QBXML request
                                request = QBXMLBuilder.build_customer_add(subjob_data)
                                response_xml = qb.execute_request(request)
                                parser_result = QBXMLParser.parse_response(response_xml)

                                if not parser_result['success']:
                                    error_msg = parser_result.get('error', 'Unknown error')
                                    app.root.after(0, lambda sn=subjob_num, err=error_msg:
                                                  app._log_create(f"    ✗ Sub-job {sn} failed: {err}"))
                                    continue

                                # Sub-job created successfully
                                subjob_info = parser_result['data']
                                app.root.after(0, lambda sn=subjob_num, name=subjob_info['full_name']:
                                              app._log_create(f"    ✓ Sub-job {sn}/{num_subjobs} created: {name}"))

                            except Exception as e:
                                error_str = str(e)
                                app.root.after(0, lambda sn=subjob_idx+1, err=error_str:
                                              app._log_create(f"    ✗ Sub-job {sn} error: {err}"))

                except Exception as e:
                    error_str = str(e)
                    app.root.after(0, lambda n=job_idx+1, err=error_str:
                                  app._log_create(f"  ✗ Job {n} error: {err}"))

            # Summary
            total_created = 1 + num_jobs + (num_jobs * num_subjobs)
            app.root.after(0, lambda t=total_created:
                          app._log_create(f"✓ All done! Created {t} total record(s)"))
        else:
            app.root.after(0, lambda: app._log_create(f"✓ Customer creation complete!"))

    except QBConnectionError as e:
        error_str = str(e)
        app.root.after(0, lambda: app._log_create(f"✗ QB Connection Error: {error_str}"))
        app.root.after(0, lambda: messagebox.showerror("QB Connection Error", error_str))
    except Exception as e:
        error_str = str(e)
        app.root.after(0, lambda: app._log_create(f"✗ Unexpected Error: {error_str}"))
        app.root.after(0, lambda: messagebox.showerror("Error", error_str))
    finally:
        # Disconnect from QuickBooks after batch operation completes
        disconnect_qb()
        # Re-enable button and update status
        app.root.after(0, lambda: app.create_customer_btn.config(state='normal'))
        app.root.after(0, lambda: app.status_bar.config(text="Ready"))
