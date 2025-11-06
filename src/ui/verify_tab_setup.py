"""
Verification Results tab setup for QuickBooks Desktop Test Tool.
"""

from tkinter import ttk


def setup_verify_tab(app):
    """
    Setup the Verification Results tab.

    Args:
        app: Reference to the main QBDTestToolApp instance
    """
    # Results tree
    tree_frame = ttk.Frame(app.verify_tab, padding=10)
    tree_frame.pack(fill='both', expand=True)

    columns = ('Timestamp', 'Type', 'Txn Ref#', 'Result', 'Details')
    app.verify_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=20)

    # Set column widths
    app.verify_tree.heading('Timestamp', text='Timestamp')
    app.verify_tree.column('Timestamp', width=150)

    app.verify_tree.heading('Type', text='Type')
    app.verify_tree.column('Type', width=120)

    app.verify_tree.heading('Txn Ref#', text='Txn Ref#')
    app.verify_tree.column('Txn Ref#', width=100)

    app.verify_tree.heading('Result', text='Result')
    app.verify_tree.column('Result', width=80)

    app.verify_tree.heading('Details', text='Details')
    app.verify_tree.column('Details', width=600)

    app.verify_tree.pack(fill='both', expand=True)

    # Scrollbar
    scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=app.verify_tree.yview)
    scrollbar.pack(side='right', fill='y')
    app.verify_tree.configure(yscrollcommand=scrollbar.set)
