"""
Reducers for Redux-like store.

Pure functions that take current state and action, return new state.
"""

from typing import Any, Dict
from .state import AppState

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
