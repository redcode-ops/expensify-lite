# Expensify Lite v2 – Smart Expense Tracker with TinyDB + Login + Daily/Monthly Summary + CSV Export + Feedback

import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from tinydb import TinyDB, Query
import os

# -------------------------
# Setup
# -------------------------
st.set_page_config(page_title="Expensify Lite", page_icon="💸")
st.title("💸 Expensify Lite")

# Timezone: India
india_tz = pytz.timezone('Asia/Kolkata')
now = datetime.now(india_tz)

# -------------------------
# DB Setup
# -------------------------
os.makedirs("db", exist_ok=True)
db = TinyDB("db/expenses.json")
user_table = TinyDB("db/users.json")
feedback_table = TinyDB("db/feedback.json")

# -------------------------
# Session State
# -------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

# -------------------------
# Login / Signup
# -------------------------
if not st.session_state.logged_in:
    tabs = st.tabs(["🔐 Login", "📝 Sign Up"])

    with tabs[0]:
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            User = Query()
            result = user_table.search((User.email == email) & (User.password == password))
            if result:
                st.session_state.logged_in = True
                st.session_state.user = email
                st.success("✅ Logged in successfully!")
                st.rerun()
            else:
                st.error("❌ Invalid credentials")

    with tabs[1]:
        new_email = st.text_input("New Email")
        new_pass = st.text_input("New Password", type="password")
        if st.button("Create Account"):
            User = Query()
            exists = user_table.search(User.email == new_email)
            if exists:
                st.warning("⚠️ Email already registered")
            else:
                user_table.insert({"email": new_email, "password": new_pass})
                st.success("✅ Account created! Please login.")

    st.stop()

# -------------------------
# Main App
# -------------------------
st.markdown(f"**👤 Logged in as:** `{st.session_state.user}`")
st.markdown(f"**📅 Date:** {now.strftime('%d-%m-%Y')} | **🕒 Time (IST):** {now.strftime('%I:%M:%S %p')}")

# Expense Entry
with st.form("Add Expense"):
    col1, col2 = st.columns([3, 1])
    with col1:
        note = st.text_input("📝 What did you spend on?")
    with col2:
        amount = st.number_input("₹ Amount", min_value=1.0, step=0.5)

    category = st.selectbox("📁 Category", ["Food", "Travel", "Shopping", "Bills", "Health", "Other"])
    submitted = st.form_submit_button("Add")

    if submitted and note and amount:
        db.insert({
            "user": st.session_state.user,
            "note": note,
            "amount": amount,
            "category": category,
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%I:%M:%S %p")
        })
        st.success("✅ Expense added!")

# Load user expenses
records = db.search(Query().user == st.session_state.user)

# Search Filter
search = st.text_input("🔎 Search your expenses")
if search:
    records = [r for r in records if search.lower() in r["note"].lower()]

if records:
    df = pd.DataFrame(records)
    st.subheader("📋 Your Expenses")
    st.dataframe(df[["note", "amount", "category", "date", "time"]], use_container_width=True)

    total = df["amount"].sum()
    st.metric("💰 Total Spent", f"₹{total:.2f}")

    # Category Summary
    cat_df = df.groupby("category")["amount"].sum().reset_index()
    st.subheader("📊 Spend by Category")
    st.bar_chart(cat_df, x="category", y="amount")

    # Daily Summary
    df["date"] = pd.to_datetime(df["date"])
    daily = df.groupby(df["date"].dt.date)["amount"].sum().reset_index()
    st.subheader("📆 Daily Spend")
    st.bar_chart(daily, x="date", y="amount")

    # Monthly Summary
    df["month"] = df["date"].dt.strftime("%B %Y")
    monthly = df.groupby("month")["amount"].sum().reset_index()
    st.subheader("🗓️ Monthly Spend")
    st.bar_chart(monthly, x="month", y="amount")

    # Download CSV
    st.download_button("⬇️ Download CSV", data=df.to_csv(index=False).encode(), file_name="expenses.csv", mime="text/csv")
else:
    st.info("No expenses to show.")

# Feedback Form
with st.expander("💬 Share Feedback"):
    feedback_text = st.text_area("Your feedback")
    if st.button("Submit Feedback"):
        if feedback_text.strip():
            feedback_table.insert({
                "user": st.session_state.user,
                "feedback": feedback_text.strip(),
                "submitted": now.strftime("%Y-%m-%d %I:%M %p")
            })
            st.success("✅ Feedback submitted! Thank you.")
        else:
            st.warning("⚠️ Please enter feedback before submitting.")

# Logout
st.sidebar.title("🔓 Logout")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.user = None
    st.rerun()
