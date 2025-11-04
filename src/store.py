"""
Simple Redux-like store pattern for state management.
"""

from typing import Callable, Any, Dict, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class InvoiceRecord:
    """Represents an invoice tracked by the application."""
    txn_id: str
    ref_number: str
    customer_name: str
    amount: float
    status: str  # 'open', 'closed'
    created_at: datetime
    last_checked: datetime = None
    deposit_account: str = None
    payment_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SalesReceiptRecord:
    """Represents a sales receipt tracked by the application."""
    txn_id: str
    ref_number: str
    customer_name: str
    amount: float
    status: str  # 'open' (unpaid), 'closed' (paid)
    created_at: datetime
    last_checked: datetime = None
    deposit_account: str = None
    payment_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StatementChargeRecord:
    """Represents a statement charge tracked by the application."""
    txn_id: str
    ref_number: str
    customer_name: str
    amount: float
    status: str  # Always 'completed' for charges
    created_at: datetime
    last_checked: datetime = None


@dataclass
class AppState:
    """Application state."""
    customers: List[Dict[str, Any]] = field(default_factory=list)
    items: List[Dict[str, Any]] = field(default_factory=list)
    terms: List[Dict[str, Any]] = field(default_factory=list)
    classes: List[Dict[str, Any]] = field(default_factory=list)
    accounts: List[Dict[str, Any]] = field(default_factory=list)
    invoices: List[InvoiceRecord] = field(default_factory=list)
    sales_receipts: List[SalesReceiptRecord] = field(default_factory=list)
    statement_charges: List[StatementChargeRecord] = field(default_factory=list)
    monitoring_active: bool = False
    last_sync: datetime = None
    verification_results: List[Dict[str, Any]] = field(default_factory=list)
    expected_deposit_account: str = None


class Store:
    """Simple Redux-like store for state management."""

    def __init__(self, initial_state: AppState = None):
        self._state = initial_state or AppState()
        self._listeners: List[Callable] = []

    def get_state(self) -> AppState:
        """Get current state (read-only)."""
        return self._state

    def dispatch(self, action: Dict[str, Any]) -> None:
        """Dispatch an action to update state."""
        self._state = reducer(self._state, action)
        self._notify_listeners()

    def subscribe(self, listener: Callable) -> Callable:
        """Subscribe to state changes. Returns unsubscribe function."""
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    def _notify_listeners(self) -> None:
        """Notify all listeners of state change."""
        for listener in self._listeners:
            listener()


def reducer(state: AppState, action: Dict[str, Any]) -> AppState:
    """Root reducer - updates state based on action type."""
    action_type = action.get('type')
    payload = action.get('payload', {})

    if action_type == 'ADD_CUSTOMER':
        return AppState(
            **{**state.__dict__, 'customers': state.customers + [payload]}
        )

    elif action_type == 'SET_CUSTOMERS':
        return AppState(
            **{**state.__dict__, 'customers': payload}
        )

    elif action_type == 'SET_ITEMS':
        return AppState(
            **{**state.__dict__, 'items': payload}
        )

    elif action_type == 'SET_TERMS':
        return AppState(
            **{**state.__dict__, 'terms': payload}
        )

    elif action_type == 'SET_CLASSES':
        return AppState(
            **{**state.__dict__, 'classes': payload}
        )

    elif action_type == 'SET_ACCOUNTS':
        return AppState(
            **{**state.__dict__, 'accounts': payload}
        )

    elif action_type == 'ADD_INVOICE':
        return AppState(
            **{**state.__dict__, 'invoices': state.invoices + [payload]}
        )

    elif action_type == 'UPDATE_INVOICE':
        updated_invoices = [
            payload if inv.txn_id == payload.txn_id else inv
            for inv in state.invoices
        ]
        return AppState(
            **{**state.__dict__, 'invoices': updated_invoices}
        )

    elif action_type == 'ADD_SALES_RECEIPT':
        return AppState(
            **{**state.__dict__, 'sales_receipts': state.sales_receipts + [payload]}
        )

    elif action_type == 'UPDATE_SALES_RECEIPT':
        updated_receipts = [
            payload if sr.txn_id == payload.txn_id else sr
            for sr in state.sales_receipts
        ]
        return AppState(
            **{**state.__dict__, 'sales_receipts': updated_receipts}
        )

    elif action_type == 'SET_SALES_RECEIPTS':
        return AppState(
            **{**state.__dict__, 'sales_receipts': payload}
        )

    elif action_type == 'ADD_STATEMENT_CHARGE':
        return AppState(
            **{**state.__dict__, 'statement_charges': state.statement_charges + [payload]}
        )

    elif action_type == 'UPDATE_STATEMENT_CHARGE':
        updated_charges = [
            payload if charge.txn_id == payload.txn_id else charge
            for charge in state.statement_charges
        ]
        return AppState(
            **{**state.__dict__, 'statement_charges': updated_charges}
        )

    elif action_type == 'SET_STATEMENT_CHARGES':
        return AppState(
            **{**state.__dict__, 'statement_charges': payload}
        )

    elif action_type == 'SET_MONITORING':
        return AppState(
            **{**state.__dict__, 'monitoring_active': payload}
        )

    elif action_type == 'ADD_VERIFICATION_RESULT':
        return AppState(
            **{**state.__dict__, 'verification_results': state.verification_results + [payload]}
        )

    elif action_type == 'UPDATE_LAST_SYNC':
        return AppState(
            **{**state.__dict__, 'last_sync': payload}
        )

    elif action_type == 'SET_EXPECTED_DEPOSIT_ACCOUNT':
        return AppState(
            **{**state.__dict__, 'expected_deposit_account': payload}
        )

    return state


# Action creators
def add_customer(customer: Dict[str, Any]) -> Dict[str, Any]:
    """Create ADD_CUSTOMER action."""
    return {'type': 'ADD_CUSTOMER', 'payload': customer}


def set_items(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create SET_ITEMS action."""
    return {'type': 'SET_ITEMS', 'payload': items}


def set_terms(terms: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create SET_TERMS action."""
    return {'type': 'SET_TERMS', 'payload': terms}


def set_classes(classes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create SET_CLASSES action."""
    return {'type': 'SET_CLASSES', 'payload': classes}


def set_accounts(accounts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create SET_ACCOUNTS action."""
    return {'type': 'SET_ACCOUNTS', 'payload': accounts}


def add_invoice(invoice: InvoiceRecord) -> Dict[str, Any]:
    """Create ADD_INVOICE action."""
    return {'type': 'ADD_INVOICE', 'payload': invoice}


def update_invoice(invoice: InvoiceRecord) -> Dict[str, Any]:
    """Create UPDATE_INVOICE action."""
    return {'type': 'UPDATE_INVOICE', 'payload': invoice}


def add_sales_receipt(sales_receipt: SalesReceiptRecord) -> Dict[str, Any]:
    """Create ADD_SALES_RECEIPT action."""
    return {'type': 'ADD_SALES_RECEIPT', 'payload': sales_receipt}


def update_sales_receipt(sales_receipt: SalesReceiptRecord) -> Dict[str, Any]:
    """Create UPDATE_SALES_RECEIPT action."""
    return {'type': 'UPDATE_SALES_RECEIPT', 'payload': sales_receipt}


def set_sales_receipts(sales_receipts: List[SalesReceiptRecord]) -> Dict[str, Any]:
    """Create SET_SALES_RECEIPTS action."""
    return {'type': 'SET_SALES_RECEIPTS', 'payload': sales_receipts}


def add_statement_charge(charge: StatementChargeRecord) -> Dict[str, Any]:
    """Create ADD_STATEMENT_CHARGE action."""
    return {'type': 'ADD_STATEMENT_CHARGE', 'payload': charge}


def update_statement_charge(charge: StatementChargeRecord) -> Dict[str, Any]:
    """Create UPDATE_STATEMENT_CHARGE action."""
    return {'type': 'UPDATE_STATEMENT_CHARGE', 'payload': charge}


def set_statement_charges(charges: List[StatementChargeRecord]) -> Dict[str, Any]:
    """Create SET_STATEMENT_CHARGES action."""
    return {'type': 'SET_STATEMENT_CHARGES', 'payload': charges}


def set_monitoring(active: bool) -> Dict[str, Any]:
    """Create SET_MONITORING action."""
    return {'type': 'SET_MONITORING', 'payload': active}


def add_verification_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """Create ADD_VERIFICATION_RESULT action."""
    return {'type': 'ADD_VERIFICATION_RESULT', 'payload': result}


def update_last_sync(timestamp: datetime) -> Dict[str, Any]:
    """Create UPDATE_LAST_SYNC action."""
    return {'type': 'UPDATE_LAST_SYNC', 'payload': timestamp}


def set_expected_deposit_account(account_name: str) -> Dict[str, Any]:
    """Create SET_EXPECTED_DEPOSIT_ACCOUNT action."""
    return {'type': 'SET_EXPECTED_DEPOSIT_ACCOUNT', 'payload': account_name}
