"""
Customer and job data generator for QuickBooks test data.
"""

from faker import Faker
from typing import Dict, Any, Optional
import random

fake = Faker()


class CustomerGenerator:
    """Generate randomized customer and job data for QuickBooks testing."""

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
