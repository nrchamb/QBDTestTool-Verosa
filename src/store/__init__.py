"""
Redux-like store package for QuickBooks Desktop Test Tool.

This package provides a clean separation of concerns following Redux patterns:
- state.py: State dataclasses and type definitions
- actions.py: Action creators
- reducers.py: Pure reducer functions
- store.py: Store class for state management

Public API exports all necessary components for consumers.
"""

# State types
from .state import (
    AppState,
    InvoiceRecord,
    SalesReceiptRecord,
    StatementChargeRecord,
)

# Store
from .store import Store

# Action creators
from .actions import (
    # Customer actions
    add_customer,
    set_customers,
    # Item actions
    set_items,
    # Terms actions
    set_terms,
    # Class actions
    set_classes,
    # Account actions
    set_accounts,
    # Invoice actions
    add_invoice,
    update_invoice,
    # Sales receipt actions
    add_sales_receipt,
    update_sales_receipt,
    set_sales_receipts,
    # Statement charge actions
    add_statement_charge,
    update_statement_charge,
    set_statement_charges,
    # Monitoring actions
    set_monitoring,
    # Verification actions
    add_verification_result,
    # Sync actions
    update_last_sync,
    # Configuration actions
    set_expected_deposit_account,
)

__all__ = [
    # State
    'AppState',
    'InvoiceRecord',
    'SalesReceiptRecord',
    'StatementChargeRecord',
    # Store
    'Store',
    # Actions
    'add_customer',
    'set_customers',
    'set_items',
    'set_terms',
    'set_classes',
    'set_accounts',
    'add_invoice',
    'update_invoice',
    'add_sales_receipt',
    'update_sales_receipt',
    'set_sales_receipts',
    'add_statement_charge',
    'update_statement_charge',
    'set_statement_charges',
    'set_monitoring',
    'add_verification_result',
    'update_last_sync',
    'set_expected_deposit_account',
]
