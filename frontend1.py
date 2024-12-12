import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import base64
import time
import threading
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Set the page title and layout
st.set_page_config(page_title="Email Management Dashboard", layout="wide")

# Initialize session state variables if not set
if 'page' not in st.session_state:
    st.session_state.page = "Register"  # Default page
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'email' not in st.session_state:
    st.session_state.email = ""
if 'selected_mailbox' not in st.session_state:
    st.session_state.selected_mailbox = None  # Track selected mailbox

# Function to simulate adding default values to mailboxes
def add_default_values(contact):
    defaults = {
        "health": 8.9,
        "deliverability": "50%",
        "spam_count": 5,
        "landed_in_inbox": "94%",
    }
    for key, value in defaults.items():
        contact.setdefault(key, value)
    return contact

# Function to send email via SMTP
def send_email_via_smtp(mailbox, recipients, subject, body, signature):
    msg = MIMEMultipart()
    msg['From'] = mailbox["email"]
    msg['To'] = ", ".join(recipients['to'])
    if recipients['cc']:
        msg['CC'] = ", ".join(recipients['cc'])
    if recipients['bcc']:
        msg['BCC'] = ", ".join(recipients['bcc'])
    if recipients['reply_to']:
        msg.add_header("Reply-To", recipients['reply_to'])
    msg['Subject'] = subject
    msg.attach(MIMEText(body + "\n\n" + signature, 'plain'))

    try:
        # Send via SMTP (Note: This is a placeholder. In real implementation, 
        # you'd need to handle authentication securely)
        with smtplib.SMTP(mailbox["smtp_server"]) as server:
            server.starttls()
            # Replace with secure password handling
            server.login(mailbox["email"], "your_password_here")
            server.sendmail(mailbox["email"], recipients['to'] + recipients['cc'] + recipients['bcc'], msg.as_string())
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False

# Function to schedule email sending
def schedule_send_email(mailbox, recipients, subject, body, signature, delay):
    time.sleep(delay)
    send_email_via_smtp(mailbox, recipients, subject, body, signature)

# -------------------- REGISTER PAGE --------------------
if st.session_state.page == "Register":
    st.title("Create Your Account")

    email = st.text_input("Email", placeholder="Enter your email")
    password = st.text_input("Password", type="password", placeholder="Choose a strong password")
    confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm password")

    if st.button("Register"):
        if email and password and password == confirm_password:
            st.success("Registration successful! Please proceed to login.")
            st.session_state.page = "Login"
            st.session_state.email = email
            st.experimental_rerun()

        else:
            st.error("Error: Please check your inputs.")

    if st.button("Already have an account? Login"):
        st.session_state.page = "Login"
        st.experimental_rerun()

# -------------------- LOGIN PAGE --------------------
elif st.session_state.page == "Login":
    st.title("Login to Your Account")

    email_login = st.text_input("Email", placeholder="Enter your email")
    password_login = st.text_input("Password", type="password", placeholder="Enter your password")

    if st.button("Login"):
        if email_login == st.session_state.email and password_login:
            st.session_state.logged_in = True
            st.session_state.page = "Email Management Dashboard"
            st.success("Login successful!")
            st.experimental_rerun()

        else:
            st.error("Invalid email or password. Please try again.")

    if st.button("Don't have an account? Register"):
        st.session_state.page = "Register"
        st.experimental_rerun()

# -------------------- SEND MAIL PAGE --------------------
elif st.session_state.page == "Email Statistics":
    st.title("Email Statistics")
    st.write(f"Welcome, *{st.session_state.email}*!")

    # Side navigation bar
    st.sidebar.title("Navigation")
    page_options = ["Email Management Dashboard", "Email Statistics"]
    st.session_state.page = st.sidebar.radio("Go to", page_options)

    # Mailbox Management Section
    st.subheader("Mailbox Management")
    st.write("### Mailboxes List")

    # Simulated mailbox data
    mailboxes = [
        {"id": 1, "name": "Personal Mailbox", "email": st.session_state.email, "smtp_server": "smtp.gmail.com", "health": 8.4, "deliverability": "95%", "spam_count": 5, "landed_in_inbox": "94%"},
        {"id": 2, "name": "Work Mailbox", "email": f"{st.session_state.email.split('@')[0]}@companydomain.com", "smtp_server": "smtp.outlook.com", "health": 9.3, "deliverability": "92%", "spam_count": 3, "landed_in_inbox": "92%" }
    ]

    mailboxes = [add_default_values(mailbox) for mailbox in mailboxes]

    # Email sending section
    st.subheader("Email Statistics")
    st.write("### Choose your email settings")

    # Select mailbox
    mailbox_options = [mailbox['name'] for mailbox in mailboxes]
    selected_mailbox_name = st.selectbox("Select Mailbox", mailbox_options)
    selected_mailbox = next(mailbox for mailbox in mailboxes if mailbox["name"] == selected_mailbox_name)

    # Upload CSV for recipients
    uploaded_file = st.file_uploader("Upload CSV with recipients (To, CC, BCC)", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write("Recipients List:")
        st.write(df)

    # Email fields
    to_field = st.text_input("To (comma-separated email addresses)")
    cc_field = st.text_input("CC (comma-separated email addresses)", help="Optional")
    bcc_field = st.text_input("BCC (comma-separated email addresses)", help="Optional")
    reply_to_field = st.text_input("Reply-To (email address)", help="Optional")
    
    # Subject, body, and signature
    subject = st.text_input("Subject")
    body = st.text_area("Body")
    signature = st.text_area("Signature", placeholder="Add your email signature here")

    # Template Option
    use_template = st.radio("Use Template?", ("No", "Yes"))
    if use_template == "Yes":
        template_options = ["Professional Intro", "Business Proposal", "Follow-up"]
        template_choice = st.selectbox("Select Template", template_options)
        
        if template_choice == "Professional Intro":
            body = f"Dear [Recipient],\n\nI hope this email finds you well. My name is {st.session_state.email.split('@')[0]}, and I'm reaching out to...\n\nBest regards,\n{st.session_state.email.split('@')[0]}"
        elif template_choice == "Business Proposal":
            body = f"Dear [Recipient],\n\nI am writing to discuss a potential business opportunity that could be of interest to your organization...\n\nSincerely,\n{st.session_state.email.split('@')[0]}"
        elif template_choice == "Follow-up":
            body = f"Dear [Recipient],\n\nI'm following up on our previous conversation regarding...\n\nLooking forward to your response,\n{st.session_state.email.split('@')[0]}"

    # Scheduling Option
    schedule_email = st.radio("Schedule Email?", ("No", "Yes"))
    if schedule_email == "Yes":
        schedule_date = st.date_input("Schedule Date", min_value=datetime.today().date())
        schedule_time = st.time_input("Schedule Time")

    # Send Email Button
    if st.button("Send/Schedule Email"):
        if to_field and subject and body:
            recipients = {
                "to": [email.strip() for email in to_field.split(",")],
                "cc": [email.strip() for email in cc_field.split(",")] if cc_field else [],
                "bcc": [email.strip() for email in bcc_field.split(",")] if bcc_field else [],
                "reply_to": reply_to_field.strip() if reply_to_field else selected_mailbox["email"]
            }

            if schedule_email == "No":
                # Send immediately
                if send_email_via_smtp(selected_mailbox, recipients, subject, body, signature):
                    st.success("Email sent successfully!")
                else:
                    st.error("Failed to send email.")
            else:
                # Schedule email
                schedule_datetime = datetime.combine(schedule_date, schedule_time)
                time_diff = (schedule_datetime - datetime.now()).total_seconds()

                if time_diff > 0:
                    thread = threading.Thread(target=schedule_send_email, 
                                              args=(selected_mailbox, recipients, subject, body, signature, time_diff))
                    thread.start()
                    st.success(f"Email scheduled for {schedule_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    st.error("Scheduled time must be in the future!")
        else:
            st.error("Please fill in To, Subject, and Body fields.")

    # Logout button
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.page = "Login"
        st.experimental_rerun()

# -------------------- EMAIL DASHBOARD PAGE --------------------
elif st.session_state.page == "Email Management Dashboard":
    st.title("Email Management Dashboard")
    st.write(f"Welcome, *{st.session_state.email}*!")

    # Side navigation bar
    st.sidebar.title("Navigation")
    page_options = ["Email Management Dashboard", "Email Statistics"]
    st.session_state.page = st.sidebar.radio("Go to", page_options)

    # Create two columns for the graphs
    col1, col2 = st.columns(2)

    # Spacer between graphs for a cleaner layout
    st.write("<br>", unsafe_allow_html=True)

    st.subheader("Your Daily Email Limit is 100. Please increase by 50 per day.")

    # Performance Summary Section
    st.subheader("Performance Summary")
    col1, col2, col3, col4 = st.columns(4)

    # Example performance data
    performance_data = {
        "Sent": {"value": 1876, "change": "+5% from last week"},
        "Delivered": {"value": 1786, "change": "+5% from last week"},
        "Landed in Inbox": {"value": "94%", "change": "+2% from last week"},
        "Landed in Spam": {"value": "5%", "change": "-1% from last week"},
    }

    col1.metric("Sent", performance_data["Sent"]["value"], performance_data["Sent"]["change"])
    col2.metric("Delivered", performance_data["Delivered"]["value"], performance_data["Delivered"]["change"])
    col3.metric("Landed in Inbox", performance_data["Landed in Inbox"]["value"], performance_data["Landed in Inbox"]["change"])
    col4.metric("Landed in Spam", performance_data["Landed in Spam"]["value"], performance_data["Landed in Spam"]["change"])

    # Mailbox Management Section
    st.subheader("Mailbox Management")
    st.write("### Mailboxes List")

    # Simulated mailbox data
    mailboxes = [
        {"id": 1, "name": "Personal Mailbox", "email": st.session_state.email, "smtp_server": "smtp.gmail.com", "health": 8.4, "deliverability": "95%", "spam_count": 5, "landed_in_inbox": "94%"},
        {"id": 2, "name": "Work Mailbox", "email": f"{st.session_state.email.split('@')[0]}@companydomain.com", "smtp_server": "smtp.outlook.com", "health": 9.3, "deliverability": "92%", "spam_count": 3, "landed_in_inbox": "92%" }
    ]

    mailboxes = [add_default_values(mailbox) for mailbox in mailboxes]

    # Display mailboxes with columns
    col0, col1, col2, col3, col4, col5 = st.columns([1, 3, 3, 3, 2, 3])

    col0.write("**Select**")
    col1.write("**Name**")
    col2.write("**Email**")
    col3.write("**SMTP Server**")
    col4.write("**Deliverability Score**")
    col5.write("**Health**")

    for mailbox in mailboxes:
        with col0:
            selected = st.checkbox("", key=f"mailbox_{mailbox['id']}")
            if selected:
                # Update the session state with the selected mailbox
                st.session_state.selected_mailbox = mailbox
                deliverability_score = int(mailbox['landed_in_inbox'].strip('%'))
                health_score = mailbox['health']
                spam_count = mailbox['spam_count']

        with col1:
            st.write(mailbox['name'])
        with col2:
            st.write(mailbox['email'])
        with col3:
            st.write(mailbox['smtp_server'])
        with col4:
            st.write(mailbox['landed_in_inbox'])
        with col5:
            st.write(mailbox['health'])

    # Update the graphs dynamically when a mailbox is selected
    if st.session_state.selected_mailbox:
        selected_mailbox = st.session_state.selected_mailbox
        # Update Deliverability Score Graph based on Landed in Inbox
        deliverability_score = int(selected_mailbox['landed_in_inbox'].strip('%'))
        health_score = selected_mailbox['health']
        spam_count = selected_mailbox['spam_count']
        
        fig1 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=deliverability_score,
            title={'text': "Deliverability Score (%)"},
            gauge={'axis': {'range': [None, 100]}, 'bar': {'color': "#1e90ff"}}
        ))
        st.plotly_chart(fig1, use_container_width=True)

        # Spacer for cleaner layout between the graphs
        st.write("<br>", unsafe_allow_html=True)

        # Update Health Performance Graph
        fig2 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=health_score,
            title={'text': "Health Performance (%)"},
            gauge={'axis': {'range': [None, 10]}, 'bar': {'color': "#28a745"}}
        ))
        st.plotly_chart(fig2, use_container_width=True)

        # Combine deliverability, health, and spam count into a single pie chart
        avg_deliverability = sum([int(mailbox['landed_in_inbox'].strip('%')) for mailbox in mailboxes]) / len(mailboxes)
        avg_health = sum([mailbox['health'] for mailbox in mailboxes]) / len(mailboxes)
        avg_spam_count = sum([mailbox['spam_count'] for mailbox in mailboxes]) / len(mailboxes)

        # Combined pie chart
        total = avg_deliverability + avg_health + avg_spam_count
        combined_pie = go.Figure(data=[go.Pie(
            labels=["Deliverability", "Health", "Spam Count"],
            values=[avg_deliverability, avg_health, avg_spam_count],
            marker=dict(colors=["#00BFFF", "#32CD32", "#FF6347"])  # Professional colors
        )])

        # Update layout for better visual
        combined_pie.update_layout(
            title="Overall Performance",
            font_size=24,  # Increase font size
            height=600,
            showlegend=True,
            margin={"t": 50, "b": 50, "l": 50, "r": 50}  # Add padding around the pie chart
        )

        # Center the pie chart
        st.plotly_chart(combined_pie, use_container_width=True)
        
    # Simulate statistics data
    email_stats = {
        "Total Sent": 4000,
        "Delivered": 3800,
        "Open Rate": "85%",
        "Click Rate": "30%",
        "Bounce Rate": "1%",
        "Unsubscribed": "0.5%",
    }

    # Show statistics data
    st.subheader("Performance Summary")
    col1, col2 = st.columns(2)

    col1.write(f"*Total Sent*: {email_stats['Total Sent']}")
    col2.write(f"*Delivered*: {email_stats['Delivered']}")

    col1.write(f"*Open Rate*: {email_stats['Open Rate']}")
    col2.write(f"*Click Rate*: {email_stats['Click Rate']}")

    col1.write(f"*Bounce Rate*: {email_stats['Bounce Rate']}")
    col2.write(f"*Unsubscribed*: {email_stats['Unsubscribed']}")

    # Optionally, add a bar chart for more visual presentation
    fig3 = go.Figure(data=[go.Bar(
        x=["Sent", "Delivered", "Open Rate", "Click Rate", "Bounce Rate", "Unsubscribed"],
        y=[email_stats["Total Sent"], email_stats["Delivered"], 85, 30, 1, 0.5],
        marker=dict(color=["#FF6347", "#1e90ff", "#28a745", "#32CD32", "#FF4500", "#FFD700"])
    )])
    fig3.update_layout(title="Email Performance Metrics", showlegend=False)
    st.plotly_chart(fig3, use_container_width=True)

    # Logout button
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.page = "Login"
        st.experimental_rerun()