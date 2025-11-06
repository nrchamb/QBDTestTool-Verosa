"""
State definitions for Redux-like store.

Contains all dataclasses representing application state structure.
"""

from typing import Any, Dict, List
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
    initial_memo: str = None  # Track memo at creation for validation


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
    initial_memo: str = None  # Track memo at creation for validation


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
