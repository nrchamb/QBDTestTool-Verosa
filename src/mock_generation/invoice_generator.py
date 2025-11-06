"""
Invoice data generator for QuickBooks test data.
"""

from faker import Faker
from typing import Dict, Any, Optional
from datetime import datetime
import random

fake = Faker()


class InvoiceGenerator:
    """Generate randomized invoice data for QuickBooks testing."""

    @staticmethod
    def generate_invoice_data(
        customer_ref: str,
        num_line_items: int = None,
        item_refs: list = None,
        total_amount: float = None,
        txn_date: str = None,
        po_prefix: str = None,
        terms_ref: str = None,
        class_ref: str = None
    ) -> Dict[str, Any]:
        """
        Generate invoice data.

        Args:
            customer_ref: Customer ListID
            num_line_items: Number of line items (random 1-5 if not specified)
            item_refs: List of item ListIDs to use (will use placeholders if not provided)
            total_amount: Target total amount (will randomize if not specified)
            txn_date: Transaction date (defaults to today)
            po_prefix: PO number prefix (e.g., "PO-") - will generate random 5-digit number if provided
            terms_ref: Terms ListID (optional)
            class_ref: Class ListID (optional)

        Returns:
            Dict suitable for QBXMLBuilder.build_invoice_add()

        Note:
            If item_refs is None, you'll need to query items from QB first,
            or use service items that exist in the test company file.
        """
        if num_line_items is None:
            num_line_items = random.randint(1, 5)

        if total_amount is None:
            total_amount = round(random.uniform(100, 5000), 2)

        # Generate line items
        line_items = []
        remaining_amount = total_amount

        for i in range(num_line_items):
            # Last item gets remaining amount, others get random portion
            if i == num_line_items - 1:
                line_amount = remaining_amount
            else:
                line_amount = round(remaining_amount * random.uniform(0.2, 0.5), 2)
                remaining_amount -= line_amount

            quantity = random.randint(1, 10)
            rate = round(line_amount / quantity, 2)

            line_item = {
                'desc': fake.catch_phrase(),
                'quantity': quantity,
                'rate': rate
            }

            # Add item reference if provided
            if item_refs and i < len(item_refs):
                line_item['item_ref'] = item_refs[i]

            line_items.append(line_item)

        invoice_data = {
            'customer_ref': customer_ref,
            'txn_date': txn_date if txn_date else datetime.now().strftime('%Y-%m-%d'),
            'ref_number': f"INV-{random.randint(10000, 99999)}",
            'line_items': line_items,
            'memo': f"Test invoice - {fake.sentence()}"
        }

        # Add optional PO number
        if po_prefix:
            invoice_data['po_number'] = f"{po_prefix}{random.randint(10000, 99999)}"

        # Add optional terms reference
        if terms_ref:
            invoice_data['terms_ref'] = terms_ref

        # Add optional class reference
        if class_ref:
            invoice_data['class_ref'] = class_ref

        return invoice_data
