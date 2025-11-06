"""
Action creators for Redux-like store.

All action creators return action dictionaries with 'type' and optional 'payload'.
"""

from typing import Any, Dict, List
from datetime import datetime

from .state import InvoiceRecord, SalesReceiptRecord, StatementChargeRecord


# Customer actions
def add_customer(customer: Dict[str, Any]) -> Dict[str, Any]:
    """Create ADD_CUSTOMER action."""
    return {'type': 'ADD_CUSTOMER', 'payload': customer}


def set_customers(customers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create SET_CUSTOMERS action."""
    return {'type': 'SET_CUSTOMERS', 'payload': customers}


# Item actions
def set_items(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create SET_ITEMS action."""
    return {'type': 'SET_ITEMS', 'payload': items}


# Terms actions
def set_terms(terms: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create SET_TERMS action."""
    return {'type': 'SET_TERMS', 'payload': terms}


# Class actions
def set_classes(classes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create SET_CLASSES action."""
    return {'type': 'SET_CLASSES', 'payload': classes}


# Account actions
def set_accounts(accounts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create SET_ACCOUNTS action."""
    return {'type': 'SET_ACCOUNTS', 'payload': accounts}


# Invoice actions
def add_invoice(invoice: InvoiceRecord) -> Dict[str, Any]:
    """Create ADD_INVOICE action."""
    return {'type': 'ADD_INVOICE', 'payload': invoice}


def update_invoice(invoice: InvoiceRecord) -> Dict[str, Any]:
    """Create UPDATE_INVOICE action."""
    return {'type': 'UPDATE_INVOICE', 'payload': invoice}


# Sales receipt actions
def add_sales_receipt(sales_receipt: SalesReceiptRecord) -> Dict[str, Any]:
    """Create ADD_SALES_RECEIPT action."""
    return {'type': 'ADD_SALES_RECEIPT', 'payload': sales_receipt}


def update_sales_receipt(sales_receipt: SalesReceiptRecord) -> Dict[str, Any]:
    """Create UPDATE_SALES_RECEIPT action."""
    return {'type': 'UPDATE_SALES_RECEIPT', 'payload': sales_receipt}


def set_sales_receipts(sales_receipts: List[SalesReceiptRecord]) -> Dict[str, Any]:
    """Create SET_SALES_RECEIPTS action."""
    return {'type': 'SET_SALES_RECEIPTS', 'payload': sales_receipts}


# Statement charge actions
def add_statement_charge(charge: StatementChargeRecord) -> Dict[str, Any]:
    """Create ADD_STATEMENT_CHARGE action."""
    return {'type': 'ADD_STATEMENT_CHARGE', 'payload': charge}


def update_statement_charge(charge: StatementChargeRecord) -> Dict[str, Any]:
    """Create UPDATE_STATEMENT_CHARGE action."""
    return {'type': 'UPDATE_STATEMENT_CHARGE', 'payload': charge}


def set_statement_charges(charges: List[StatementChargeRecord]) -> Dict[str, Any]:
    """Create SET_STATEMENT_CHARGES action."""
    return {'type': 'SET_STATEMENT_CHARGES', 'payload': charges}


# Monitoring actions
def set_monitoring(active: bool) -> Dict[str, Any]:
    """Create SET_MONITORING action."""
    return {'type': 'SET_MONITORING', 'payload': active}


# Verification actions
def add_verification_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """Create ADD_VERIFICATION_RESULT action."""
    return {'type': 'ADD_VERIFICATION_RESULT', 'payload': result}


# Sync actions
def update_last_sync(timestamp: datetime) -> Dict[str, Any]:
    """Create UPDATE_LAST_SYNC action."""
    return {'type': 'UPDATE_LAST_SYNC', 'payload': timestamp}


# Configuration actions
def set_expected_deposit_account(account_name: str) -> Dict[str, Any]:
    """Create SET_EXPECTED_DEPOSIT_ACCOUNT action."""
    return {'type': 'SET_EXPECTED_DEPOSIT_ACCOUNT', 'payload': account_name}
