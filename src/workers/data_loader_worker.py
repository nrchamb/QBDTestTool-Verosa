"""
Data loader workers for QuickBooks Desktop Test Tool.

Background workers for loading data from QuickBooks (items, terms, classes, accounts, customers).
"""

from tkinter import messagebox
from qb_data_loader import QBDataLoader
from store import set_items, set_terms, set_classes, set_accounts
from qb_ipc_client import disconnect_qb
from app_logging import LOG_NORMAL, LOG_VERBOSE


def load_items_worker(app):
    """Worker function to load items in background."""
    try:
        app.root.after(0, lambda: app._log_create("Loading items from QuickBooks..."))

        # Load items from QuickBooks
        result = QBDataLoader.load_items()

        if result['success']:
            items = result['data']
            count = result['count']

            # Dispatch to store
            app.store.dispatch(set_items(items))

            # Update UI
            app.root.after(0, lambda: app._log_create(f"✓ Loaded {count} items from QuickBooks"))
            app.root.after(0, lambda: app.items_status_label.config(
                text=f"{count} item{'s' if count != 1 else ''} loaded", foreground='green'
            ))

            # Update setup summary - only show ready when BOTH are loaded
            state = app.store.get_state()
            num_customers = len(state.customers)
            if num_customers > 0 and count > 0:
                app.root.after(0, lambda: app.setup_summary_label.config(
                    text=f"{num_customers} customers, {count} items loaded - Ready to create transactions"
                ))
            else:
                app.root.after(0, lambda: app.setup_summary_label.config(
                    text=f"{num_customers} customers, {count} items loaded - Load both to begin"
                ))
        else:
            error_msg = result['error']
            app.root.after(0, lambda: app._log_create(f"✗ Error loading items: {error_msg}"))
            app.root.after(0, lambda: messagebox.showerror("Error", error_msg))

    except Exception as e:
        error_str = str(e)
        app.root.after(0, lambda: app._log_create(f"✗ Error: {error_str}"))
        app.root.after(0, lambda: messagebox.showerror("Error", error_str))
    finally:
        app.root.after(0, lambda: app.load_items_btn.config(state='normal'))
        app.root.after(0, lambda: app.status_bar.config(text="Ready"))


def load_terms_worker(app):
    """Worker function to load terms in background."""
    try:
        app.root.after(0, lambda: app._log_create("Loading terms from QuickBooks..."))

        # Load terms from QuickBooks
        result = QBDataLoader.load_terms()

        if result['success']:
            terms = result['data']
            count = result['count']

            # Dispatch to store
            app.store.dispatch(set_terms(terms))

            # Update UI
            app.root.after(0, lambda: app._log_create(f"✓ Loaded {count} terms from QuickBooks"))
            app.root.after(0, lambda: app.terms_status_label.config(
                text=f"{count} term{'s' if count != 1 else ''} loaded", foreground='green'
            ))

            # Update invoice terms dropdown
            term_names = ['(None)'] + [term['name'] for term in terms]
            app.root.after(0, lambda: app.invoice_terms_combo.config(values=term_names))
        else:
            error_msg = result['error']
            app.root.after(0, lambda: app._log_create(f"✗ Error loading terms: {error_msg}"))
            app.root.after(0, lambda: messagebox.showerror("Error", error_msg))

    except Exception as e:
        error_str = str(e)
        app.root.after(0, lambda: app._log_create(f"✗ Error: {error_str}"))
        app.root.after(0, lambda: messagebox.showerror("Error", error_str))
    finally:
        app.root.after(0, lambda: app.load_terms_btn.config(state='normal'))
        app.root.after(0, lambda: app.status_bar.config(text="Ready"))


def load_classes_worker(app):
    """Worker function to load classes in background."""
    try:
        app.root.after(0, lambda: app._log_create("Loading classes from QuickBooks..."))

        # Load classes from QuickBooks
        result = QBDataLoader.load_classes()

        if result['success']:
            classes = result['data']
            count = result['count']

            # Dispatch to store
            app.store.dispatch(set_classes(classes))

            # Update UI
            app.root.after(0, lambda: app._log_create(f"✓ Loaded {count} classes from QuickBooks"))
            app.root.after(0, lambda: app.classes_status_label.config(
                text=f"{count} class{'es' if count != 1 else ''} loaded", foreground='green'
            ))

            # Update invoice class dropdown
            class_names = ['(None)'] + [cls['full_name'] for cls in classes]
            app.root.after(0, lambda: app.invoice_class_combo.config(values=class_names))
        else:
            error_msg = result['error']
            app.root.after(0, lambda: app._log_create(f"✗ Error loading classes: {error_msg}"))
            app.root.after(0, lambda: messagebox.showerror("Error", error_msg))

    except Exception as e:
        error_str = str(e)
        app.root.after(0, lambda: app._log_create(f"✗ Error: {error_str}"))
        app.root.after(0, lambda: messagebox.showerror("Error", error_str))
    finally:
        app.root.after(0, lambda: app.load_classes_btn.config(state='normal'))
        app.root.after(0, lambda: app.status_bar.config(text="Ready"))


def load_accounts_worker(app):
    """Worker function to load accounts in background."""
    try:
        app.root.after(0, lambda: app._log_create("Loading accounts from QuickBooks..."))

        # Load accounts from QuickBooks (filtered for deposit accounts)
        result = QBDataLoader.load_accounts(filter_deposit_accounts=True)

        if result['success']:
            deposit_accounts = result['data']
            count = result['count']

            # Dispatch to store
            app.store.dispatch(set_accounts(deposit_accounts))

            # Update UI
            app.root.after(0, lambda: app._log_create(f"✓ Loaded {count} deposit accounts from QuickBooks"))
            app.root.after(0, lambda: app.accounts_status_label.config(
                text=f"{count} account{'s' if count != 1 else ''} loaded", foreground='green'
            ))

            # Update deposit account dropdown in Monitor tab
            app.root.after(0, app._update_accounts_combo)
        else:
            error_msg = result['error']
            app.root.after(0, lambda: app._log_create(f"✗ Error loading accounts: {error_msg}"))
            app.root.after(0, lambda: messagebox.showerror("Error", error_msg))

    except Exception as e:
        error_str = str(e)
        app.root.after(0, lambda: app._log_create(f"✗ Error: {error_str}"))
        app.root.after(0, lambda: messagebox.showerror("Error", error_str))
    finally:
        app.root.after(0, lambda: app.load_accounts_btn.config(state='normal'))
        app.root.after(0, lambda: app.status_bar.config(text="Ready"))


def load_customers_worker(app):
    """Worker function to load customers in background."""
    try:
        app.root.after(0, lambda: app._log_create("Loading customers from QuickBooks..."))

        # Load customers from QuickBooks (already marked with created_by_app = False)
        result = QBDataLoader.load_customers()

        if result['success']:
            loaded_customers = result['data']
            count = result['count']

            # Dispatch to store (replaces existing customer list)
            app.store.dispatch({'type': 'SET_CUSTOMERS', 'payload': loaded_customers})

            # Update UI
            app.root.after(0, lambda: app._log_create(f"✓ Loaded {count} customers from QuickBooks"))
            app.root.after(0, app._update_customer_combo)
        else:
            error_msg = result['error']
            app.root.after(0, lambda: app._log_create(f"✗ Error loading customers: {error_msg}"))
            app.root.after(0, lambda: messagebox.showerror("Error", error_msg))

    except Exception as e:
        error_str = str(e)
        app.root.after(0, lambda: app._log_create(f"✗ Error: {error_str}"))
        app.root.after(0, lambda: messagebox.showerror("Error", error_str))
    finally:
        app.root.after(0, lambda: app.load_customers_btn.config(state='normal'))
        app.root.after(0, lambda: app.status_bar.config(text="Ready"))


def load_all_worker(app):
    """Worker function to load all data sequentially in background."""
    try:
        app._log_create("Starting Load All...")

        # Load customers
        app.root.after(0, lambda: app._log_create("Loading customers...", LOG_VERBOSE))
        result = QBDataLoader.load_customers()
        if result['success']:
            app.store.dispatch({'type': 'SET_CUSTOMERS', 'payload': result['data']})
            app.root.after(0, lambda: app._log_create(f"✓ Loaded {result['count']} customers", LOG_VERBOSE))
            app.root.after(0, app._update_customer_combo)
        else:
            raise Exception(f"Failed to load customers: {result['error']}")

        # Load items
        app.root.after(0, lambda: app._log_create("Loading items...", LOG_VERBOSE))
        result = QBDataLoader.load_items()
        if result['success']:
            app.store.dispatch(set_items(result['data']))
            count = result['count']
            app.root.after(0, lambda c=count: app._log_create(f"✓ Loaded {c} items", LOG_VERBOSE))
            app.root.after(0, lambda c=count: app.items_status_label.config(
                text=f"{c} item{'s' if c != 1 else ''} loaded", foreground='green'
            ))
        else:
            raise Exception(f"Failed to load items: {result['error']}")

        # Load terms
        app.root.after(0, lambda: app._log_create("Loading terms...", LOG_VERBOSE))
        result = QBDataLoader.load_terms()
        if result['success']:
            terms = result['data']
            app.store.dispatch(set_terms(terms))
            count = result['count']
            app.root.after(0, lambda c=count: app._log_create(f"✓ Loaded {c} terms", LOG_VERBOSE))
            app.root.after(0, lambda c=count: app.terms_status_label.config(
                text=f"{c} term{'s' if c != 1 else ''} loaded", foreground='green'
            ))
            term_names = ['(None)'] + [term['name'] for term in terms]
            app.root.after(0, lambda tn=term_names: app.txn_terms_combo.config(values=tn))
        else:
            raise Exception(f"Failed to load terms: {result['error']}")

        # Load classes
        app.root.after(0, lambda: app._log_create("Loading classes...", LOG_VERBOSE))
        result = QBDataLoader.load_classes()
        if result['success']:
            classes = result['data']
            app.store.dispatch(set_classes(classes))
            count = result['count']
            app.root.after(0, lambda c=count: app._log_create(f"✓ Loaded {c} classes", LOG_VERBOSE))
            app.root.after(0, lambda c=count: app.classes_status_label.config(
                text=f"{c} class{'es' if c != 1 else ''} loaded", foreground='green'
            ))
            class_names = ['(None)'] + [cls['full_name'] for cls in classes]
            app.root.after(0, lambda cn=class_names: app.txn_class_combo.config(values=cn))
        else:
            raise Exception(f"Failed to load classes: {result['error']}")

        # Load accounts
        app.root.after(0, lambda: app._log_create("Loading accounts...", LOG_VERBOSE))
        result = QBDataLoader.load_accounts(filter_deposit_accounts=True)
        if result['success']:
            app.store.dispatch(set_accounts(result['data']))
            count = result['count']
            app.root.after(0, lambda c=count: app._log_create(f"✓ Loaded {c} deposit accounts", LOG_VERBOSE))
            app.root.after(0, lambda c=count: app.accounts_status_label.config(
                text=f"{c} account{'s' if c != 1 else ''} loaded", foreground='green'
            ))
            app.root.after(0, app._update_accounts_combo)
        else:
            raise Exception(f"Failed to load accounts: {result['error']}")

        app.root.after(0, lambda: app._log_create("✓ Load All complete!"))
        app.root.after(0, lambda: messagebox.showinfo("Success", "All data loaded successfully!"))

    except Exception as e:
        error_str = str(e)
        app.root.after(0, lambda es=error_str: app._log_create(f"✗ Error during Load All: {es}"))
        app.root.after(0, lambda es=error_str: messagebox.showerror("Error", es))
    finally:
        # Disconnect from QuickBooks after batch operation completes
        disconnect_qb()
        app.root.after(0, lambda: app.load_all_btn.config(state='normal'))
        app.root.after(0, lambda: app.status_bar.config(text="Ready"))
