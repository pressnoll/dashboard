import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import datetime
import firebase_config
from dateutil import parser
import hashlib

# Set page configuration
st.set_page_config(
    page_title="Staff Attendance System",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Fix theme and visibility issues
st.markdown("""
<style>
/* Overall background fix */
.main {
    background-color: #ffffff;
}
/* Fix for navigation text visibility in sidebar */
section[data-testid="stSidebar"] {
    background-color: #262730;
}
.css-1d391kg, .css-1wrcr25 {
    color: white !important;
}
button[kind="secondary"] {
    background-color: #1565C0 !important;
    color: white !important;
}
.stRadio label, .stRadio div {
    color: white !important;
}
/* Navigation text fix */
.css-pkbazv {
    color: white !important;
}
/* Better contrast for content */
.css-18e3th9 {
    padding: 1rem 1rem 1.5rem;
}
/* Improve button visibility */
.stButton button {
    background-color: #1565C0;
    color: white;
    font-weight: bold;
}
/* Improve text readability */
h1, h2, h3 {
    color: #1565C0 !important;
    font-weight: 700 !important;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'user_role' not in st.session_state:
    st.session_state.user_role = ""

# Initialize Firebase
db = firebase_config.initialize_firebase()

# Database functions
def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def check_user_credentials(db, username, password):
    """Verify user credentials from Firestore."""
    try:
        users_ref = db.collection('users')
        query = users_ref.where('username', '==', username).limit(1)
        results = query.get()
        if len(results) > 0:
            user_data = results[0].to_dict()
            stored_hash = user_data.get('password', '')
            if stored_hash == hash_password(password):
                return user_data.get('role', 'admin')
        return None
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return None

def get_staff_list(db):
    """Get list of all staff members from registration collection"""
    try:
        registration_ref = db.collection('registration')
        registration_docs = registration_ref.get()
        staff_list = []
        for doc in registration_docs:
            staff_data = doc.to_dict()
            staff_data['id'] = doc.id
            staff_list.append(staff_data)
        return staff_list
    except Exception as e:
        st.error(f"Error fetching staff list: {str(e)}")
        return []

def get_attendance_data(db):
    """Get attendance data from all 'records' subcollections under each date in 'attendance'"""
    try:
        attendance_ref = db.collection('attendance')
        attendance_docs = attendance_ref.get()
        attendance_data = []
        for doc in attendance_docs:
            date_id = doc.id
            parent_data = doc.to_dict()
            records_ref = attendance_ref.document(date_id).collection('records')
            records_docs = records_ref.get()
            for record_doc in records_docs:
                data = record_doc.to_dict()
                data['id'] = record_doc.id
                data['date'] = parent_data.get('date', date_id)  # Use parent doc's date or doc id
                attendance_data.append(data)
        return attendance_data
    except Exception as e:
        st.error(f"Error fetching attendance data: {str(e)}")
        return []

def register_attendance(db, staff_name, action_type, timestamp):
    """Register check-in or check-out"""
    try:
        attendance_ref = db.collection('attendance')
        
        date_str = timestamp.strftime('%Y-%m-%d')
        time_str = timestamp.strftime('%H:%M:%S')
        
        # Check if there's an existing record for today
        query = attendance_ref.where('staff_name', '==', staff_name).where('date', '==', date_str).limit(1)
        results = query.get()
        
        if action_type == "check_in":
            if len(results) == 0:
                # New attendance record
                attendance_ref.add({
                    'staff_name': staff_name,
                    'date': date_str,
                    'check_in': time_str,
                    'check_out': None,
                    'status': 'present'
                })
            else:
                # Update existing record
                doc_id = results[0].id
                attendance_ref.document(doc_id).update({
                    'check_in': time_str,
                    'status': 'present'
                })
        elif action_type == "check_out":
            if len(results) > 0:
                # Update existing record
                doc_id = results[0].id
                attendance_ref.document(doc_id).update({
                    'check_out': time_str
                })
            else:
                # Unusual case: Check-out without check-in
                attendance_ref.add({
                    'staff_name': staff_name,
                    'date': date_str,
                    'check_in': None,
                    'check_out': time_str,
                    'status': 'present'
                })
        
        return True
    except Exception as e:
        st.error(f"Error registering attendance: {str(e)}")
        return False

def create_chart(chart_type, data, x_col, y_col, title):
    """Create various chart types"""
    plt.figure(figsize=(10, 6))
    
    if chart_type == "bar":
        sns.barplot(x=x_col, y=y_col, data=data)
    elif chart_type == "line":
        sns.lineplot(x=x_col, y=y_col, data=data)
    elif chart_type == "pie":
        plt.pie(data[y_col], labels=data[x_col], autopct='%1.1f%%')
    
    plt.title(title)
    plt.tight_layout()
    return plt

def login_page():
    st.title("Staff Attendance System")
    st.subheader("Login")
    tab_login, tab_signup = st.tabs(["Sign In", "Sign Up"])
    with tab_login:
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            if username and password:
                user_role = check_user_credentials(db, username, password)
                if user_role:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.user_role = user_role
                    st.experimental_rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.warning("Please enter both username and password")
    with tab_signup:
        st.markdown("#### Register New User (Admin Only)")
        new_username = st.text_input("New Username", key="signup_username")
        new_password = st.text_input("New Password", type="password", key="signup_password")
        new_role = st.selectbox("Role", ["admin", "staff"], key="signup_role")
        if st.button("Sign Up"):
            if new_username and new_password:
                # Check if user exists
                users_ref = db.collection('users')
                query = users_ref.where('username', '==', new_username).limit(1)
                results = query.get()
                if len(results) > 0:
                    st.error("Username already exists.")
                else:
                    # Add new user
                    users_ref.add({
                        'username': new_username,
                        'password': hash_password(new_password),
                        'role': new_role
                    })
                    st.success(f"User '{new_username}' registered successfully.")
            else:
                st.warning("Please enter both username and password.")
    st.markdown("<div style='margin-top: 2rem; background-color: #E3F2FD; padding: 10px; border-radius: 5px;'><span style='color: #0D47A1;'>Welcome to the Staff Attendance System. Please login or sign up to continue.</span></div>", unsafe_allow_html=True)

def logout():
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.user_role = ""
    st.experimental_rerun()

def display_dashboard():
    st.title("Staff Attendance Dashboard")
    st.markdown(f"""
    <div style="background-color:#E3F2FD; padding:10px; border-radius:5px; margin-bottom:20px;">
        <p style="color:#0D47A1; margin:0; font-size:14px;">
            <strong>Current Date and Time:</strong> {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} &nbsp;&nbsp;|&nbsp;&nbsp;
            <strong>Logged in as:</strong> {st.session_state.username}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Period selection
    period = st.selectbox("Select Period", ["Today", "Last 7 Days", "Last 30 Days", "Custom Range"])
    today = datetime.datetime.now().date()
    start_date, end_date = today, today
    if period == "Today":
        start_date, end_date = today, today
    elif period == "Last 7 Days":
        start_date = today - datetime.timedelta(days=6)
        end_date = today
    elif period == "Last 30 Days":
        start_date = today - datetime.timedelta(days=29)
        end_date = today
    elif period == "Custom Range":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=today - datetime.timedelta(days=6))
        with col2:
            end_date = st.date_input("End Date", value=today)

    # Fetch attendance data
    attendance_data = get_attendance_data(db)
    # Filter by selected period using actual record dates
    filtered_data = []
    for record in attendance_data:
        record_date = record.get('date')
        if record_date:
            try:
                rec_date = datetime.datetime.strptime(record_date, '%Y-%m-%d').date()
                if start_date <= rec_date <= end_date:
                    filtered_data.append(record)
            except Exception:
                continue

    # If viewing 'Today', show punctuality-focused metrics and chart
    if period == "Today":
        st.markdown("#### Staff Present Today")
        today_staff = {}
        for record in filtered_data:
            name = record.get("name", "")
            ts = record.get("timestamp", "-")
            if name and ts:
                # Only keep earliest check-in per staff
                if name not in today_staff or ts < today_staff[name]:
                    today_staff[name] = ts
        staff_today = [
            {"Name": name, "Check-in Time": ts}
            for name, ts in sorted(today_staff.items(), key=lambda x: x[1])
        ]
        st.metric("Number of Staff Present Today", len(staff_today))
        # Chart: Staff Check-in Times
        if staff_today:
            chart_df = pd.DataFrame(staff_today)
            def to_hour_minute(ts):
                t = parse_firestore_timestamp(ts)
                if t:
                    return t.hour + t.minute/60
                return None
            chart_df['Check-in Hour'] = chart_df['Check-in Time'].apply(to_hour_minute)
            st.bar_chart(chart_df.set_index('Name')['Check-in Hour'])
        df_today = pd.DataFrame(staff_today, columns=["Name", "Check-in Time"])
        if not df_today.empty:
            st.dataframe(df_today.style.hide(axis='index'), use_container_width=True)
        else:
            st.info("No staff have checked in today.")
        st.stop()  # Skip rest of dashboard for 'Today' view

    # Calculate check-in times robustly
    checkin_times = []
    checkin_records = []
    for record in filtered_data:
        ts = record.get('timestamp')
        name = record.get('name', '-')
        t = parse_firestore_timestamp(ts)
        if t:
            checkin_times.append(t.time())
            checkin_records.append((name, t.time()))
    total_checkins = len(checkin_times)
    days_in_period = (end_date - start_date).days + 1
    avg_checkins_per_day = total_checkins / days_in_period if days_in_period > 0 else 0
    if checkin_times:
        avg_seconds = sum([t.hour*3600 + t.minute*60 + t.second for t in checkin_times]) / len(checkin_times)
        avg_hour = int(avg_seconds // 3600)
        avg_minute = int((avg_seconds % 3600) // 60)
        avg_second = int(avg_seconds % 60)
        avg_checkin_time = f"{avg_hour:02d}:{avg_minute:02d}:{avg_second:02d}"
        earliest = min(checkin_records, key=lambda x: x[1])
        latest = max(checkin_records, key=lambda x: x[1])
        earliest_str = earliest[0]
        latest_str = latest[0]
    else:
        avg_checkin_time = "-"
        earliest_str = "-"
        latest_str = "-"

    # KPI metrics 
    st.markdown("<style>.big-metric {font-size: 2.2rem !important; font-weight: 700; color: #1565C0;} .section-header {font-size: 1.5rem !important; font-weight: 700; color: #1565C0; margin-top: 2rem;}</style>", unsafe_allow_html=True)
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns([1,1,1,1,1])
    kpi1.markdown(f'<div class="big-metric">{total_checkins}</div><div>Total Check-ins</div>', unsafe_allow_html=True)
    kpi2.markdown(f'<div class="big-metric">{avg_checkins_per_day:.2f}</div><div>Avg Check-ins per Day</div>', unsafe_allow_html=True)
    kpi3.markdown(f'<div class="big-metric">{avg_checkin_time}</div><div>Average Check-in Time</div>', unsafe_allow_html=True)
    kpi4.markdown(f'<div class="big-metric">{earliest_str}</div><div>Earliest Check-in</div>', unsafe_allow_html=True)
    kpi5.markdown(f'<div class="big-metric">{latest_str}</div><div>Latest Check-in</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">Check-in Time Distribution</div>', unsafe_allow_html=True)
    chart_row1, chart_row2 = st.columns([2,2])
    with chart_row1:
        if len(checkin_times) > 0:
            checkin_hours = [t.hour + t.minute/60 for t in checkin_times if t]
            fig, ax = plt.subplots(figsize=(8,4))
            ax.hist(checkin_hours, bins=range(6, 20), color="#1565C0", edgecolor="white")
            ax.set_xlabel("Check-in Hour", fontsize=13)
            ax.set_ylabel("Number of Check-ins", fontsize=13)
            ax.set_title("Check-in Time Distribution", fontsize=15)
            st.pyplot(fig)
        else:
            st.info("No check-in time data available for chart.")
    with chart_row2:
        st.markdown('<div class="section-header">Daily Check-ins Trend</div>', unsafe_allow_html=True)
        date_counts = pd.Series([record.get('date', '') for record in filtered_data]).value_counts().sort_index().reset_index()
        date_counts.columns = ['Date', 'Check-ins']
        if not date_counts.empty:
            st.line_chart(date_counts.set_index('Date'))
        else:
            st.info("No trend data available.")

def check_in_out():
    st.title("Check In / Check Out")
    
    # FIXED DATE DISPLAY
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.write(f"Current Date and Time: {current_time}")
    
    staff_list = get_staff_list(db)
    
    if staff_list:
        selected_staff = st.selectbox("Select Staff Member", [staff["name"] for staff in staff_list])
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Mark Check In"):
                register_attendance(db, selected_staff, "check_in", datetime.datetime.now())
                st.success(f"Marked {selected_staff} as checked in at {datetime.datetime.now().strftime('%H:%M:%S')}")
        with col2:
            if st.button("Mark Check Out"):
                register_attendance(db, selected_staff, "check_out", datetime.datetime.now())
                st.success(f"Marked {selected_staff} as checked out at {datetime.datetime.now().strftime('%H:%M:%S')}")
    else:
        st.warning("No staff members found in the database")
        if st.button("Add Sample Staff"):
            st.info("This would add sample staff data to the database")

def staff_management():
    st.title("Staff Management")
    
    tab1, tab2, tab3 = st.tabs(["View Staff", "Add Staff", "Remove Staff"])
    
    with tab1:
        st.subheader("Staff List")
        staff_list = get_staff_list(db)
        if staff_list:
            staff_df = pd.DataFrame(staff_list)
            st.dataframe(staff_df)
        else:
            st.info("No staff members found")
    
    with tab2:
        st.subheader("Add Staff")
        with st.form("add_staff_form"):
            name = st.text_input("Full Name")
            position = st.text_input("Position")
            department = st.selectbox("Department", ["IT", "HR", "Finance", "Marketing", "Operations", "Other"])
            email = st.text_input("Email")
            phone = st.text_input("Phone Number")
            
            if st.form_submit_button("Add Staff Member"):
                if name:
                    try:
                        db.collection('staff').add({
                            "name": name,
                            "position": position,
                            "department": department,
                            "email": email,
                            "phone": phone,
                            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        st.success(f"Added staff member: {name}")
                    except Exception as e:
                        st.error(f"Error adding staff: {str(e)}")
                else:
                    st.error("Name is required")
    
    with tab3:
        st.subheader("Remove Staff")
        staff_list = get_staff_list(db)
        if staff_list:
            selected_staff = st.selectbox("Select Staff to Remove", [staff["name"] for staff in staff_list])
            if st.button("Remove Staff", key="remove_staff_btn"):
                try:
                    # Find staff document
                    staff_ref = db.collection('staff')
                    query = staff_ref.where('name', '==', selected_staff).limit(1)
                    results = query.get()
                    
                    if len(results) > 0:
                        doc_id = results[0].id
                        staff_ref.document(doc_id).delete()
                        st.success(f"Removed staff member: {selected_staff}")
                        st.experimental_rerun()
                    else:
                        st.error("Staff member not found")
                except Exception as e:
                    st.error(f"Error removing staff: {str(e)}")
        else:
            st.info("No staff members to remove")

def reports():
    st.title("Reports")
    st.markdown("#### Flexible Attendance Reporting")
    staff_list = get_staff_list(db)
    staff_names = [s.get('name', '-') for s in staff_list]
    selected_staff = st.selectbox("Select Staff Member", ["All Staff"] + staff_names)
    # Date range selection as dropdown
    date_option = st.selectbox("Select Period", ["Today", "Last 7 Days", "Last 30 Days", "Custom Range"])
    today = datetime.datetime.now().date()
    if date_option == "Today":
        start_date, end_date = today, today
    elif date_option == "Last 7 Days":
        start_date = today - datetime.timedelta(days=6)
        end_date = today
    elif date_option == "Last 30 Days":
        start_date = today - datetime.timedelta(days=29)
        end_date = today
    elif date_option == "Custom Range":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=today - datetime.timedelta(days=6))
        with col2:
            end_date = st.date_input("End Date", value=today)
    if st.button("Generate Report"):
        st.info("Generating report...")
        attendance_data = get_attendance_data(db)
        filtered_data = []
        for record in attendance_data:
            record_date = record.get('date')
            if record_date:
                try:
                    rec_date = datetime.datetime.strptime(record_date, '%Y-%m-%d').date()
                    if start_date <= rec_date <= end_date:
                        if selected_staff == "All Staff" or record.get('name') == selected_staff:
                            filtered_data.append(record)
                except Exception:
                    continue
        # Table: enforce column order, fill missing columns, hide index, and set fixed width
        if filtered_data:
            df = pd.DataFrame(filtered_data)
            columns = ["name", "nfc_uid", "date", "device_id", "department", "user_id", "timestamp", "action", "id"]
            for col in columns:
                if col not in df.columns:
                    df[col] = ""
            df = df[columns]
            # Truncate long text in all columns to 30 chars
            for col in columns:
                df[col] = df[col].apply(lambda x: str(x)[:30] if pd.notnull(x) else "")
            # Limit to first 100 rows for stability
            df = df.head(100)
            # Add extra CSS for fixed table layout
            st.markdown("""
            <style>
            .stDataFrame table { table-layout: fixed; }
            .stDataFrame th, .stDataFrame td { min-width: 120px !important; max-width: 120px !important; overflow: hidden; text-overflow: ellipsis; }
            </style>
            """, unsafe_allow_html=True)
            styled_df = df.style.hide(axis='index').set_properties(**{'font-size': '14px'})
            st.dataframe(styled_df, use_container_width=True, height=500)
        else:
            st.info("No attendance records found for selected period.")
        st.download_button("Download Report (CSV)", pd.DataFrame(filtered_data).to_csv(index=False), file_name="attendance_report.csv")
def settings():
    st.title("System Settings")
    
    tab1, tab2 = st.tabs(["General Settings", "Database Settings"])
    
    with tab1:
        st.subheader("General Settings")
        
        with st.form("general_settings"):
            company_name = st.text_input("Company Name", value="Your Company")
            working_hours_start = st.time_input("Working Hours Start", datetime.time(9, 0))
            working_hours_end = st.time_input("Working Hours End", datetime.time(17, 0))
            
            if st.form_submit_button("Save Settings"):
                st.success("Settings saved successfully")
    
    with tab2:
        st.subheader("Database Connection")
        st.info("Configure Firestore database connection")
        
        # Add test connection button
        if st.button("Test Database Connection"):
            try:
                test_ref = db.collection('test').document('connection')
                test_ref.set({
                    'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'status': 'success'
                })
                st.success("Database connection successful!")
            except Exception as e:
                st.error(f"Database connection failed: {str(e)}")

def parse_firestore_timestamp(ts):
    """Robustly parse Firestore timestamp field to datetime object."""
    import datetime
    from dateutil import parser
    if ts is None:
        return None
    # Firestore native timestamp dict
    if isinstance(ts, dict) and '_seconds' in ts:
        try:
            return datetime.datetime.fromtimestamp(ts['_seconds'])
        except Exception:
            return None
    # Python datetime object
    if isinstance(ts, datetime.datetime):
        return ts
    # String: try ISO, then time-only
    if isinstance(ts, str):
        try:
            return parser.parse(ts)
        except Exception:
            try:
                return datetime.datetime.strptime(ts, '%H:%M:%S')
            except Exception:
                return None
    return None

def main():
    # Only check authentication and show dashboard, do not check for MockFirestore or show mock data
    if not st.session_state.authenticated:
        login_page()
    else:
        st.sidebar.title("Navigation")
        page = st.sidebar.radio(
            "Go to",
            ["Dashboard", "Staff Management", "Reports", "Settings"],
        )
        st.sidebar.markdown(f"Logged in as: **{st.session_state.username}**")
        st.sidebar.markdown("---")
        if st.sidebar.button("Logout"):
            logout()
        if page == "Dashboard":
            display_dashboard()
        elif page == "Staff Management":
            staff_management()
        elif page == "Reports":
            reports()
        elif page == "Settings":
            settings()

if __name__ == "__main__":
    main()