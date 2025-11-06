# QBD Test Tool

A testing utility for QuickBooks Desktop integrations. This is an internal tool, not meant for end users.

## What This Does

When you're building software that integrates with QuickBooks Desktop, you need a way to:
- Quickly create test data (customers, invoices, sales receipts)
- Verify that payment records and deposit accounts are correctly updated
- Test state changes without manually clicking through QuickBooks

That's what this tool does. It talks directly to QuickBooks via QBXML/COM and lets you automate the testing workflow.

## Getting Started

### Option 1: Run the Executable (Easiest)

**Requirements:**
- Windows (any version that runs QuickBooks)
- QuickBooks Desktop must be running with a company file open
- On first launch, QuickBooks will prompt you to authorize access - click "Yes, always"


### Option 2: Run from Source

If you're modifying the tool:

**Requirements:**
- Python 3.11 or higher
- Windows (required for COM access to QuickBooks)

**Install dependencies:**
```bash
pip install pywin32 lxml faker pillow pystray
```

**Run:**
```bash
# Windows (recommended)
run.bat

# Or directly with Python
python src/app.py
```

QuickBooks needs to be running first, or you'll get COM errors.

The `run.bat` script will check for Python and dependencies before launching.


### Initial Setup

When you first open the app, go to the **Setup** tab (under Create Data) and click **Load All**. This pulls in your existing customers, items, accounts, etc. from QuickBooks so you have something to work with.

If you don't have any test data yet, you can create customers from scratch, but it's faster to load what's already there.

### Creating Test Invoices

1. **Create Data tab** → **Invoice subtab**
2. Select a customer (or create one first in the Customer subtab)
3. Configure how many invoices you want and the line item totals
4. Click **Create Invoice**

The tool generates invoices with randomized line items using your actual QuickBooks items. Each invoice gets a unique ref number so you can track it later.

### Monitoring Changes

Once you have some test invoices, you can monitor them to see when your integration changes their state:

1. **Monitor Transactions tab**
2. Set a check interval (how often to poll QuickBooks, in seconds)
3. Click **Start Monitoring**

The tool will periodically query QuickBooks for your invoices and detect when they change from Open to Closed (or vice versa). 

### Verification

When an invoice closes, the tool automatically checks if:
- A payment record exists
- The deposit account is set correctly
- The payment amount <= the sale.

Results show up in the **Verification Results tab**. Red = something's wrong, Green = looks good.


### "QuickBooks is not running" error

QuickBooks needs to be running **and** have a company file open before you start the tool. If you launch the tool first, it won't work.

Fix: Start QuickBooks, open a company file, then run the tool.

### "Access denied" or "Application not authorized"

First time you run this, QuickBooks will ask if you want to allow access. You need to click "Yes, always allow" or it won't work.

If you accidentally clicked "No", you'll need to go into QuickBooks' integrated applications preferences and authorize it manually.


### Project Structure

```
src/
├── app.py                    - Main GUI application
├── ui/
│   ├── create_tab.py         - Create data interface
│   ├── monitor_tab.py        - Monitoring interface
│   └── verify_tab.py         - Verification results
├── store.py                  - State management 
├── qb_connection.py          - QuickBooks COM wrapper
├── qb_connection_manager.py  - Separate manager process
├── qb_ipc_client.py          - IPC client for manager
├── qb_operations.py          - Query operations
├── qbxml_builder.py          - Build QBXML requests
├── qbxml_parser.py           - Parse QBXML responses
├── test_data.py              - Generate random test data (Faker)
└── tray_icon.py              - System tray integration
```

### Dependencies

**Core:**
- `pywin32` - COM access to QuickBooks
- `lxml` - XML parsing for QBXML
- `tkinter` - GUI (ships with Python)

**Extras:**
- `faker` - Generate random customer names/addresses
- `pillow` - Tray icon graphics
- `pystray` - System tray integration

## Building the Executable

If you need to build a new exe:

```bash
pip install pyinstaller
pyinstaller --clean QBDTestTool.spec
```

The spec file is already configured. Output goes to `dist/QBDTestTool.exe`.


### Use:

<img width="902" height="732" alt="image" src="https://github.com/user-attachments/assets/05b437b4-4fbe-402c-ae97-abfc22a982ae" />

##### Initialize

1. Load Customers, Inventory Items, Terms, Classes, and Accounts.
2. Create or Use an Existing Customer
   Create:
   - Select the Customer sub-tab under the Create Data tab.
   - Enter an email address (Can be nonsense)
   - Choose to random data or uncheck the box to manually submit information with the creation.
   - Jobs, Sub-Jobs - This will create n number of jobs and n number of sub-jobs (Customer:Job:Sub-Job)
   - Scroll the window, if needed
   - Create New Customer
  Use:
   - Drop-down Boxes in Invoice, Sales Receipt, and Statement Charge windows.

<img width="902" height="1392" alt="image" src="https://github.com/user-attachments/assets/5a158ab9-2c3e-4439-bbab-771d5950de5c" />


##### Generate
Under Invoice, Sales Receipt, and Statement Charge sub-tabs:
1. Select a Customer. If you generate a new customer, the Customer will automatically be selected.
2. Select the number of invoices you wish to generate.
3. Set the number of line-items, the Invoice amount range, date range, and select terms and a class.
4. Create <Item> Batch

<img width="902" height="657" alt="image" src="https://github.com/user-attachments/assets/cd9c2ed0-83db-47da-bd17-d3ec2bd68088" />
<img width="902" height="854" alt="image" src="https://github.com/user-attachments/assets/cd9571ed-5277-4f69-b134-b70496f73087" />
<img width="902" height="854" alt="image" src="https://github.com/user-attachments/assets/7f187829-ff93-4d81-9119-b8341833c802" />


##### Monitor

1. After generating sales with the testing tool, open the Monitor Transactions Tab.
2. Set the expected Posting Account (Deposit Account)
3. Set the refresh interval. This sets how often the program checks for paid invoices.
4. Pay an invoice in QB or with Payment Terminal.
5. The interface should update to show the invoices close.

<img width="902" height="854" alt="image" src="https://github.com/user-attachments/assets/1a3a7fd0-23ab-4d3b-bf9d-a92b0c506911" />

##### Verification Results

Automatically checks Monitored Transactions for changes. When the change is detected, it will check the deposit account, the memo fields, and the ammount to ensure post-back is mapping properly.
  
