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

    match action_type:
        case 'ADD_CUSTOMER':
            return AppState(
                **{**state.__dict__, 'customers': state.customers + [payload]}
            )

        case 'SET_CUSTOMERS':
            return AppState(
                **{**state.__dict__, 'customers': payload}
            )

        case 'SET_ITEMS':
            return AppState(
                **{**state.__dict__, 'items': payload}
            )

        case 'SET_TERMS':
            return AppState(
                **{**state.__dict__, 'terms': payload}
            )

        case 'SET_CLASSES':
            return AppState(
                **{**state.__dict__, 'classes': payload}
            )

        case 'SET_ACCOUNTS':
            return AppState(
                **{**state.__dict__, 'accounts': payload}
            )

        case 'ADD_INVOICE':
            return AppState(
                **{**state.__dict__, 'invoices': state.invoices + [payload]}
            )

        case 'UPDATE_INVOICE':
            updated_invoices = [
                payload if inv.txn_id == payload.txn_id else inv
                for inv in state.invoices
            ]
            return AppState(
                **{**state.__dict__, 'invoices': updated_invoices}
            )

        case 'ADD_SALES_RECEIPT':
            return AppState(
                **{**state.__dict__, 'sales_receipts': state.sales_receipts + [payload]}
            )

        case 'UPDATE_SALES_RECEIPT':
            updated_receipts = [
                payload if sr.txn_id == payload.txn_id else sr
                for sr in state.sales_receipts
            ]
            return AppState(
                **{**state.__dict__, 'sales_receipts': updated_receipts}
            )

        case 'SET_SALES_RECEIPTS':
            return AppState(
                **{**state.__dict__, 'sales_receipts': payload}
            )

        case 'ADD_STATEMENT_CHARGE':
            return AppState(
                **{**state.__dict__, 'statement_charges': state.statement_charges + [payload]}
            )

        case 'UPDATE_STATEMENT_CHARGE':
            updated_charges = [
                payload if charge.txn_id == payload.txn_id else charge
                for charge in state.statement_charges
            ]
            return AppState(
                **{**state.__dict__, 'statement_charges': updated_charges}
            )

        case 'SET_STATEMENT_CHARGES':
            return AppState(
                **{**state.__dict__, 'statement_charges': payload}
            )

        case 'SET_MONITORING':
            return AppState(
                **{**state.__dict__, 'monitoring_active': payload}
            )

        case 'ADD_VERIFICATION_RESULT':
            return AppState(
                **{**state.__dict__, 'verification_results': state.verification_results + [payload]}
            )

        case 'UPDATE_LAST_SYNC':
            return AppState(
                **{**state.__dict__, 'last_sync': payload}
            )

        case 'SET_EXPECTED_DEPOSIT_ACCOUNT':
            return AppState(
                **{**state.__dict__, 'expected_deposit_account': payload}
            )

        case _:
            # Default case - return unchanged state
            return state
