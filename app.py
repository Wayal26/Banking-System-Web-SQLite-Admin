import hashlib
import secrets
import sqlite3
from datetime import datetime
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Banking System",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = Path(__file__).with_name("banking.db")

# ---------- Styling ----------
st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1200px;}
    [data-testid="stSidebar"] {border-right: 1px solid rgba(128,128,128,.18);}
    .brand {font-size: 1.55rem; font-weight: 800; margin-bottom: .15rem;}
    .muted {opacity: .68; font-size: .9rem;}
    .hero {
        padding: 1.6rem; border-radius: 20px;
        border: 1px solid rgba(128,128,128,.18);
        background: linear-gradient(135deg, rgba(30,100,255,.13), rgba(0,190,150,.10));
        margin-bottom: 1rem;
    }
    .hero h1 {margin: 0 0 .35rem 0; font-size: 2.25rem;}
    .card {
        padding: 1rem 1.1rem; border-radius: 16px;
        border: 1px solid rgba(128,128,128,.18);
        background: rgba(128,128,128,.035);
    }
    .amount {font-size: 2rem; font-weight: 800; margin-top: .25rem;}
    .small {font-size: .82rem; opacity: .68;}
    div.stButton > button, div[data-testid="stFormSubmitButton"] > button {border-radius: 10px; min-height: 2.7rem; font-weight: 650;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Database ----------
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                account_number TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                phone TEXT NOT NULL UNIQUE,
                pin_hash TEXT NOT NULL,
                balance REAL NOT NULL DEFAULT 0,
                approval_status TEXT NOT NULL DEFAULT 'Pending',
                rejection_reason TEXT DEFAULT '',
                approved_at TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        # Migrate older project databases created before approval workflow.
        account_columns = {row[1] for row in conn.execute("PRAGMA table_info(accounts)").fetchall()}
        if "approval_status" not in account_columns:
            conn.execute("ALTER TABLE accounts ADD COLUMN approval_status TEXT NOT NULL DEFAULT 'Approved'")
        if "rejection_reason" not in account_columns:
            conn.execute("ALTER TABLE accounts ADD COLUMN rejection_reason TEXT DEFAULT ''")
        if "approved_at" not in account_columns:
            conn.execute("ALTER TABLE accounts ADD COLUMN approved_at TEXT")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_number TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                amount REAL NOT NULL,
                details TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY(account_number) REFERENCES accounts(account_number) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS admins (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        if conn.execute("SELECT 1 FROM admins WHERE username=?", ("admin",)).fetchone() is None:
            conn.execute(
                "INSERT INTO admins (username, password_hash, created_at) VALUES (?, ?, ?)",
                ("admin", hash_password("Admin@123"), datetime.now().isoformat(timespec="seconds")),
            )


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def hash_pin(pin):
    return hashlib.sha256(pin.encode("utf-8")).hexdigest()


def generate_account_number(conn):
    while True:
        number = str(secrets.randbelow(90000000) + 10000000)
        if conn.execute("SELECT 1 FROM accounts WHERE account_number=?", (number,)).fetchone() is None:
            return number


def get_account(account_number):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM accounts WHERE account_number=?", (account_number,)).fetchone()


def add_transaction(conn, account_number, transaction_type, amount, details=""):
    conn.execute(
        "INSERT INTO transactions (account_number, transaction_type, amount, details, created_at) VALUES (?, ?, ?, ?, ?)",
        (account_number, transaction_type, amount, details, datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")),
    )


def create_account(name, phone, pin):
    name, phone, pin = name.strip(), phone.strip(), pin.strip()
    if not name:
        return False, "Full name is required.", None
    if not phone.isdigit() or len(phone) != 10:
        return False, "Enter a valid 10-digit phone number.", None
    if not pin.isdigit() or len(pin) != 4:
        return False, "PIN must contain exactly 4 digits.", None

    try:
        with get_conn() as conn:
            if conn.execute("SELECT 1 FROM accounts WHERE phone=?", (phone,)).fetchone():
                return False, "An account already exists with this phone number.", None
            account_number = generate_account_number(conn)
            conn.execute(
                "INSERT INTO accounts (account_number, full_name, phone, pin_hash, balance, approval_status, created_at) VALUES (?, ?, ?, ?, 0, 'Pending', ?)",
                (account_number, name, phone, hash_pin(pin), datetime.now().isoformat(timespec="seconds")),
            )
            return True, "Account created successfully!", account_number
    except sqlite3.Error:
        return False, "Could not create the account. Please try again.", None


def authenticate(account_number, pin):
    account = get_account(account_number.strip())
    return account if account and account["approval_status"] == "Approved" and account["pin_hash"] == hash_pin(pin.strip()) else None


def authenticate_admin(username, password):
    with get_conn() as conn:
        admin = conn.execute("SELECT * FROM admins WHERE username=?", (username.strip(),)).fetchone()
    return admin if admin and admin["password_hash"] == hash_password(password) else None


def money_input(label):
    return float(st.number_input(label, min_value=0.0, step=100.0, format="%.2f"))


init_db()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = None
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = None

# ---------- Public screens ----------
if st.session_state.logged_in is None and st.session_state.admin_logged_in is None:
    st.markdown(
        '<div class="hero"><div class="small">PYTHON • STREAMLIT • SQLITE</div><h1>🏦 Banking System</h1><div class="muted">A modern banking management mini project with customer and admin portals.</div></div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1.15, 1], gap="large")
    with col1:
        st.subheader("Welcome")
        st.write("Create an account, sign in as a customer, or use the administrator portal.")
        a, b, c = st.columns(3)
        a.metric("Storage", "SQLite")
        b.metric("Frontend", "Streamlit")
        c.metric("Language", "Python")
        st.info("Customer accounts and transaction records are stored permanently in the SQLite database.")

    with col2:
        create_tab, login_tab, status_tab, admin_tab = st.tabs(["Create Account", "Customer Login", "Application Status", "🔐 Admin Login"])
        with create_tab:
            with st.form("create_account_form", clear_on_submit=False):
                name = st.text_input("Full Name")
                phone = st.text_input("10-digit Phone Number", max_chars=10)
                pin = st.text_input("Create 4-digit PIN", type="password", max_chars=4)
                submitted = st.form_submit_button("Create Account", use_container_width=True)
            if submitted:
                ok, message, account_number = create_account(name, phone, pin)
                if ok:
                    st.success(message)
                    st.success(f"Your Account Number: {account_number}")
                    st.warning("Your account is pending admin approval. You can log in after the administrator approves your application.")
                    st.caption("Save your account number and use Application Status to check approval.")
                else:
                    st.error(message)

        with login_tab:
            with st.form("login_form"):
                account_number = st.text_input("Account Number", max_chars=8)
                login_pin = st.text_input("4-digit PIN", type="password", max_chars=4)
                submitted = st.form_submit_button("Login", use_container_width=True)
            if submitted:
                account = authenticate(account_number, login_pin)
                if account:
                    st.session_state.logged_in = account["account_number"]
                    st.rerun()
                else:
                    st.error("Invalid account number or PIN.")

        with status_tab:
            st.caption("Check whether your account application has been approved by the administrator.")
            with st.form("status_form"):
                status_account = st.text_input("Account Number", max_chars=8)
                status_phone = st.text_input("Registered Phone Number", max_chars=10)
                status_submit = st.form_submit_button("Check Approval Status", use_container_width=True)
            if status_submit:
                with get_conn() as conn:
                    status_row = conn.execute(
                        "SELECT account_number, full_name, approval_status, rejection_reason, created_at FROM accounts WHERE account_number=? AND phone=?",
                        (status_account.strip(), status_phone.strip()),
                    ).fetchone()
                if not status_row:
                    st.error("Account details not found. Check your account number and phone number.")
                elif status_row["approval_status"] == "Approved":
                    st.success("✅ Your account has been approved. You can now log in.")
                elif status_row["approval_status"] == "Rejected":
                    st.error("❌ Your account application was rejected.")
                    if status_row["rejection_reason"]:
                        st.info(f"Reason: {status_row['rejection_reason']}")
                else:
                    st.warning("⏳ Your account is still pending admin approval.")

        with admin_tab:
            st.caption("Administrator access for project management and monitoring.")
            with st.form("admin_login_form"):
                admin_username = st.text_input("Admin Username")
                admin_password = st.text_input("Admin Password", type="password")
                submitted = st.form_submit_button("Open Admin Panel", use_container_width=True)
            if submitted:
                admin = authenticate_admin(admin_username, admin_password)
                if admin:
                    st.session_state.admin_logged_in = admin["username"]
                    st.rerun()
                else:
                    st.error("Invalid admin username or password.")
            st.caption("Demo credentials: admin / Admin@123")

    st.divider()
    st.caption("College mini project • Banking System Web Version")

# ---------- Admin panel ----------
elif st.session_state.admin_logged_in is not None:
    with st.sidebar:
        st.markdown('<div class="brand">🛡️ Admin Panel</div><div class="muted">Banking System Management</div>', unsafe_allow_html=True)
        st.divider()
        st.write(f"**Administrator:** {st.session_state.admin_logged_in}")
        admin_menu = st.radio("Navigation", ["Dashboard", "Approval Requests", "Customer Accounts", "All Transactions"], label_visibility="collapsed")
        st.divider()
        if st.button("Logout Admin", use_container_width=True):
            st.session_state.admin_logged_in = None
            st.rerun()

    st.markdown("## 🛡️ Administrator Dashboard")
    st.caption("Monitor customer accounts, balances and transaction activity.")

    with get_conn() as conn:
        total_customers = conn.execute("SELECT COUNT(*) AS c FROM accounts").fetchone()["c"]
        total_balance = conn.execute("SELECT COALESCE(SUM(balance), 0) AS total FROM accounts").fetchone()["total"]
        total_transactions = conn.execute("SELECT COUNT(*) AS c FROM transactions").fetchone()["c"]
        total_deposits = conn.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM transactions WHERE transaction_type='Deposit'").fetchone()["total"]
        pending_approvals = conn.execute("SELECT COUNT(*) AS c FROM accounts WHERE approval_status='Pending'").fetchone()["c"]

    if admin_menu == "Dashboard":
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Customers", total_customers)
        c2.metric("Total Balance", f"₹{total_balance:,.2f}")
        c3.metric("Transactions", total_transactions)
        c4.metric("Deposits", f"₹{total_deposits:,.2f}")
        c5.metric("Pending Approvals", pending_approvals)
        st.subheader("System Overview")
        st.info("The admin panel provides a project-level view of registered customers and banking transactions. PIN values are never displayed.")

    elif admin_menu == "Approval Requests":
        st.subheader("✅ Admin Approval Requests")
        st.caption("Review newly created customer accounts before allowing customer login.")
        with get_conn() as conn:
            pending = conn.execute(
                "SELECT account_number, full_name, phone, created_at FROM accounts WHERE approval_status='Pending' ORDER BY created_at DESC"
            ).fetchall()
        if not pending:
            st.success("No pending account approval requests.")
        else:
            for request in pending:
                with st.container(border=True):
                    left, right = st.columns([2, 1])
                    with left:
                        st.write(f"**{request['full_name']}**")
                        st.caption(f"A/C: {request['account_number']} • Phone: {request['phone']} • Applied: {request['created_at']}")
                    with right:
                        approve_col, reject_col = st.columns(2)
                        if approve_col.button("Approve", key=f"approve_{request['account_number']}", use_container_width=True):
                            with get_conn() as conn:
                                conn.execute(
                                    "UPDATE accounts SET approval_status='Approved', approved_at=?, rejection_reason='' WHERE account_number=?",
                                    (datetime.now().isoformat(timespec="seconds"), request["account_number"]),
                                )
                            st.success("Account approved.")
                            st.rerun()
                        if reject_col.button("Reject", key=f"reject_{request['account_number']}", use_container_width=True):
                            st.session_state[f"reject_mode_{request['account_number']}"] = True
                            st.rerun()
                    if st.session_state.get(f"reject_mode_{request['account_number']}"):
                        reason = st.text_input("Rejection reason", key=f"reason_{request['account_number']}")
                        if st.button("Confirm Rejection", key=f"confirm_reject_{request['account_number']}"):
                            with get_conn() as conn:
                                conn.execute(
                                    "UPDATE accounts SET approval_status='Rejected', rejection_reason=? WHERE account_number=?",
                                    (reason.strip() or "Application rejected by administrator.", request["account_number"]),
                                )
                            st.success("Application rejected.")
                            st.rerun()

    elif admin_menu == "Customer Accounts":
        st.subheader("👥 Customer Accounts")
        with get_conn() as conn:
            customers = conn.execute("SELECT account_number, full_name, phone, balance, created_at FROM accounts ORDER BY created_at DESC").fetchall()
        if not customers:
            st.info("No customer accounts found.")
        else:
            import pandas as pd
            df = pd.DataFrame([dict(row) for row in customers])
            df.columns = ["Account Number", "Full Name", "Phone", "Balance (₹)", "Created At"]
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button("⬇️ Download Customer List (CSV)", df.to_csv(index=False).encode("utf-8"), "customer_accounts.csv", "text/csv", use_container_width=True)

    elif admin_menu == "All Transactions":
        st.subheader("📋 All Transactions")
        with get_conn() as conn:
            transactions = conn.execute("""
                SELECT t.id, t.account_number, a.full_name, t.transaction_type, t.amount, t.details, t.created_at
                FROM transactions t JOIN accounts a ON a.account_number=t.account_number
                ORDER BY t.id DESC
            """).fetchall()
        if not transactions:
            st.info("No transactions found.")
        else:
            import pandas as pd
            df = pd.DataFrame([dict(row) for row in transactions])
            df.columns = ["ID", "Account Number", "Customer", "Type", "Amount (₹)", "Details", "Date & Time"]
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button("⬇️ Download Transactions (CSV)", df.to_csv(index=False).encode("utf-8"), "all_transactions.csv", "text/csv", use_container_width=True)

# ---------- Logged-in customer dashboard ----------
elif st.session_state.logged_in is not None:
    account_number = st.session_state.logged_in
    account = get_account(account_number)
    if account is None:
        st.session_state.logged_in = None
        st.rerun()

    with st.sidebar:
        st.markdown('<div class="brand">🏦 Banking System</div><div class="muted">Customer Dashboard</div>', unsafe_allow_html=True)
        st.divider()
        st.write(f"**{account['full_name']}**")
        st.caption(f"A/C: {account['account_number']}")
        menu = st.radio(
            "Navigation",
            ["Dashboard", "Deposit", "Withdraw", "Transfer", "Transaction History", "Admin Approval", "Change PIN"],
            label_visibility="collapsed",
        )
        st.divider()
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = None
            st.rerun()

    st.markdown(f"## Good day, {account['full_name'].split()[0]} 👋")
    st.caption(f"Account number: {account['account_number']}")

    if menu == "Dashboard":
        st.markdown('<div class="hero"><div class="small">AVAILABLE BALANCE</div><div class="amount">₹{:,.2f}</div><div class="muted">Your current account balance</div></div>'.format(account["balance"]), unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Account Balance", f"₹{account['balance']:,.2f}")
        with c2:
            with get_conn() as conn:
                count = conn.execute("SELECT COUNT(*) AS c FROM transactions WHERE account_number=?", (account_number,)).fetchone()["c"]
            st.metric("Transactions", count)
        with c3:
            st.metric("Account", "Active")

        st.subheader("Quick Actions")
        q1, q2, q3 = st.columns(3)
        if q1.button("➕ Deposit", use_container_width=True):
            st.session_state.quick_menu = "Deposit"
            st.rerun()
        if q2.button("➖ Withdraw", use_container_width=True):
            st.session_state.quick_menu = "Withdraw"
            st.rerun()
        if q3.button("🔄 Transfer", use_container_width=True):
            st.session_state.quick_menu = "Transfer"
            st.rerun()

        with get_conn() as conn:
            recent = conn.execute(
                "SELECT transaction_type, amount, details, created_at FROM transactions WHERE account_number=? ORDER BY id DESC LIMIT 5",
                (account_number,),
            ).fetchall()
        st.subheader("Recent Transactions")
        if not recent:
            st.info("No transactions yet. Use Quick Actions to get started.")
        else:
            for tx in recent:
                sign = "+" if tx["transaction_type"] in ("Deposit", "Transfer Received") else "-"
                st.markdown(
                    f"**{tx['transaction_type']}**  ·  {sign}₹{tx['amount']:,.2f}  \n<small>{tx['created_at']} • {tx['details']}</small>",
                    unsafe_allow_html=True,
                )
                st.divider()

    elif menu == "Deposit":
        st.subheader("➕ Deposit Money")
        with st.form("deposit_form"):
            amount = money_input("Amount to deposit (₹)")
            submitted = st.form_submit_button("Deposit Money", use_container_width=True)
        if submitted:
            if amount <= 0:
                st.error("Amount must be greater than zero.")
            else:
                with get_conn() as conn:
                    conn.execute("UPDATE accounts SET balance = balance + ? WHERE account_number=?", (amount, account_number))
                    add_transaction(conn, account_number, "Deposit", amount, "Cash deposited")
                st.success(f"₹{amount:,.2f} deposited successfully.")
                st.rerun()

    elif menu == "Withdraw":
        st.subheader("➖ Withdraw Money")
        st.caption(f"Available balance: ₹{account['balance']:,.2f}")
        with st.form("withdraw_form"):
            amount = money_input("Amount to withdraw (₹)")
            submitted = st.form_submit_button("Withdraw Money", use_container_width=True)
        if submitted:
            if amount <= 0:
                st.error("Amount must be greater than zero.")
            elif amount > account["balance"]:
                st.error("Insufficient balance.")
            else:
                with get_conn() as conn:
                    conn.execute("UPDATE accounts SET balance = balance - ? WHERE account_number=?", (amount, account_number))
                    add_transaction(conn, account_number, "Withdrawal", amount, "Cash withdrawn")
                st.success(f"₹{amount:,.2f} withdrawn successfully.")
                st.rerun()

    elif menu == "Transfer":
        st.subheader("🔄 Transfer Money")
        with st.form("transfer_form"):
            receiver = st.text_input("Receiver Account Number", max_chars=8)
            amount = money_input("Amount to transfer (₹)")
            submitted = st.form_submit_button("Transfer Money", use_container_width=True)
        if submitted:
            receiver = receiver.strip()
            if amount <= 0:
                st.error("Amount must be greater than zero.")
            elif receiver == account_number:
                st.error("You cannot transfer money to your own account.")
            elif amount > account["balance"]:
                st.error("Insufficient balance.")
            else:
                with get_conn() as conn:
                    target = conn.execute("SELECT account_number FROM accounts WHERE account_number=?", (receiver,)).fetchone()
                    if target is None:
                        st.error("Receiver account not found.")
                    else:
                        conn.execute("UPDATE accounts SET balance = balance - ? WHERE account_number=?", (amount, account_number))
                        conn.execute("UPDATE accounts SET balance = balance + ? WHERE account_number=?", (amount, receiver))
                        add_transaction(conn, account_number, "Transfer", amount, f"Transferred to Account {receiver}")
                        add_transaction(conn, receiver, "Transfer Received", amount, f"Received from Account {account_number}")
                        st.success(f"₹{amount:,.2f} transferred successfully.")
                        st.rerun()

    elif menu == "Transaction History":
        st.subheader("📋 Transaction History")
        with get_conn() as conn:
            transactions = conn.execute(
                "SELECT transaction_type, amount, details, created_at FROM transactions WHERE account_number=? ORDER BY id DESC",
                (account_number,),
            ).fetchall()
        if not transactions:
            st.info("No transactions found.")
        else:
            for i, tx in enumerate(transactions, start=1):
                sign = "+" if tx["transaction_type"] in ("Deposit", "Transfer Received") else "-"
                with st.container(border=True):
                    c1, c2 = st.columns([2, 1])
                    c1.write(f"**{i}. {tx['transaction_type']}**")
                    c1.caption(f"{tx['created_at']} • {tx['details']}")
                    c2.markdown(f"### {sign}₹{tx['amount']:,.2f}")

    elif menu == "Admin Approval":
        st.subheader("🛡️ Admin Approval")
        status = account["approval_status"]
        if status == "Approved":
            st.success("✅ Account Approved")
            if account["approved_at"]:
                st.caption(f"Approved on: {account['approved_at']}")
            st.write("Your account has been approved by the administrator and is active.")
        elif status == "Pending":
            st.warning("⏳ Approval Pending")
            st.write("Your account is waiting for administrator approval.")
        else:
            st.error("❌ Account Rejected")
            st.write(account["rejection_reason"] or "Please contact the administrator for more information.")

    elif menu == "Change PIN":
        st.subheader("🔐 Change PIN")
        with st.form("change_pin_form"):
            old_pin = st.text_input("Current PIN", type="password", max_chars=4)
            new_pin = st.text_input("New 4-digit PIN", type="password", max_chars=4)
            confirm_pin = st.text_input("Confirm New PIN", type="password", max_chars=4)
            submitted = st.form_submit_button("Change PIN", use_container_width=True)
        if submitted:
            if hash_pin(old_pin) != account["pin_hash"]:
                st.error("Incorrect current PIN.")
            elif not new_pin.isdigit() or len(new_pin) != 4:
                st.error("New PIN must contain exactly 4 digits.")
            elif new_pin != confirm_pin:
                st.error("New PIN and confirmation do not match.")
            else:
                with get_conn() as conn:
                    conn.execute("UPDATE accounts SET pin_hash=? WHERE account_number=?", (hash_pin(new_pin), account_number))
                st.success("PIN changed successfully.")
