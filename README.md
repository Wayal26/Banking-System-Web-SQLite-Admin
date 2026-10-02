# 🏦 Banking System – Web Version

A college mini-project built with **Python, Streamlit and SQLite**.

## Features

### Customer
- Create account
- Account approval status
- Customer login
- Dashboard with balance and account information
- Deposit request with admin approval
- Withdraw
- Transfer between approved accounts
- Transaction history
- Deposit request status: Pending / Approved / Rejected

### Admin
The admin sidebar contains only:
1. 📊 Dashboard
2. 🛡️ Approval Requests
3. 💰 Deposit Requests
4. ❌ Rejected Requests
5. 👥 Customer Accounts

Admin can:
- Approve/reject new customer accounts
- Approve/reject deposit requests
- Review rejected requests
- View each customer's account and transactions

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Demo admin login

Username: `admin`  
Password: `admin123`

Change these credentials before using the project for anything beyond a classroom demo.

## Deployment

Upload `app.py`, `requirements.txt` and `README.md` to GitHub, then deploy the repository using Streamlit Community Cloud.

> Educational/demo project only. Do not store real banking credentials or financial information.
