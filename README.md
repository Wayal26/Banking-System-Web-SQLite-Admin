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
