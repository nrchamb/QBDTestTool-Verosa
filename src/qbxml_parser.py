"""
QBXML response parser for QuickBooks Desktop operations.
"""

from lxml import etree
from typing import Dict, Any, List, Optional


class QBXMLParser:
    """Helper class to parse QBXML responses."""

    @staticmethod
    def parse_response(xml_string: str) -> Dict[str, Any]:
        """
        Parse QBXML response and return structured data.

        Returns:
            Dict with 'success' (bool), 'data' (parsed content), 'error' (if failed)
        """
        try:
            root = etree.fromstring(xml_string.encode('utf-8'))

            # Check for errors
            status_code = root.xpath('//QBXMLMsgsRs/*/@statusCode')
            if status_code and status_code[0] != '0':
                status_msg = root.xpath('//QBXMLMsgsRs/*/@statusMessage')
                return {
                    'success': False,
                    'error': status_msg[0] if status_msg else 'Unknown error',
                    'status_code': status_code[0]
                }

            # Determine response type
            response_type = root.xpath('local-name(//QBXMLMsgsRs/*[1])')

            if response_type == 'CustomerAddRs':
                return QBXMLParser._parse_customer_response(root)
            elif response_type == 'CustomerQueryRs':
                return QBXMLParser._parse_customer_query_response(root)
            elif response_type == 'InvoiceAddRs':
                return QBXMLParser._parse_invoice_add_response(root)
            elif response_type == 'InvoiceQueryRs':
                return QBXMLParser._parse_invoice_query_response(root)
            elif response_type == 'InvoiceModRs':
                return QBXMLParser._parse_invoice_mod_response(root)
            elif response_type == 'SalesReceiptAddRs':
                return QBXMLParser._parse_sales_receipt_add_response(root)
            elif response_type == 'SalesReceiptQueryRs':
                return QBXMLParser._parse_sales_receipt_query_response(root)
            elif response_type == 'ChargeAddRs':
                return QBXMLParser._parse_charge_add_response(root)
            elif response_type == 'ChargeQueryRs':
                return QBXMLParser._parse_charge_query_response(root)
            elif response_type == 'AccountQueryRs':
                return QBXMLParser._parse_account_query_response(root)
            elif response_type == 'ItemQueryRs':
                return QBXMLParser._parse_item_query_response(root)
            elif response_type == 'StandardTermsQueryRs':
                return QBXMLParser._parse_terms_query_response(root)
            elif response_type == 'ClassQueryRs':
                return QBXMLParser._parse_class_query_response(root)
            else:
                return {'success': True, 'data': {'response_type': response_type}}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _parse_customer_response(root: etree.Element) -> Dict[str, Any]:
        """Parse CustomerAddRs response."""
        customer = root.xpath('//CustomerRet')[0] if root.xpath('//CustomerRet') else None

        if not customer:
            return {'success': False, 'error': 'No customer data in response'}

        return {
            'success': True,
            'data': {
                'list_id': customer.findtext('ListID'),
                'name': customer.findtext('Name'),
                'full_name': customer.findtext('FullName'),
                'edit_sequence': customer.findtext('EditSequence')
            }
        }

    @staticmethod
    def _parse_customer_query_response(root: etree.Element) -> Dict[str, Any]:
        """Parse CustomerQueryRs response."""
        customers = root.xpath('//CustomerRet')

        if not customers:
            return {'success': True, 'data': {'customers': []}}

        customer_list = []
        for customer in customers:
            customer_list.append({
                'list_id': customer.findtext('ListID'),
                'name': customer.findtext('Name'),
                'full_name': customer.findtext('FullName'),
                'email': customer.findtext('Email') or '',
                'is_active': customer.findtext('IsActive') == 'true',
                'balance': float(customer.findtext('Balance', '0'))
            })

        return {'success': True, 'data': {'customers': customer_list}}

    @staticmethod
    def _parse_invoice_add_response(root: etree.Element) -> Dict[str, Any]:
        """Parse InvoiceAddRs response."""
        invoice = root.xpath('//InvoiceRet')[0] if root.xpath('//InvoiceRet') else None

        if not invoice:
            return {'success': False, 'error': 'No invoice data in response'}

        return {
            'success': True,
            'data': {
                'txn_id': invoice.findtext('TxnID'),
                'ref_number': invoice.findtext('RefNumber'),
                'txn_date': invoice.findtext('TxnDate'),
                'customer_ref': {
                    'list_id': invoice.find('CustomerRef/ListID').text if invoice.find('CustomerRef/ListID') is not None else None,
                    'full_name': invoice.find('CustomerRef/FullName').text if invoice.find('CustomerRef/FullName') is not None else None
                },
                'subtotal': invoice.findtext('Subtotal'),
                'balance_remaining': invoice.findtext('BalanceRemaining'),
                'is_paid': invoice.findtext('IsPaid') == 'true',
                'edit_sequence': invoice.findtext('EditSequence')
            }
        }

    @staticmethod
    def _parse_invoice_query_response(root: etree.Element) -> Dict[str, Any]:
        """Parse InvoiceQueryRs response."""
        invoices = root.xpath('//InvoiceRet')

        if not invoices:
            return {'success': True, 'data': {'invoices': []}}

        invoice_list = []
        for invoice in invoices:
            invoice_data = {
                'txn_id': invoice.findtext('TxnID'),
                'ref_number': invoice.findtext('RefNumber'),
                'txn_date': invoice.findtext('TxnDate'),
                'customer_ref': {
                    'list_id': invoice.find('CustomerRef/ListID').text if invoice.find('CustomerRef/ListID') is not None else None,
                    'full_name': invoice.find('CustomerRef/FullName').text if invoice.find('CustomerRef/FullName') is not None else None
                },
                'subtotal': float(invoice.findtext('Subtotal', '0')),
                'balance_remaining': float(invoice.findtext('BalanceRemaining', '0')),
                'is_paid': invoice.findtext('IsPaid') == 'true',
                'is_pending': invoice.findtext('IsPending') == 'true',
                'edit_sequence': invoice.findtext('EditSequence'),
                'time_modified': invoice.findtext('TimeModified')
            }

            # Parse deposit/payment info if present
            deposit_to_account_ref = invoice.find('DepositToAccountRef')
            if deposit_to_account_ref is not None:
                invoice_data['deposit_account'] = {
                    'list_id': deposit_to_account_ref.findtext('ListID'),
                    'full_name': deposit_to_account_ref.findtext('FullName')
                }

            # Parse linked transactions (payments)
            linked_txns = invoice.xpath('LinkedTxn')
            if linked_txns:
                invoice_data['linked_transactions'] = []
                for linked in linked_txns:
                    linked_data = {
                        'txn_id': linked.findtext('TxnID'),
                        'txn_type': linked.findtext('TxnType'),
                        'txn_date': linked.findtext('TxnDate'),
                        'ref_number': linked.findtext('RefNumber'),
                        'amount': linked.findtext('Amount')
                    }

                    # Add payment method if available (typically requires separate payment query)
                    # For now, check if PaymentMethodRef is in the linked transaction
                    payment_method_ref = linked.find('PaymentMethodRef')
                    if payment_method_ref is not None:
                        linked_data['payment_method'] = payment_method_ref.findtext('FullName')

                    invoice_data['linked_transactions'].append(linked_data)

            invoice_list.append(invoice_data)

        return {'success': True, 'data': {'invoices': invoice_list}}

    @staticmethod
    def _parse_invoice_mod_response(root: etree.Element) -> Dict[str, Any]:
        """Parse InvoiceModRs response."""
        invoice = root.xpath('//InvoiceRet')[0] if root.xpath('//InvoiceRet') else None

        if not invoice:
            return {'success': False, 'error': 'No invoice data in response'}

        return {
            'success': True,
            'data': {
                'txn_id': invoice.findtext('TxnID'),
                'ref_number': invoice.findtext('RefNumber'),
                'is_pending': invoice.findtext('IsPending') == 'true',
                'edit_sequence': invoice.findtext('EditSequence')
            }
        }

    @staticmethod
    def _parse_sales_receipt_add_response(root: etree.Element) -> Dict[str, Any]:
        """Parse SalesReceiptAddRs response."""
        sales_receipt = root.xpath('//SalesReceiptRet')[0] if root.xpath('//SalesReceiptRet') else None

        if not sales_receipt:
            return {'success': False, 'error': 'No sales receipt data in response'}

        return {
            'success': True,
            'data': {
                'txn_id': sales_receipt.findtext('TxnID'),
                'ref_number': sales_receipt.findtext('RefNumber'),
                'txn_date': sales_receipt.findtext('TxnDate'),
                'customer_ref': {
                    'list_id': sales_receipt.find('CustomerRef/ListID').text if sales_receipt.find('CustomerRef/ListID') is not None else None,
                    'full_name': sales_receipt.find('CustomerRef/FullName').text if sales_receipt.find('CustomerRef/FullName') is not None else None
                },
                'subtotal': sales_receipt.findtext('Subtotal'),
                'total_amount': sales_receipt.findtext('TotalAmount'),
                'balance_remaining': sales_receipt.findtext('BalanceRemaining'),
                'is_pending': sales_receipt.findtext('IsPending') == 'true',
                'edit_sequence': sales_receipt.findtext('EditSequence')
            }
        }

    @staticmethod
    def _parse_sales_receipt_query_response(root: etree.Element) -> Dict[str, Any]:
        """Parse SalesReceiptQueryRs response."""
        sales_receipts = root.xpath('//SalesReceiptRet')

        if not sales_receipts:
            return {'success': True, 'data': {'sales_receipts': []}}

        receipt_list = []
        for receipt in sales_receipts:
            receipt_data = {
                'txn_id': receipt.findtext('TxnID'),
                'ref_number': receipt.findtext('RefNumber'),
                'txn_date': receipt.findtext('TxnDate'),
                'txn_number': receipt.findtext('TxnNumber'),
                'customer_ref': {
                    'list_id': receipt.find('CustomerRef/ListID').text if receipt.find('CustomerRef/ListID') is not None else None,
                    'full_name': receipt.find('CustomerRef/FullName').text if receipt.find('CustomerRef/FullName') is not None else None
                },
                'subtotal': float(receipt.findtext('Subtotal', '0')),
                'total_amount': float(receipt.findtext('TotalAmount', '0')),
                'balance_remaining': float(receipt.findtext('BalanceRemaining', '0')),
                'is_pending': receipt.findtext('IsPending') == 'true',
                'is_to_be_printed': receipt.findtext('IsToBePrinted') == 'true',
                'is_to_be_emailed': receipt.findtext('IsToBeEmailed') == 'true',
                'edit_sequence': receipt.findtext('EditSequence'),
                'time_modified': receipt.findtext('TimeModified'),
                'time_created': receipt.findtext('TimeCreated')
            }

            # Parse deposit account if present
            deposit_to_account_ref = receipt.find('DepositToAccountRef')
            if deposit_to_account_ref is not None:
                receipt_data['deposit_account'] = {
                    'list_id': deposit_to_account_ref.findtext('ListID'),
                    'full_name': deposit_to_account_ref.findtext('FullName')
                }

            receipt_list.append(receipt_data)

        return {'success': True, 'data': {'sales_receipts': receipt_list}}

    @staticmethod
    def _parse_account_query_response(root: etree.Element) -> Dict[str, Any]:
        """Parse AccountQueryRs response."""
        accounts = root.xpath('//AccountRet')

        if not accounts:
            return {'success': True, 'data': {'accounts': []}}

        account_list = []
        for account in accounts:
            account_list.append({
                'list_id': account.findtext('ListID'),
                'name': account.findtext('Name'),
                'full_name': account.findtext('FullName'),
                'account_type': account.findtext('AccountType'),
                'balance': float(account.findtext('Balance', '0')),
                'account_number': account.findtext('AccountNumber')
            })

        return {'success': True, 'data': {'accounts': account_list}}

    @staticmethod
    def _parse_item_query_response(root: etree.Element) -> Dict[str, Any]:
        """Parse ItemQueryRs response."""
        # Items can be of different types (Service, Inventory, NonInventory, etc.)
        # We'll look for common item types
        item_types = ['ItemServiceRet', 'ItemInventoryRet', 'ItemNonInventoryRet',
                      'ItemOtherChargeRet', 'ItemDiscountRet']

        items = []
        for item_type in item_types:
            found_items = root.xpath(f'//{item_type}')
            for item in found_items:
                items.append({
                    'list_id': item.findtext('ListID'),
                    'name': item.findtext('Name'),
                    'full_name': item.findtext('FullName'),
                    'type': item_type.replace('Item', '').replace('Ret', ''),
                    'description': item.findtext('SalesOrPurchaseDesc') or item.findtext('SalesDesc') or '',
                    'is_active': item.findtext('IsActive') == 'true'
                })

        return {'success': True, 'data': {'items': items}}

    @staticmethod
    def _parse_charge_add_response(root: etree.Element) -> Dict[str, Any]:
        """Parse ChargeAddRs response."""
        charge = root.xpath('//ChargeRet')[0] if root.xpath('//ChargeRet') else None

        if not charge:
            return {'success': False, 'error': 'No charge data in response'}

        return {
            'success': True,
            'data': {
                'txn_id': charge.findtext('TxnID'),
                'txn_date': charge.findtext('TxnDate'),
                'customer_ref': {
                    'list_id': charge.find('CustomerRef/ListID').text if charge.find('CustomerRef/ListID') is not None else None,
                    'full_name': charge.find('CustomerRef/FullName').text if charge.find('CustomerRef/FullName') is not None else None
                },
                'amount': charge.findtext('Amount'),
                'quantity': charge.findtext('Quantity'),
                'memo': charge.findtext('Memo'),
                'edit_sequence': charge.findtext('EditSequence')
            }
        }

    @staticmethod
    def _parse_charge_query_response(root: etree.Element) -> Dict[str, Any]:
        """Parse ChargeQueryRs response."""
        charges = root.xpath('//ChargeRet')

        if not charges:
            return {'success': True, 'data': {'charges': []}}

        charges_list = []
        for charge in charges:
            charges_list.append({
                'txn_id': charge.findtext('TxnID'),
                'ref_number': charge.findtext('RefNumber'),
                'txn_date': charge.findtext('TxnDate'),
                'customer_ref': {
                    'list_id': charge.find('CustomerRef/ListID').text if charge.find('CustomerRef/ListID') is not None else None,
                    'full_name': charge.find('CustomerRef/FullName').text if charge.find('CustomerRef/FullName') is not None else None
                },
                'amount': float(charge.findtext('Amount')) if charge.findtext('Amount') else 0.0,
                'quantity': charge.findtext('Quantity'),
                'desc': charge.findtext('Desc'),
                'edit_sequence': charge.findtext('EditSequence')
            })

        return {'success': True, 'data': {'charges': charges_list}}

    @staticmethod
    def _parse_terms_query_response(root: etree.Element) -> Dict[str, Any]:
        """Parse StandardTermsQueryRs response."""
        terms_list = root.xpath('//StandardTermsRet')

        if not terms_list:
            return {'success': True, 'data': {'terms': []}}

        terms = []
        for term in terms_list:
            terms.append({
                'list_id': term.findtext('ListID'),
                'name': term.findtext('Name'),
                'is_active': term.findtext('IsActive') == 'true',
                'std_due_days': term.findtext('StdDueDays'),
                'std_discount_days': term.findtext('StdDiscountDays'),
                'discount_pct': term.findtext('DiscountPct')
            })

        return {'success': True, 'data': {'terms': terms}}

    @staticmethod
    def _parse_class_query_response(root: etree.Element) -> Dict[str, Any]:
        """Parse ClassQueryRs response."""
        classes_list = root.xpath('//ClassRet')

        if not classes_list:
            return {'success': True, 'data': {'classes': []}}

        classes = []
        for cls in classes_list:
            classes.append({
                'list_id': cls.findtext('ListID'),
                'name': cls.findtext('Name'),
                'full_name': cls.findtext('FullName'),
                'is_active': cls.findtext('IsActive') == 'true'
            })

        return {'success': True, 'data': {'classes': classes}}
