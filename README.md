# 🏦 Banking System – Web Version

A college mini project that demonstrates common banking operations using **Python, Streamlit and SQLite**.

## Technology Stack

- **Python** – application logic
- **Streamlit** – interactive web interface
- **SQLite** – persistent database storage

## Features

- Create a bank account
- Login with account number and PIN
- Dashboard with balance and recent transactions
- Deposit money
- Withdraw money
- Transfer money between accounts
- View complete transaction history
- Change PIN
- Logout
- Admin login portal
- Admin dashboard with customer statistics
- Admin approval workflow for new customer accounts
- Customer application status and approval status page
- View all customer accounts
- View all transactions
- Export customer and transaction data as CSV

## Database

The application automatically creates `banking.db` on first run. It contains three tables:

- `accounts` – account number, name, phone, PIN hash, balance and creation time
- `transactions` – transaction type, amount, details, account number and timestamp
- `admins` – administrator username, password hash and creation time

SQLite is used so the project does not require a separate database server.

> **Project note:** This is an educational mini project, not a production banking system. It should not be used for real financial data.

## Admin Panel

The project includes a separate administrator portal. For the college/demo version, the default credentials are:

- **Username:** `admin`
- **Password:** `Admin@123`

The admin panel can view customer accounts, total balances, transaction counts, all transactions, and export tables as CSV. Customer PINs are not displayed.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deployment

The project can be deployed through Streamlit Community Cloud from a GitHub repository.

> **Cloud note:** SQLite is suitable for a college/demo project and local deployment. On some cloud hosting environments, local files can be reset when the application is rebuilt or restarted. A production application would use a managed persistent database.


## Admin Approval Workflow

1. A new customer creates an account.
2. The account is saved with **Pending** approval status.
3. The customer can use **Application Status** to check the request.
4. The administrator opens **Approval Requests** and can **Approve** or **Reject** the application.
5. Only approved customers can log in to the banking dashboard.
6. Rejected applications can include a rejection reason.

This approval workflow is intended for a college/demo project and is not a production banking approval system.


## Deposit Approval
Customer deposit requests are stored as pending requests. The administrator can approve or reject each request. The customer balance and transaction history are updated only after an administrator approves the deposit.
