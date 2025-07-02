# Expensify Lite v2 – Persistent User Auth + UI Enhancements + Feedback Box

import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os

# -------------------------
# Page Setup & Custom CSS
# -------------------------
st.set_page_config(page_title="Expensify Lite", page_icon="💸", layout="centered")

st.markdown("""
    <style>
    body {
        background-color: #f8f9fa;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Segoe UI', sans-serif;
        color: #333333;
    }
    .stTextInput > label, .stNumberInput > label, .stSelectbox > label {
        font-weight: 500;
        font-size: 16px;
    }
    </style>
""", unsafe_allow_html=True)

# Timezone: India Standard Time
india_timezone = pytz.timezone('Asia/Kolkata')
now = datetime.now(india_timezone)

# -------------------------
# Load/Save Users
# -------------------------
user_db_file = "data/users.csv"
os.makedirs("data", exist_ok=True)

if os.path.exists(user_db_file):
    user_df = pd.read_csv(user_db_file)
    users_db = dict(zip(user_df["Email"], user_df["Password"]))
else:
    users_db = {}
    pd.DataFrame(columns=["Email", "Password"]).to_csv(user_db_file, index=False)

# -------------------------
# Session State Setup
# -------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.expenses = []

# -------------------------
# SIGN-UP / LOGIN SYSTEM
# -------------------------
if not st.session_state.logged_in:
    st.markdown("""<h2 style='text-align:center;'>Welcome to <span style='color:#27ae60;'>Expensify Lite</span></h2>""", unsafe_allow_html=True)

    tabs = st.tabs(["🔐 Login", "📝 Sign Up"])

    with tabs[0]:
        email = st.text_input("Email", key="login_email").strip()
        password = st.text_input("Password", type="password", key="login_password").strip()

        if st.button("Login"):
            if email in users_db:
                if password == users_db[email]:
                    st.session_state.logged_in = True
                    st.session_state.user = email

                    file_path = f"expenses/{email.replace('@', '_at_')}.csv"
                    if os.path.exists(file_path):
                        st.session_state.expenses = pd.read_csv(file_path).to_dict("records")
                    else:
                        st.session_state.expenses = []

                    user_log_path = "users/expensify_users.csv"
                    os.makedirs("users", exist_ok=True)
                    login_data = {
                        "Email": email,
                        "Login Time": now.strftime("%Y-%m-%d %I:%M:%S %p"),
                        "Total Expenses": len(st.session_state.expenses),
                        "Last Updated": now.strftime("%Y-%m-%d")
                    }

                    if os.path.exists(user_log_path):
                        user_df = pd.read_csv(user_log_path)
                        user_df = user_df[user_df["Email"] != email]
                        user_df = pd.concat([user_df, pd.DataFrame([login_data])], ignore_index=True)
                    else:
                        user_df = pd.DataFrame([login_data])

                    user_df.to_csv(user_log_path, index=False)
                    st.success(f"✅ Welcome, {email}")
                    st.rerun()
                else:
                    st.error("❌ Incorrect password")
            else:
                st.error("❌ Email not found")

    with tabs[1]:
        new_email = st.text_input("New Email", key="signup_email").strip()
        new_password = st.text_input("New Password", type="password", key="signup_password").strip()

        if st.button("Sign Up"):
            if new_email in users_db:
                st.warning("⚠️ Email already registered. Please log in.")
            elif not new_email or not new_password:
                st.warning("⚠️ Please enter both email and password.")
            else:
                new_entry = pd.DataFrame([[new_email, new_password]], columns=["Email", "Password"])
                new_entry.to_csv(user_db_file, mode='a', index=False, header=False)
                st.success("✅ Account created! Please login now.")

    st.stop()

# -------------------------
# MAIN APP AFTER LOGIN
# -------------------------
st.markdown("""<h2 style='margin-bottom:0;'>💸 Expensify Lite</h2>""", unsafe_allow_html=True)
st.caption(f"👤 Logged in as: `{st.session_state.user}`")
st.caption(f"📅 Date: {now.strftime('%d-%m-%Y')} | 🕒 Time (IST): {now.strftime('%I:%M:%S %p')}")

file_path = f"expenses/{st.session_state.user.replace('@', '_at_')}.csv"

# -------------------------
# Add Expense Form
# -------------------------
st.markdown("""<h4 style='margin-top:30px;'>➕ Add a New Expense</h4>""", unsafe_allow_html=True)
with st.form("Add Expense"):
    col1, col2 = st.columns([3, 1])
    with col1:
        note = st.text_input("What did you spend on?")
    with col2:
        amount = st.number_input("Amount (₹)", min_value=1.0, step=0.5)

    category = st.selectbox("Category", ["Food", "Travel", "Shopping", "Bills", "Health", "Other"])
    submitted = st.form_submit_button("Add")

    if submitted and note and amount:
        st.session_state.expenses.append({
            "Note": note,
            "Amount": amount,
            "Category": category,
            "Date": now.strftime("%Y-%m-%d"),
            "Time": now.strftime("%I:%M:%S %p")
        })
        st.success("✅ Expense added!")

        df_all = pd.DataFrame(st.session_state.expenses)
        os.makedirs("expenses", exist_ok=True)
        df_all.to_csv(file_path, index=False)

# -------------------------
# Filter & Search
# -------------------------
search = st.text_input("Search expenses by keyword")
if search:
    filtered = [e for e in st.session_state.expenses if search.lower() in e["Note"].lower()]
else:
    filtered = st.session_state.expenses

# -------------------------
# Display Table & Charts
# -------------------------
if filtered:
    df = pd.DataFrame(filtered)
    st.markdown("<h4>Your Expenses</h4>", unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True)

    total = sum(e["Amount"] for e in filtered)
    st.metric("💰 Total Spent", f"₹{total:.2f}")

    cat_df = df.groupby("Category")["Amount"].sum().reset_index()
    st.subheader("Spend by Category")
    st.bar_chart(cat_df, x="Category", y="Amount")

    df["Date"] = pd.to_datetime(df["Date"])
    daily = df.groupby(df["Date"].dt.date)["Amount"].sum().reset_index()
    st.subheader("Daily Spend Summary")
    st.dataframe(daily, use_container_width=True)
    st.bar_chart(daily, x="Date", y="Amount")

    df["Month"] = df["Date"].dt.strftime('%B %Y')
    monthly = df.groupby("Month")["Amount"].sum().reset_index()
    st.subheader("Monthly Spend Summary")
    st.dataframe(monthly, use_container_width=True)
    st.bar_chart(monthly, x="Month", y="Amount")

    csv = df.to_csv(index=False).encode()
    st.download_button("⬇️ Download CSV", data=csv, file_name=f"{st.session_state.user}_expenses.csv", mime="text/csv")
else:
    st.info("No expenses yet.")

# -------------------------
# Feedback Section
# -------------------------
st.markdown("""<hr><h4>💬 Got Feedback?</h4>""", unsafe_allow_html=True)
with st.form("Feedback"):
    feedback = st.text_area("Share your thoughts to help us improve:", placeholder="This app is great but I wish it had...")
    send = st.form_submit_button("Send Feedback")

    if send and feedback:
        feedback_path = "data/feedback.csv"
        os.makedirs("data", exist_ok=True)
        feedback_df = pd.DataFrame([{
            "Email": st.session_state.user,
            "Feedback": feedback,
            "Time": now.strftime("%Y-%m-%d %I:%M:%S %p")
        }])
        if os.path.exists(feedback_path):
            old_df = pd.read_csv(feedback_path)
            all_df = pd.concat([old_df, feedback_df], ignore_index=True)
        else:
            all_df = feedback_df
        all_df.to_csv(feedback_path, index=False)
        st.success("✅ Thanks for your feedback!")

        # -------------------------
# 📊 Visual Tracker of All Users (only visible to you)
# -------------------------
if st.session_state.user == "redcodeops@gmail.com":
    if os.path.exists("users/expensify_users.csv"):
        st.markdown("<hr><h4>📊 User Login Activity</h4>", unsafe_allow_html=True)
        log_df = pd.read_csv("users/expensify_users.csv")
        
        st.dataframe(log_df, use_container_width=True)
        st.metric("🧑‍💻 Total Users", log_df['Email'].nunique())
        
        daily_logins = log_df.groupby("Login Time")["Email"].count().reset_index()
        daily_logins.columns = ["Time", "Logins"]
        
        st.subheader("🕒 Login Timeline")
        st.line_chart(daily_logins.set_index("Time"))


# -------------------------
# Logout
# -------------------------
st.sidebar.title("🔓 Logout")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.expenses = []
    st.rerun()
