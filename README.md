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
python src/app.py
```

QuickBooks needs to be running first, or you'll get COM errors.


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