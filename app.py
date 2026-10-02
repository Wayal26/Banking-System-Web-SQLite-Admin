
import streamlit as st
import sqlite3
import hashlib
from datetime import datetime

st.set_page_config(
    page_title="Banking System",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB = "banking.db"

def hash_pin(pin):
    return hashlib.sha256(pin.encode()).hexdigest()

def db():
    conn = sqlite3.connect(DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_no TEXT UNIQUE,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            pin_hash TEXT NOT NULL,
            balance REAL DEFAULT 0,
            status TEXT DEFAULT 'Pending',
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_no TEXT NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS deposit_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_no TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'Pending',
            reason TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            processed_at TEXT DEFAULT ''
        )
    """)
    conn.commit()
    conn.close()

def next_account_no():
    conn = db()
    row = conn.execute("SELECT account_no FROM customers ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    if not row:
        return "100001"
    try:
        return str(int(row["account_no"]) + 1)
    except:
        return "100001"

def customer_by_account(account_no):
    conn = db()
    row = conn.execute("SELECT * FROM customers WHERE account_no=?", (account_no,)).fetchone()
    conn.close()
    return row

def money(v):
    return f"₹{v:,.2f}"

def add_tx(account_no, typ, amount, description):
    conn = db()
    conn.execute(
        "INSERT INTO transactions(account_no,type,amount,description,created_at) VALUES(?,?,?,?,?)",
        (account_no, typ, amount, description, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()

def css():
    st.markdown("""
    <style>
    .stApp { background: #0b1020; }
    [data-testid="stSidebar"] { background: #10182c; }
    .hero {
        padding: 26px 28px; border-radius: 20px;
        background: linear-gradient(135deg,#16213d,#111827);
        border: 1px solid #263552; margin-bottom: 22px;
    }
    .hero h1 { margin: 0; font-size: 34px; }
    .hero p { color:#aab7cf; margin:8px 0 0; }
    .card {
        background:#121b30; border:1px solid #263552;
        border-radius:18px; padding:20px; min-height:120px;
    }
    .label { color:#8fa0bd; font-size:13px; }
    .value { font-size:28px; font-weight:700; margin-top:6px; }
    .small { color:#9aa9c2; font-size:13px; }
    .status {
        display:inline-block; padding:6px 12px; border-radius:20px;
        font-size:12px; font-weight:700; background:#1e293b;
    }
    .section-title { font-size:22px; font-weight:700; margin:12px 0; }
    div.stButton > button { border-radius:10px; }
    </style>
    """, unsafe_allow_html=True)

def hero(title, subtitle):
    st.markdown(f"""
    <div class="hero">
      <h1>🏦 {title}</h1>
      <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

def customer_home():
    hero("Banking System", "A modern banking management mini project with customer and admin portals.")
    c1,c2,c3 = st.columns(3)
    with c1:
        st.markdown('<div class="card"><div class="label">STORAGE</div><div class="value">SQLite</div><div class="small">Persistent local database</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="card"><div class="label">FRONTEND</div><div class="value">Streamlit</div><div class="small">Responsive web interface</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="card"><div class="label">LANGUAGE</div><div class="value">Python</div><div class="small">Simple and maintainable</div></div>', unsafe_allow_html=True)

    st.write("")
    left, right = st.columns([1, 1.15], gap="large")
    with left:
        st.markdown("### ✨ Customer Portal")
        st.info("Create an account, wait for admin approval, then use your account to manage deposits, transfers, withdrawals and transaction history.")
        st.markdown("### 🔐 Demo Project")
        st.caption("This application is for educational/college project use. Do not use real financial information.")
    with right:
        st.markdown("### 📝 Create Account")
        with st.form("create_account"):
            name = st.text_input("Full Name")
            phone = st.text_input("10-digit Phone Number", max_chars=10)
            pin = st.text_input("4-digit PIN", type="password", max_chars=4)
            submitted = st.form_submit_button("Create Account", use_container_width=True)
            if submitted:
                if not name.strip() or not phone.isdigit() or len(phone) != 10:
                    st.error("Enter a valid full name and 10-digit phone number.")
                elif not pin.isdigit() or len(pin) != 4:
                    st.error("PIN must contain exactly 4 digits.")
                else:
                    conn = db()
                    acc = next_account_no()
                    try:
                        conn.execute(
                            "INSERT INTO customers(account_no,full_name,phone,pin_hash,balance,status,created_at) VALUES(?,?,?,?,?,?,?)",
                            (acc,name.strip(),phone,hash_pin(pin),0,"Pending",
                             datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        )
                        conn.commit()
                        st.success(f"Account created successfully. Account Number: {acc}")
                        st.info("Your account is pending admin approval.")
                    except sqlite3.IntegrityError:
                        st.error("Please try again.")
                    finally:
                        conn.close()

def application_status():
    hero("Application Status", "Check whether your account application has been approved.")
    acc = st.text_input("Account Number")
    if st.button("Check Status", use_container_width=True):
        row = customer_by_account(acc.strip())
        if not row:
            st.error("Account not found.")
        else:
            if row["status"] == "Approved":
                st.success("✅ Account Approved")
            elif row["status"] == "Rejected":
                st.error("❌ Account Rejected")
            else:
                st.warning("⏳ Account Pending Approval")
            st.write(f"**Name:** {row['full_name']}")
            st.write(f"**Account Number:** {row['account_no']}")

def customer_login():
    hero("Customer Login", "Access your approved banking account.")
    with st.form("login"):
        acc = st.text_input("Account Number")
        pin = st.text_input("4-digit PIN", type="password", max_chars=4)
        ok = st.form_submit_button("Login", use_container_width=True)
    if ok:
        row = customer_by_account(acc.strip())
        if not row or row["pin_hash"] != hash_pin(pin):
            st.error("Invalid account number or PIN.")
        elif row["status"] != "Approved":
            st.warning(f"Your account is currently {row['status'].lower()}.")
        else:
            st.session_state.customer = row["account_no"]
            st.rerun()

def customer_dashboard():
    acc = st.session_state.customer
    row = customer_by_account(acc)
    if not row:
        st.session_state.pop("customer", None)
        st.rerun()
    hero("Customer Dashboard", f"Welcome, {row['full_name']} • Account #{row['account_no']}")
    st.markdown(f'<span class="status">● {row["status"]}</span>', unsafe_allow_html=True)
    st.write("")
    a,b,c,d = st.columns(4)
    with a:
        st.markdown(f'<div class="card"><div class="label">AVAILABLE BALANCE</div><div class="value">{money(row["balance"])}</div></div>', unsafe_allow_html=True)
    with b:
        st.markdown(f'<div class="card"><div class="label">ACCOUNT NUMBER</div><div class="value">{row["account_no"]}</div></div>', unsafe_allow_html=True)
    conn=db()
    tx_count=conn.execute("SELECT COUNT(*) c FROM transactions WHERE account_no=?", (acc,)).fetchone()["c"]
    pending=conn.execute("SELECT COUNT(*) c FROM deposit_requests WHERE account_no=? AND status='Pending'", (acc,)).fetchone()["c"]
    conn.close()
    with c:
        st.markdown(f'<div class="card"><div class="label">TRANSACTIONS</div><div class="value">{tx_count}</div></div>', unsafe_allow_html=True)
    with d:
        st.markdown(f'<div class="card"><div class="label">PENDING DEPOSITS</div><div class="value">{pending}</div></div>', unsafe_allow_html=True)

    st.write("")
    st.markdown("### ⚡ Quick Actions")
    q1,q2,q3,q4 = st.columns(4)
    with q1:
        if st.button("💰 Deposit", use_container_width=True): st.session_state.customer_page="Deposit"
    with q2:
        if st.button("💸 Withdraw", use_container_width=True): st.session_state.customer_page="Withdraw"
    with q3:
        if st.button("🔄 Transfer", use_container_width=True): st.session_state.customer_page="Transfer"
    with q4:
        if st.button("📜 History", use_container_width=True): st.session_state.customer_page="History"

    page=st.session_state.get("customer_page","Home")
    if page=="Deposit": customer_deposit()
    elif page=="Withdraw": customer_withdraw()
    elif page=="Transfer": customer_transfer()
    elif page=="History": customer_history()

    st.markdown("### 🧾 Account Information")
    x,y=st.columns(2)
    with x:
        st.write(f"**Full Name:** {row['full_name']}")
        st.write(f"**Phone:** {row['phone']}")
    with y:
        st.write(f"**Created:** {row['created_at']}")
        st.write(f"**Status:** {row['status']}")
    if st.button("Logout", type="secondary"):
        st.session_state.pop("customer", None)
        st.rerun()

def customer_deposit():
    st.markdown("### 💰 Deposit Request")
    with st.form("deposit"):
        amount=st.number_input("Amount", min_value=1.0, step=100.0)
        submit=st.form_submit_button("Submit Deposit Request", use_container_width=True)
    if submit:
        conn=db()
        conn.execute("INSERT INTO deposit_requests(account_no,amount,status,reason,created_at) VALUES(?,?,?,?,?)",
                     (st.session_state.customer,amount,"Pending","",datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit(); conn.close()
        st.success("Deposit request submitted. Admin approval is required.")
    conn=db()
    rows=conn.execute("SELECT * FROM deposit_requests WHERE account_no=? ORDER BY id DESC LIMIT 5",(st.session_state.customer,)).fetchall()
    conn.close()
    for r in rows:
        icon={"Pending":"⏳","Approved":"✅","Rejected":"❌"}.get(r["status"],"•")
        st.write(f"{icon} {money(r['amount'])} — **{r['status']}** — {r['created_at']}")
        if r["status"]=="Rejected" and r["reason"]: st.caption(f"Reason: {r['reason']}")

def customer_withdraw():
    st.markdown("### 💸 Withdraw")
    with st.form("withdraw"):
        amount=st.number_input("Amount",min_value=1.0,step=100.0)
        submit=st.form_submit_button("Withdraw",use_container_width=True)
    if submit:
        row=customer_by_account(st.session_state.customer)
        if amount>row["balance"]: st.error("Insufficient balance.")
        else:
            conn=db()
            conn.execute("UPDATE customers SET balance=balance-? WHERE account_no=?",(amount,st.session_state.customer))
            conn.commit(); conn.close()
            add_tx(st.session_state.customer,"Withdrawal",amount,"Cash withdrawal")
            st.success("Withdrawal successful.")
            st.rerun()

def customer_transfer():
    st.markdown("### 🔄 Transfer")
    with st.form("transfer"):
        target=st.text_input("Receiver Account Number")
        amount=st.number_input("Amount",min_value=1.0,step=100.0)
        submit=st.form_submit_button("Transfer",use_container_width=True)
    if submit:
        sender=customer_by_account(st.session_state.customer)
        receiver=customer_by_account(target.strip())
        if not receiver: st.error("Receiver account not found.")
        elif receiver["status"]!="Approved": st.error("Receiver account is not approved.")
        elif receiver["account_no"]==sender["account_no"]: st.error("You cannot transfer to yourself.")
        elif amount>sender["balance"]: st.error("Insufficient balance.")
        else:
            conn=db()
            conn.execute("UPDATE customers SET balance=balance-? WHERE account_no=?",(amount,sender["account_no"]))
            conn.execute("UPDATE customers SET balance=balance+? WHERE account_no=?",(amount,receiver["account_no"]))
            conn.commit(); conn.close()
            add_tx(sender["account_no"],"Transfer",amount,f"Transfer to {receiver['account_no']}")
            add_tx(receiver["account_no"],"Transfer",amount,f"Received from {sender['account_no']}")
            st.success("Transfer successful.")
            st.rerun()

def customer_history():
    st.markdown("### 📜 Transaction History")
    conn=db()
    rows=conn.execute("SELECT * FROM transactions WHERE account_no=? ORDER BY id DESC",(st.session_state.customer,)).fetchall()
    conn.close()
    if not rows: st.info("No transactions yet.")
    else:
        for r in rows:
            sign="+" if r["type"]=="Deposit" else "-"
            st.write(f"**{r['type']}** · {r['description']} · {money(r['amount'])} · {r['created_at']}")

def admin_login():
    hero("Admin Login", "Secure administration portal.")
    with st.form("admin_login"):
        u=st.text_input("Username")
        p=st.text_input("Password",type="password")
        ok=st.form_submit_button("Admin Login",use_container_width=True)
    if ok:
        if u=="admin" and p=="admin123":
            st.session_state.admin=True
            st.rerun()
        else: st.error("Invalid admin credentials.")

def admin_dashboard():
    st.sidebar.title("🛡️ Admin Panel")
    page=st.sidebar.radio("Navigation",[
        "📊 Dashboard","🛡️ Approval Requests","💰 Deposit Requests","❌ Rejected Requests","👥 Customer Accounts"
    ])
    if st.sidebar.button("Logout"):
        st.session_state.admin=False; st.rerun()

    conn=db()
    total=conn.execute("SELECT COUNT(*) c FROM customers").fetchone()["c"]
    approved=conn.execute("SELECT COUNT(*) c FROM customers WHERE status='Approved'").fetchone()["c"]
    pending=conn.execute("SELECT COUNT(*) c FROM customers WHERE status='Pending'").fetchone()["c"]
    deposits=conn.execute("SELECT COUNT(*) c FROM deposit_requests WHERE status='Pending'").fetchone()["c"]
    conn.close()

    if page=="📊 Dashboard":
        hero("Admin Dashboard","Monitor customers, approvals and deposit requests.")
        a,b,c,d=st.columns(4)
        for col,label,val in [(a,"TOTAL CUSTOMERS",total),(b,"APPROVED",approved),(c,"PENDING ACCOUNTS",pending),(d,"PENDING DEPOSITS",deposits)]:
            with col: st.markdown(f'<div class="card"><div class="label">{label}</div><div class="value">{val}</div></div>',unsafe_allow_html=True)
        st.write("")
        st.info("Use the sidebar to review account applications, deposit requests, rejected requests and customer-specific transactions.")

    elif page=="🛡️ Approval Requests":
        hero("Approval Requests","Review new customer account applications.")
        conn=db(); rows=conn.execute("SELECT * FROM customers WHERE status='Pending' ORDER BY id DESC").fetchall(); conn.close()
        if not rows: st.success("No pending account requests.")
        for r in rows:
            with st.container(border=True):
                x,y=st.columns([3,1])
                with x:
                    st.subheader(r["full_name"])
                    st.write(f"Account: **{r['account_no']}** · Phone: **{r['phone']}**")
                    st.caption(r["created_at"])
                with y:
                    if st.button("✅ Approve",key=f"ap{r['id']}",use_container_width=True):
                        conn=db(); conn.execute("UPDATE customers SET status='Approved' WHERE id=?",(r["id"],)); conn.commit(); conn.close(); st.rerun()
                    if st.button("❌ Reject",key=f"rej{r['id']}",use_container_width=True):
                        conn=db(); conn.execute("UPDATE customers SET status='Rejected' WHERE id=?",(r["id"],)); conn.commit(); conn.close(); st.rerun()

    elif page=="💰 Deposit Requests":
        hero("Deposit Requests","Approve or reject customer deposit requests.")
        conn=db(); rows=conn.execute("SELECT d.*,c.full_name FROM deposit_requests d JOIN customers c ON c.account_no=d.account_no WHERE d.status='Pending' ORDER BY d.id DESC").fetchall(); conn.close()
        if not rows: st.success("No pending deposit requests.")
        for r in rows:
            with st.container(border=True):
                x,y=st.columns([3,1])
                with x:
                    st.subheader(money(r["amount"]))
                    st.write(f"Customer: **{r['full_name']}** · Account: **{r['account_no']}**")
                    st.caption(r["created_at"])
                with y:
                    if st.button("✅ Approve",key=f"da{r['id']}",use_container_width=True):
                        conn=db()
                        conn.execute("UPDATE customers SET balance=balance+? WHERE account_no=?",(r["amount"],r["account_no"]))
                        conn.execute("UPDATE deposit_requests SET status='Approved',processed_at=? WHERE id=?",(datetime.now().strftime("%Y-%m-%d %H:%M:%S"),r["id"]))
                        conn.commit(); conn.close()
                        add_tx(r["account_no"],"Deposit",r["amount"],"Deposit approved by admin")
                        st.rerun()
                    if st.button("❌ Reject",key=f"dr{r['id']}",use_container_width=True):
                        conn=db()
                        conn.execute("UPDATE deposit_requests SET status='Rejected',reason=?,processed_at=? WHERE id=?",
                                     ("Rejected by admin",datetime.now().strftime("%Y-%m-%d %H:%M:%S"),r["id"]))
                        conn.commit(); conn.close(); st.rerun()

    elif page=="❌ Rejected Requests":
        hero("Rejected Requests","Review rejected account and deposit requests.")
        conn=db()
        accounts=conn.execute("SELECT * FROM customers WHERE status='Rejected' ORDER BY id DESC").fetchall()
        deps=conn.execute("SELECT d.*,c.full_name FROM deposit_requests d JOIN customers c ON c.account_no=d.account_no WHERE d.status='Rejected' ORDER BY d.id DESC").fetchall()
        conn.close()
        st.markdown("### Account Requests")
        if not accounts: st.caption("No rejected account requests.")
        for r in accounts: st.write(f"❌ **{r['full_name']}** · Account {r['account_no']} · {r['created_at']}")
        st.markdown("### Deposit Requests")
        if not deps: st.caption("No rejected deposit requests.")
        for r in deps: st.write(f"❌ **{r['full_name']}** · {money(r['amount'])} · Account {r['account_no']} · {r['reason']}")

    elif page=="👥 Customer Accounts":
        hero("Customer Accounts","View all customers and their account-specific transactions.")
        conn=db(); rows=conn.execute("SELECT * FROM customers ORDER BY id DESC").fetchall(); conn.close()
        if not rows: st.info("No customers found.")
        for r in rows:
            with st.container(border=True):
                x,y=st.columns([3,1])
                with x:
                    st.subheader(r["full_name"])
                    st.write(f"Account: **{r['account_no']}** · Phone: **{r['phone']}**")
                    st.write(f"Balance: **{money(r['balance'])}** · Status: **{r['status']}**")
                with y:
                    if st.button("📜 View Transactions",key=f"vt{r['id']}",use_container_width=True):
                        st.session_state.view_account=r["account_no"]
                if st.session_state.get("view_account")==r["account_no"]:
                    conn=db(); tx=conn.execute("SELECT * FROM transactions WHERE account_no=? ORDER BY id DESC",(r["account_no"],)).fetchall(); conn.close()
                    st.markdown("**Transactions for this customer**")
                    if not tx: st.caption("No transactions.")
                    else:
                        for t in tx:
                            st.write(f"• {t['type']} — {money(t['amount'])} — {t['description']} — {t['created_at']}")

def main():
    init_db()
    css()
    if "customer" in st.session_state:
        customer_dashboard()
        return
    if st.session_state.get("admin"):
        admin_dashboard()
        return

    nav=st.radio("",["Create Account","Customer Login","Application Status","Admin"],horizontal=True,label_visibility="collapsed")
    if nav=="Create Account": customer_home()
    elif nav=="Customer Login": customer_login()
    elif nav=="Application Status": application_status()
    else: admin_login()

if __name__=="__main__":
    main()
