# QBD Test Tool

A testing utility for QuickBooks Desktop integrations. This is an internal tool, not meant for end users.

## What This Does

When you're building software that integrates with QuickBooks Desktop, you need a way to:
- Quickly create test data (customers, invoices, sales receipts, statement charges)
- Monitor transaction state changes in real-time
- Verify that payment records and deposit accounts are correctly updated
- Test payment posting workflows without manually clicking through QuickBooks
- Archive and clean up test data when done

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

### Creating Test Transactions

The tool supports three transaction types: **Invoices**, **Sales Receipts**, and **Statement Charges**.

1. **Create Data tab** → Select transaction type subtab (Invoice, Sales Receipt, or Statement Charge)
2. Select a customer (or create one first in the Customer subtab)
3. Configure:
   - Number of transactions to create
   - Line items (for invoices/sales receipts)
   - Amount range
   - Date range
   - Terms and class (for invoices)
4. Click **Create Batch**

The tool generates transactions with randomized data using your actual QuickBooks items, terms, and classes. Each transaction gets a unique ref number for tracking.

**Statement Charges** are simpler - they create a single charge on the customer's statement without line items.

### Monitoring Changes

Once you have created transactions, you can monitor them to see when your integration changes their state:

1. **Monitor Transactions tab**
2. Set a check interval (how often to poll QuickBooks, in seconds)
3. Click **Start Monitoring**

The tool will periodically query QuickBooks for all your transactions (invoices, sales receipts, statement charges) and detect when they change from Open to Closed (or vice versa). All transaction types appear in the same monitoring table. 

### Verification

When a transaction status changes (e.g., invoice closes after payment), the tool automatically verifies:
- Payment records exist and amounts are correct
- Deposit account matches expected account
- Payment amount is appropriate (full payment, partial payment, or overpayment)
- Transaction and payment memos are updated correctly

Results show up in the **Verification Results tab**:
- **PASS** (green): Everything looks correct
- **WARN** (yellow): Minor issues or incomplete data
- **FAIL** (red): Critical problems detected

The verification system works for invoices, sales receipts, and statement charges.

### Session Persistence

Sessions are automatically saved after creating transactions, allowing you to:
- Close the app and resume monitoring later
- Load previous sessions with **File → Load Session**
- Manually save with **File → Save Session**

Session files are stored in `sessions/` directory as JSON and include all created transactions and their current state.

### Logging Levels

Each tab has a log level selector:
- **Normal**: Standard operation messages
- **Verbose**: Detailed progress for each transaction
- **Debug**: Raw QBXML requests/responses (for troubleshooting)

Logs display the last 250 messages with automatic scrolling.

### Cleanup & Archive

The **Cleanup** tab (under Monitor Transactions) lets you:
- **Archive Closed**: Mark paid transactions as archived
- **Archive All**: Archive everything (including open transactions)
- **Delete from QB**: Permanently remove archived transactions from QuickBooks
- **Remove from Session**: Clear archived transactions from local session only

Useful for cleaning up after extensive testing.

## Troubleshooting

### "QuickBooks is not running" error

QuickBooks needs to be running **and** have a company file open before you start the tool. If you launch the tool first, it won't work.

Fix: Start QuickBooks, open a company file, then run the tool.

### "Access denied" or "Application not authorized"

First time you run this, QuickBooks will ask if you want to allow access. You need to click "Yes, always allow" or it won't work.

If you accidentally clicked "No", you'll need to go into QuickBooks' integrated applications preferences and authorize it manually.


### Project Structure

The codebase is organized into focused packages following separation of concerns:

```
src/
├── app.py                      - Main GUI orchestrator (214 lines, down from 3,700+)
├── actions/                    - Redux-style action creators
│   ├── customer_actions.py    - Customer CRUD operations
│   ├── invoice_actions.py     - Invoice creation actions
│   ├── sales_receipt_actions.py - Sales receipt actions
│   ├── charge_actions.py      - Statement charge actions
│   ├── monitor_actions.py     - Transaction monitoring actions
│   └── monitor_search_actions.py - Advanced invoice search
├── workers/                    - Background threading workers
│   ├── customer_worker.py     - Customer/job batch creation
│   ├── invoice_worker.py      - Invoice batch creation
│   ├── sales_receipt_worker.py - Sales receipt batch creation
│   ├── charge_worker.py       - Statement charge batch creation
│   ├── monitor_worker.py      - Transaction state monitoring
│   ├── cleanup_worker.py      - Archive/delete operations
│   └── data_loader_worker.py  - QB data loading
├── ui/                         - UI component setup
│   ├── create_tab_setup.py    - Create Data tab with subtabs
│   ├── monitor_tab_setup.py   - Monitor tab interface
│   ├── verify_tab_setup.py    - Verification results display
│   ├── setup_subtab_setup.py  - Data loading subtab
│   ├── customer_subtab_setup.py - Customer creation form
│   ├── invoice_subtab_setup.py - Invoice creation form
│   ├── sales_receipt_subtab_setup.py - Sales receipt form
│   ├── charge_subtab_setup.py - Statement charge form
│   ├── logging_utils.py       - Logging helpers
│   └── ui_utils.py            - UI utilities
├── store/                      - Redux-like state management
│   ├── store.py               - Store class (subscribe/dispatch)
│   ├── state.py               - AppState dataclass definitions
│   ├── actions.py             - Action type constants
│   └── reducers.py            - Pure reducer functions
├── qb/                         - QuickBooks integration
│   ├── connection.py          - COM wrapper for QB
│   ├── connection_manager.py  - Separate process manager
│   ├── ipc_client.py          - IPC client for manager
│   ├── data_loader.py         - Load customers/items/accounts
│   ├── xml_builder.py         - Build QBXML requests
│   └── xml_parser.py          - Parse QBXML responses
├── mock_generation/            - Test data generators
│   ├── customer_generator.py  - Random customer data (Faker)
│   ├── invoice_generator.py   - Invoice with line items
│   ├── sales_receipt_generator.py - Sales receipt data
│   └── charge_generator.py    - Statement charge data
├── trayapp/                    - System tray integration
│   ├── tray_icon.py           - Tray icon implementation
│   └── daemon_actions.py      - Daemon mode actions
├── persistence/                - Session save/load
│   ├── session_manager.py     - JSON session persistence
│   └── change_detector.py     - Detect external QB changes
└── app_logging.py             - Logging granularity control
```

**Key Architecture Benefits:**
- **Maintainability**: Easy to locate and modify specific functionality
- **Separation of Concerns**: Clear boundaries between UI, business logic, and state
- **Testability**: Isolated modules for unit testing
- **Scalability**: Simple to add new transaction types or features

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

The spec file is already configured. Output goes to `dist/QBDTestTool.exe` (26 MB single-file executable).

**Build Options:**
- **GUI-only (default)**: `console=False` in spec file - no console window appears
- **With console (debugging)**: Change to `console=True` - shows console for error messages

After building, the executable runs standalone on any Windows 10/11 machine without Python installed.


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
  
