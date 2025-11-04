"""
QBXML request builder for QuickBooks Desktop operations.
"""

from lxml import etree
from typing import Dict, Any, Optional
from datetime import datetime


class QBXMLBuilder:
    """Helper class to build QBXML requests."""

    @staticmethod
    def _create_base_qbxml() -> tuple:
        """Create base QBXML structure with proper processing instruction."""
        # Create processing instruction and wrap in tree
        pi = etree.ProcessingInstruction("qbxml", 'version="13.0"')
        qbxml = etree.Element("QBXML")
        qbxml_msgs_rq = etree.SubElement(qbxml, "QBXMLMsgsRq")
        qbxml_msgs_rq.set("onError", "stopOnError")

        # Create tree with PI first, then QBXML element
        tree = etree.ElementTree(qbxml)
        tree.getroot().addprevious(pi)

        return tree, qbxml, qbxml_msgs_rq

    @staticmethod
    def build_customer_add(customer_data: Dict[str, Any]) -> str:
        """
        Build CustomerAddRq QBXML request.

        Args:
            customer_data: Dict with keys: name, email, first_name, last_name,
                          company, phone, billing_address (optional), shipping_address (optional)
        """
        tree, qbxml, msgs_rq = QBXMLBuilder._create_base_qbxml()
        customer_add_rq = etree.SubElement(msgs_rq, "CustomerAddRq")
        customer_add_rq.set("requestID", "1")
        customer_add = etree.SubElement(customer_add_rq, "CustomerAdd")

        # IMPORTANT: Fields must be in this specific order per QBXML spec

        # 1. Name (required)
        name_elem = etree.SubElement(customer_add, "Name")
        name_elem.text = customer_data['name']

        # 2. ParentRef (optional) - for jobs/sub-customers
        if 'parent_ref' in customer_data:
            parent_ref = etree.SubElement(customer_add, "ParentRef")
            parent_list_id = etree.SubElement(parent_ref, "ListID")
            parent_list_id.text = customer_data['parent_ref']

        # 3. CompanyName (optional)
        if 'company' in customer_data:
            company_name = etree.SubElement(customer_add, "CompanyName")
            company_name.text = customer_data['company']

        # 4. FirstName (optional)
        if 'first_name' in customer_data:
            first_name = etree.SubElement(customer_add, "FirstName")
            first_name.text = customer_data['first_name']

        # 5. LastName (optional)
        if 'last_name' in customer_data:
            last_name = etree.SubElement(customer_add, "LastName")
            last_name.text = customer_data['last_name']

        # 6. BillAddress (optional)
        if 'billing_address' in customer_data:
            bill_addr = etree.SubElement(customer_add, "BillAddress")
            addr = customer_data['billing_address']
            for key, qb_field in [('addr1', 'Addr1'), ('addr2', 'Addr2'),
                                   ('city', 'City'), ('state', 'State'),
                                   ('postal_code', 'PostalCode')]:
                if key in addr:
                    elem = etree.SubElement(bill_addr, qb_field)
                    elem.text = addr[key]

        # 7. ShipAddress (optional)
        if 'shipping_address' in customer_data:
            ship_addr = etree.SubElement(customer_add, "ShipAddress")
            addr = customer_data['shipping_address']
            for key, qb_field in [('addr1', 'Addr1'), ('addr2', 'Addr2'),
                                   ('city', 'City'), ('state', 'State'),
                                   ('postal_code', 'PostalCode')]:
                if key in addr:
                    elem = etree.SubElement(ship_addr, qb_field)
                    elem.text = addr[key]

        # 8. Phone (optional) - comes AFTER addresses
        if 'phone' in customer_data:
            phone = etree.SubElement(customer_add, "Phone")
            phone.text = customer_data['phone']

        # 9. Email (optional) - comes AFTER phone
        if 'email' in customer_data:
            email = etree.SubElement(customer_add, "Email")
            email.text = customer_data['email']

        # Serialize with processing instruction included
        from io import BytesIO
        output = BytesIO()
        tree.write(output, xml_declaration=False, encoding='UTF-8', pretty_print=True)
        return output.getvalue().decode('utf-8')

    @staticmethod
    def build_invoice_add(invoice_data: Dict[str, Any]) -> str:
        """
        Build InvoiceAddRq QBXML request.

        Args:
            invoice_data: Dict with keys: customer_ref, txn_date, ref_number, memo, line_items
                         Optional: po_number, terms_ref, class_ref
                         line_items: list of {item_ref, desc, quantity, rate}
        """
        tree, qbxml, msgs_rq = QBXMLBuilder._create_base_qbxml()
        invoice_add_rq = etree.SubElement(msgs_rq, "InvoiceAddRq")
        invoice_add_rq.set("requestID", "1")
        invoice_add = etree.SubElement(invoice_add_rq, "InvoiceAdd")

        # IMPORTANT: Fields must be in this specific order per QBXML spec

        # 1. CustomerRef (required)
        customer_ref = etree.SubElement(invoice_add, "CustomerRef")
        list_id = etree.SubElement(customer_ref, "ListID")
        list_id.text = invoice_data['customer_ref']

        # 2. ClassRef (optional) - comes after CustomerRef
        if 'class_ref' in invoice_data:
            class_ref = etree.SubElement(invoice_add, "ClassRef")
            class_list_id = etree.SubElement(class_ref, "ListID")
            class_list_id.text = invoice_data['class_ref']

        # 3. TxnDate (optional)
        if 'txn_date' in invoice_data:
            txn_date = etree.SubElement(invoice_add, "TxnDate")
            txn_date.text = invoice_data['txn_date']

        # 4. RefNumber (optional)
        if 'ref_number' in invoice_data:
            ref_num = etree.SubElement(invoice_add, "RefNumber")
            ref_num.text = invoice_data['ref_number']

        # 5. IsPending (optional) - Set to false so invoice appears in main list
        is_pending = etree.SubElement(invoice_add, "IsPending")
        is_pending.text = "false"

        # 6. PONumber (optional) - comes AFTER IsPending
        if 'po_number' in invoice_data:
            po_number = etree.SubElement(invoice_add, "PONumber")
            po_number.text = invoice_data['po_number']

        # 7. TermsRef (optional) - comes AFTER PONumber
        if 'terms_ref' in invoice_data:
            terms_ref = etree.SubElement(invoice_add, "TermsRef")
            terms_list_id = etree.SubElement(terms_ref, "ListID")
            terms_list_id.text = invoice_data['terms_ref']

        # 8. Memo (optional) - MUST come BEFORE line items
        if 'memo' in invoice_data:
            memo = etree.SubElement(invoice_add, "Memo")
            memo.text = invoice_data['memo']

        # 9. InvoiceLineAdd items - come AFTER all header fields
        for item in invoice_data.get('line_items', []):
            line = etree.SubElement(invoice_add, "InvoiceLineAdd")

            if 'item_ref' in item:
                item_ref = etree.SubElement(line, "ItemRef")
                item_list_id = etree.SubElement(item_ref, "ListID")
                item_list_id.text = item['item_ref']

            if 'desc' in item:
                desc = etree.SubElement(line, "Desc")
                desc.text = item['desc']

            if 'quantity' in item:
                qty = etree.SubElement(line, "Quantity")
                qty.text = str(item['quantity'])

            if 'rate' in item:
                rate = etree.SubElement(line, "Rate")
                rate.text = str(item['rate'])

        # Serialize with processing instruction included
        from io import BytesIO
        output = BytesIO()
        tree.write(output, xml_declaration=False, encoding='UTF-8', pretty_print=True)
        return output.getvalue().decode('utf-8')

    @staticmethod
    def build_invoice_query(txn_id: Optional[str] = None, ref_number: Optional[str] = None,
                           modified_date_range_filter: Optional[Dict[str, str]] = None,
                           txn_date_range: Optional[Dict[str, str]] = None,
                           max_returned: Optional[int] = None) -> str:
        """
        Build InvoiceQueryRq QBXML request.

        Args:
            txn_id: Specific transaction ID to query
            ref_number: Reference number to query
            modified_date_range_filter: Dict with 'from_modified_date' and/or 'to_modified_date'
            txn_date_range: Dict with 'from_txn_date' and/or 'to_txn_date' (format: YYYY-MM-DD)
            max_returned: Maximum number of results to return
        """
        tree, qbxml, msgs_rq = QBXMLBuilder._create_base_qbxml()
        invoice_query_rq = etree.SubElement(msgs_rq, "InvoiceQueryRq")

        if txn_id:
            txn_id_elem = etree.SubElement(invoice_query_rq, "TxnID")
            txn_id_elem.text = txn_id

        if ref_number:
            ref_num_elem = etree.SubElement(invoice_query_rq, "RefNumber")
            ref_num_elem.text = ref_number

        if modified_date_range_filter:
            filter_elem = etree.SubElement(invoice_query_rq, "ModifiedDateRangeFilter")
            if 'from_modified_date' in modified_date_range_filter:
                from_date = etree.SubElement(filter_elem, "FromModifiedDate")
                from_date.text = modified_date_range_filter['from_modified_date']
            if 'to_modified_date' in modified_date_range_filter:
                to_date = etree.SubElement(filter_elem, "ToModifiedDate")
                to_date.text = modified_date_range_filter['to_modified_date']

        if txn_date_range:
            filter_elem = etree.SubElement(invoice_query_rq, "TxnDateRangeFilter")
            if 'from_txn_date' in txn_date_range:
                from_date = etree.SubElement(filter_elem, "FromTxnDate")
                from_date.text = txn_date_range['from_txn_date']
            if 'to_txn_date' in txn_date_range:
                to_date = etree.SubElement(filter_elem, "ToTxnDate")
                to_date.text = txn_date_range['to_txn_date']

        if max_returned:
            max_elem = etree.SubElement(invoice_query_rq, "MaxReturned")
            max_elem.text = str(max_returned)

        # Include full details
        include_line_items = etree.SubElement(invoice_query_rq, "IncludeLineItems")
        include_line_items.text = "true"

        # Serialize with processing instruction included
        from io import BytesIO
        output = BytesIO()
        tree.write(output, xml_declaration=False, encoding='UTF-8', pretty_print=True)
        return output.getvalue().decode('utf-8')

    @staticmethod
    def build_invoice_mod(invoice_mod_data: Dict[str, Any]) -> str:
        """
        Build InvoiceModRq QBXML request (for reopening/closing invoices).

        Args:
            invoice_mod_data: Dict with keys: txn_id, edit_sequence, is_pending (bool)
        """
        tree, qbxml, msgs_rq = QBXMLBuilder._create_base_qbxml()
        invoice_mod_rq = etree.SubElement(msgs_rq, "InvoiceModRq")
        invoice_mod = etree.SubElement(invoice_mod_rq, "InvoiceMod")

        # Required: TxnID and EditSequence
        txn_id = etree.SubElement(invoice_mod, "TxnID")
        txn_id.text = invoice_mod_data['txn_id']

        edit_seq = etree.SubElement(invoice_mod, "EditSequence")
        edit_seq.text = invoice_mod_data['edit_sequence']

        # IsPending to control open/closed state
        if 'is_pending' in invoice_mod_data:
            is_pending = etree.SubElement(invoice_mod, "IsPending")
            is_pending.text = "true" if invoice_mod_data['is_pending'] else "false"

        # Serialize with processing instruction included
        from io import BytesIO
        output = BytesIO()
        tree.write(output, xml_declaration=False, encoding='UTF-8', pretty_print=True)
        return output.getvalue().decode('utf-8')

    @staticmethod
    def build_sales_receipt_add(sales_receipt_data: Dict[str, Any]) -> str:
        """
        Build SalesReceiptAddRq QBXML request.

        Args:
            sales_receipt_data: Dict with keys: customer_ref, txn_date, ref_number, memo, line_items
                               line_items: list of {item_ref, desc, quantity, rate}

        Returns:
            QBXML formatted sales receipt add request
        """
        tree, qbxml, msgs_rq = QBXMLBuilder._create_base_qbxml()
        sales_receipt_add_rq = etree.SubElement(msgs_rq, "SalesReceiptAddRq")
        sales_receipt_add_rq.set("requestID", "1")
        sales_receipt_add = etree.SubElement(sales_receipt_add_rq, "SalesReceiptAdd")

        # IMPORTANT: Fields must be in this specific order per QBXML spec

        # 1. CustomerRef (required)
        customer_ref = etree.SubElement(sales_receipt_add, "CustomerRef")
        list_id = etree.SubElement(customer_ref, "ListID")
        list_id.text = sales_receipt_data['customer_ref']

        # 2. TxnDate (optional)
        if 'txn_date' in sales_receipt_data:
            txn_date = etree.SubElement(sales_receipt_add, "TxnDate")
            txn_date.text = sales_receipt_data['txn_date']

        # 3. RefNumber (optional)
        if 'ref_number' in sales_receipt_data:
            ref_num = etree.SubElement(sales_receipt_add, "RefNumber")
            ref_num.text = sales_receipt_data['ref_number']

        # 4. IsPending (optional) - Set to false so receipt appears in main list
        is_pending = etree.SubElement(sales_receipt_add, "IsPending")
        is_pending.text = "false"

        # 5. Memo (optional) - MUST come BEFORE line items
        if 'memo' in sales_receipt_data:
            memo = etree.SubElement(sales_receipt_add, "Memo")
            memo.text = sales_receipt_data['memo']

        # 6. SalesReceiptLineAdd items - come AFTER all header fields
        for item in sales_receipt_data.get('line_items', []):
            line = etree.SubElement(sales_receipt_add, "SalesReceiptLineAdd")

            if 'item_ref' in item:
                item_ref = etree.SubElement(line, "ItemRef")
                item_list_id = etree.SubElement(item_ref, "ListID")
                item_list_id.text = item['item_ref']

            if 'desc' in item:
                desc = etree.SubElement(line, "Desc")
                desc.text = item['desc']

            if 'quantity' in item:
                qty = etree.SubElement(line, "Quantity")
                qty.text = str(item['quantity'])

            if 'rate' in item:
                rate = etree.SubElement(line, "Rate")
                rate.text = str(item['rate'])

        # Serialize with processing instruction included
        from io import BytesIO
        output = BytesIO()
        tree.write(output, xml_declaration=False, encoding='UTF-8', pretty_print=True)
        return output.getvalue().decode('utf-8')

    @staticmethod
    def build_sales_receipt_query(txn_id: Optional[str] = None, ref_number: Optional[str] = None,
                                  modified_date_range_filter: Optional[Dict[str, str]] = None,
                                  txn_date_range: Optional[Dict[str, str]] = None,
                                  max_returned: Optional[int] = None) -> str:
        """
        Build SalesReceiptQueryRq QBXML request.

        Args:
            txn_id: Specific transaction ID to query
            ref_number: Reference number to query
            modified_date_range_filter: Dict with 'from_modified_date' and/or 'to_modified_date'
            txn_date_range: Dict with 'from_txn_date' and/or 'to_txn_date' (format: YYYY-MM-DD)
            max_returned: Maximum number of results to return

        Returns:
            QBXML formatted sales receipt query request
        """
        tree, qbxml, msgs_rq = QBXMLBuilder._create_base_qbxml()
        sales_receipt_query_rq = etree.SubElement(msgs_rq, "SalesReceiptQueryRq")

        if txn_id:
            txn_id_elem = etree.SubElement(sales_receipt_query_rq, "TxnID")
            txn_id_elem.text = txn_id

        if ref_number:
            ref_num_elem = etree.SubElement(sales_receipt_query_rq, "RefNumber")
            ref_num_elem.text = ref_number

        if modified_date_range_filter:
            filter_elem = etree.SubElement(sales_receipt_query_rq, "ModifiedDateRangeFilter")
            if 'from_modified_date' in modified_date_range_filter:
                from_date = etree.SubElement(filter_elem, "FromModifiedDate")
                from_date.text = modified_date_range_filter['from_modified_date']
            if 'to_modified_date' in modified_date_range_filter:
                to_date = etree.SubElement(filter_elem, "ToModifiedDate")
                to_date.text = modified_date_range_filter['to_modified_date']

        if txn_date_range:
            filter_elem = etree.SubElement(sales_receipt_query_rq, "TxnDateRangeFilter")
            if 'from_txn_date' in txn_date_range:
                from_date = etree.SubElement(filter_elem, "FromTxnDate")
                from_date.text = txn_date_range['from_txn_date']
            if 'to_txn_date' in txn_date_range:
                to_date = etree.SubElement(filter_elem, "ToTxnDate")
                to_date.text = txn_date_range['to_txn_date']

        if max_returned:
            max_elem = etree.SubElement(sales_receipt_query_rq, "MaxReturned")
            max_elem.text = str(max_returned)

        # Include full details
        include_line_items = etree.SubElement(sales_receipt_query_rq, "IncludeLineItems")
        include_line_items.text = "true"

        # Serialize with processing instruction included
        from io import BytesIO
        output = BytesIO()
        tree.write(output, xml_declaration=False, encoding='UTF-8', pretty_print=True)
        return output.getvalue().decode('utf-8')

    @staticmethod
    def build_charge_add(charge_data: Dict[str, Any]) -> str:
        """
        Build ChargeAddRq QBXML request (for statement charges).

        Args:
            charge_data: Dict with keys: customer_ref, txn_date, amount, quantity, item_ref (optional), memo

        Returns:
            QBXML formatted charge add request
        """
        tree, qbxml, msgs_rq = QBXMLBuilder._create_base_qbxml()
        charge_add_rq = etree.SubElement(msgs_rq, "ChargeAddRq")
        charge_add_rq.set("requestID", "1")
        charge_add = etree.SubElement(charge_add_rq, "ChargeAdd")

        # IMPORTANT: Fields must be in this specific order per QBXML spec

        # 1. CustomerRef (required)
        customer_ref = etree.SubElement(charge_add, "CustomerRef")
        list_id = etree.SubElement(customer_ref, "ListID")
        list_id.text = charge_data['customer_ref']

        # 2. TxnDate (optional)
        if 'txn_date' in charge_data:
            txn_date = etree.SubElement(charge_add, "TxnDate")
            txn_date.text = charge_data['txn_date']

        # 3. RefNumber (optional)
        if 'ref_number' in charge_data:
            ref_number = etree.SubElement(charge_add, "RefNumber")
            ref_number.text = charge_data['ref_number']

        # 4. ItemRef (optional but recommended)
        if 'item_ref' in charge_data:
            item_ref = etree.SubElement(charge_add, "ItemRef")
            item_list_id = etree.SubElement(item_ref, "ListID")
            item_list_id.text = charge_data['item_ref']

        # 5. Quantity (optional, defaults to 1)
        if 'quantity' in charge_data:
            quantity = etree.SubElement(charge_add, "Quantity")
            quantity.text = str(charge_data['quantity'])

        # 6. Rate (the charge amount per unit - since Quantity=1, this equals total charge)
        if 'amount' in charge_data:
            rate = etree.SubElement(charge_add, "Rate")
            rate.text = str(charge_data['amount'])

        # 7. Desc (description - NOTE: ChargeAdd uses Desc not Memo!)
        if 'memo' in charge_data:
            desc = etree.SubElement(charge_add, "Desc")
            desc.text = charge_data['memo']

        # Serialize with processing instruction included
        from io import BytesIO
        output = BytesIO()
        tree.write(output, xml_declaration=False, encoding='UTF-8', pretty_print=True)
        return output.getvalue().decode('utf-8')

    @staticmethod
    def build_charge_query(txn_id: Optional[str] = None, ref_number: Optional[str] = None,
                          modified_date_range_filter: Optional[Dict[str, str]] = None,
                          txn_date_range: Optional[Dict[str, str]] = None,
                          max_returned: Optional[int] = None) -> str:
        """
        Build ChargeQueryRq QBXML request (for statement charges).

        Args:
            txn_id: Specific transaction ID to query
            ref_number: Reference number to query
            modified_date_range_filter: Dict with 'from_modified_date' and/or 'to_modified_date'
            txn_date_range: Dict with 'from_txn_date' and/or 'to_txn_date' (format: YYYY-MM-DD)
            max_returned: Maximum number of results to return

        Returns:
            QBXML formatted charge query request
        """
        tree, qbxml, msgs_rq = QBXMLBuilder._create_base_qbxml()
        charge_query_rq = etree.SubElement(msgs_rq, "ChargeQueryRq")

        if txn_id:
            txn_id_elem = etree.SubElement(charge_query_rq, "TxnID")
            txn_id_elem.text = txn_id

        if ref_number:
            ref_num_elem = etree.SubElement(charge_query_rq, "RefNumber")
            ref_num_elem.text = ref_number

        if modified_date_range_filter:
            filter_elem = etree.SubElement(charge_query_rq, "ModifiedDateRangeFilter")
            if 'from_modified_date' in modified_date_range_filter:
                from_date = etree.SubElement(filter_elem, "FromModifiedDate")
                from_date.text = modified_date_range_filter['from_modified_date']
            if 'to_modified_date' in modified_date_range_filter:
                to_date = etree.SubElement(filter_elem, "ToModifiedDate")
                to_date.text = modified_date_range_filter['to_modified_date']

        if txn_date_range:
            filter_elem = etree.SubElement(charge_query_rq, "TxnDateRangeFilter")
            if 'from_txn_date' in txn_date_range:
                from_date = etree.SubElement(filter_elem, "FromTxnDate")
                from_date.text = txn_date_range['from_txn_date']
            if 'to_txn_date' in txn_date_range:
                to_date = etree.SubElement(filter_elem, "ToTxnDate")
                to_date.text = txn_date_range['to_txn_date']

        if max_returned:
            max_elem = etree.SubElement(charge_query_rq, "MaxReturned")
            max_elem.text = str(max_returned)

        # Serialize with processing instruction included
        from io import BytesIO
        output = BytesIO()
        tree.write(output, xml_declaration=False, encoding='UTF-8', pretty_print=True)
        return output.getvalue().decode('utf-8')

    @staticmethod
    def build_account_query(account_type: Optional[str] = None) -> str:
        """
        Build AccountQueryRq QBXML request.

        Args:
            account_type: Optional account type filter (e.g., 'Bank', 'AccountsReceivable')
        """
        tree, qbxml, msgs_rq = QBXMLBuilder._create_base_qbxml()
        account_query_rq = etree.SubElement(msgs_rq, "AccountQueryRq")

        if account_type:
            acct_type = etree.SubElement(account_query_rq, "AccountType")
            acct_type.text = account_type

        # Serialize with processing instruction included
        from io import BytesIO
        output = BytesIO()
        tree.write(output, xml_declaration=False, encoding='UTF-8', pretty_print=True)
        return output.getvalue().decode('utf-8')

    @staticmethod
    def build_customer_query() -> str:
        """
        Build CustomerQueryRq QBXML request.

        Returns:
            QBXML formatted customer query request
        """
        tree, qbxml, msgs_rq = QBXMLBuilder._create_base_qbxml()
        customer_query_rq = etree.SubElement(msgs_rq, "CustomerQueryRq")

        # Limit to active customers only
        active_status = etree.SubElement(customer_query_rq, "ActiveStatus")
        active_status.text = "ActiveOnly"

        # Serialize with processing instruction included
        from io import BytesIO
        output = BytesIO()
        tree.write(output, xml_declaration=False, encoding='UTF-8', pretty_print=True)
        return output.getvalue().decode('utf-8')

    @staticmethod
    def build_item_query(item_type: Optional[str] = None) -> str:
        """
        Build ItemQueryRq QBXML request.

        Args:
            item_type: Optional item type filter (e.g., 'Service', 'Inventory', 'NonInventory')

        Returns:
            QBXML formatted item query request
        """
        tree, qbxml, msgs_rq = QBXMLBuilder._create_base_qbxml()
        item_query_rq = etree.SubElement(msgs_rq, "ItemQueryRq")

        # Filter by item type if specified
        if item_type:
            type_filter = etree.SubElement(item_query_rq, "ItemTypeFilter")
            type_filter.text = item_type

        # Limit to active items only
        active_status = etree.SubElement(item_query_rq, "ActiveStatus")
        active_status.text = "ActiveOnly"

        # Serialize with processing instruction included
        from io import BytesIO
        output = BytesIO()
        tree.write(output, xml_declaration=False, encoding='UTF-8', pretty_print=True)
        return output.getvalue().decode('utf-8')

    @staticmethod
    def build_terms_query() -> str:
        """
        Build StandardTermsQueryRq QBXML request.

        Returns:
            QBXML formatted terms query request
        """
        tree, qbxml, msgs_rq = QBXMLBuilder._create_base_qbxml()
        terms_query_rq = etree.SubElement(msgs_rq, "StandardTermsQueryRq")

        # Limit to active terms only
        active_status = etree.SubElement(terms_query_rq, "ActiveStatus")
        active_status.text = "ActiveOnly"

        # Serialize with processing instruction included
        from io import BytesIO
        output = BytesIO()
        tree.write(output, xml_declaration=False, encoding='UTF-8', pretty_print=True)
        return output.getvalue().decode('utf-8')

    @staticmethod
    def build_class_query() -> str:
        """
        Build ClassQueryRq QBXML request.

        Returns:
            QBXML formatted class query request
        """
        tree, qbxml, msgs_rq = QBXMLBuilder._create_base_qbxml()
        class_query_rq = etree.SubElement(msgs_rq, "ClassQueryRq")

        # Limit to active classes only
        active_status = etree.SubElement(class_query_rq, "ActiveStatus")
        active_status.text = "ActiveOnly"

        # Serialize with processing instruction included
        from io import BytesIO
        output = BytesIO()
        tree.write(output, xml_declaration=False, encoding='UTF-8', pretty_print=True)
        return output.getvalue().decode('utf-8')
