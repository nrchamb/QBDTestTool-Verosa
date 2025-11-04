"""
Test data generator for QuickBooks entities.
"""

from faker import Faker
from typing import Dict, Any, Optional
from datetime import datetime
import random

fake = Faker()


class TestDataGenerator:
    """Generate randomized test data for QuickBooks testing."""

    @staticmethod
    def generate_customer(
        email: str,
        field_config: Optional[Dict[str, bool]] = None,
        manual_values: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate customer data with configurable field randomization.

        Args:
            email: Required email address (user-provided)
            field_config: Dict of field names to boolean values indicating whether to randomize
                         Keys: first_name, last_name, company, phone, billing_address, shipping_address
                         If None, all fields default to True (randomized)
            manual_values: Dict of manual values to use when field_config[field] is False
                          Keys match field_config keys. If value is empty string or None, field is omitted.

        Returns:
            Dict suitable for QBXMLBuilder.build_customer_add()
        """
        # Default config: randomize all fields
        if field_config is None:
            field_config = {
                'first_name': True,
                'last_name': True,
                'company': True,
                'phone': True,
                'billing_address': True,
                'shipping_address': True
            }

        if manual_values is None:
            manual_values = {}

        # Generate or use manual values
        # If field_config[field] is True: generate random data
        # If field_config[field] is False: use manual_values[field] (which may be None/empty)
        if field_config.get('first_name', True):
            first_name = fake.first_name()
        else:
            first_name = manual_values.get('first_name') or None

        if field_config.get('last_name', True):
            last_name = fake.last_name()
        else:
            last_name = manual_values.get('last_name') or None

        if field_config.get('company', True):
            company_name = fake.company()
        else:
            company_name = manual_values.get('company') or None

        # Name field is required - use company if available, otherwise generate
        if company_name:
            name = f"{company_name}_{random.randint(1000, 9999)}"
        elif first_name and last_name:
            name = f"{first_name}_{last_name}_{random.randint(1000, 9999)}"
        else:
            # Fallback: always generate a unique name
            name = f"Customer_{random.randint(10000, 99999)}"

        # Start with required fields
        customer_data = {
            'name': name,
            'email': email
        }

        # Add optional fields if randomized
        if first_name:
            customer_data['first_name'] = first_name
        if last_name:
            customer_data['last_name'] = last_name
        if company_name:
            customer_data['company'] = company_name

        # Phone
        if field_config.get('phone', True):
            # Generate random phone number
            phone = f"({random.randint(100, 999)}) {random.randint(100, 999)}-{random.randint(1000, 9999)}"
            customer_data['phone'] = phone
        else:
            # Use manual value if provided
            phone = manual_values.get('phone')
            if phone:
                customer_data['phone'] = phone

        # Billing address
        if field_config.get('billing_address', True):
            # Generate random billing address
            customer_data['billing_address'] = {
                'addr1': fake.street_address(),
                'city': fake.city(),
                'state': fake.state_abbr(),
                'postal_code': fake.zipcode()
            }
        else:
            # Use manual value if provided
            billing_addr = manual_values.get('billing_address')
            if billing_addr:
                customer_data['billing_address'] = billing_addr

        # Shipping address
        if field_config.get('shipping_address', True):
            # Generate random shipping address
            # 70% chance shipping = billing (if billing exists), 30% different
            if 'billing_address' in customer_data and random.random() < 0.7:
                customer_data['shipping_address'] = customer_data['billing_address'].copy()
            else:
                customer_data['shipping_address'] = {
                    'addr1': fake.street_address(),
                    'city': fake.city(),
                    'state': fake.state_abbr(),
                    'postal_code': fake.zipcode()
                }
        else:
            # Use manual value if provided
            shipping_addr = manual_values.get('shipping_address')
            if shipping_addr:
                customer_data['shipping_address'] = shipping_addr

        return customer_data

    @staticmethod
    def generate_job(
        parent_customer_ref: str,
        email: str,
        job_name: Optional[str] = None,
        is_subjob: bool = False
    ) -> Dict[str, Any]:
        """
        Generate job data (sub-customer in QB).

        Args:
            parent_customer_ref: Parent customer/job ListID
            email: Required email address
            job_name: Optional job name (will be randomized if not provided)
            is_subjob: If True, generates sub-job naming pattern (Phase1, Task, etc.)
                      If False, generates job naming pattern (Renovation, Installation, etc.)

        Returns:
            Dict suitable for customer add with parent reference
        """
        if not job_name:
            if is_subjob:
                # Sub-job naming patterns
                subjob_types = ['Phase1', 'Phase2', 'Task', 'Milestone', 'Deliverable', 'Stage']
                job_name = f"{random.choice(subjob_types)}_{random.randint(100, 999)}"
            else:
                # Job naming patterns
                job_types = ['Renovation', 'Installation', 'Repair', 'Maintenance', 'Upgrade']
                job_name = f"{random.choice(job_types)}_{random.randint(100, 999)}"

        return {
            'name': job_name,
            'parent_ref': parent_customer_ref,
            'email': email,
            'job_status': random.choice(['Pending', 'Awarded', 'InProgress', 'Closed'])
        }

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

    @staticmethod
    def generate_sales_receipt_data(
        customer_ref: str,
        num_line_items: int = None,
        item_refs: list = None,
        total_amount: float = None,
        txn_date: str = None
    ) -> Dict[str, Any]:
        """
        Generate sales receipt data.

        Args:
            customer_ref: Customer ListID
            num_line_items: Number of line items (random 1-5 if not specified)
            item_refs: List of item ListIDs to use (will use placeholders if not provided)
            total_amount: Target total amount (will randomize if not specified)

        Returns:
            Dict suitable for QBXMLBuilder.build_sales_receipt_add()

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

        sales_receipt_data = {
            'customer_ref': customer_ref,
            'txn_date': txn_date if txn_date else datetime.now().strftime('%Y-%m-%d'),
            'ref_number': f"SR-{random.randint(10000, 99999)}",
            'line_items': line_items,
            'memo': f"Test sales receipt - {fake.sentence()}"
        }

        return sales_receipt_data

    @staticmethod
    def generate_statement_charge_data(
        customer_ref: str,
        amount: float = None,
        item_ref: str = None,
        txn_date: str = None
    ) -> Dict[str, Any]:
        """
        Generate statement charge data.

        Args:
            customer_ref: Customer ListID
            amount: Charge amount (will randomize if not specified)
            item_ref: Item ListID (optional - QB may use default if not provided)
            txn_date: Transaction date (defaults to today)

        Returns:
            Dict suitable for QBXMLBuilder.build_charge_add()
        """
        if amount is None:
            amount = round(random.uniform(50, 500), 2)

        charge_data = {
            'customer_ref': customer_ref,
            'txn_date': txn_date if txn_date else datetime.now().strftime('%Y-%m-%d'),
            'ref_number': f"CHG-{random.randint(10000, 99999)}",
            'amount': amount,
            'quantity': 1,
            'memo': f"Test statement charge - {fake.sentence()}"
        }

        # Add item reference if provided
        if item_ref:
            charge_data['item_ref'] = item_ref

        return charge_data
