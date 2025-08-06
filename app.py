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
            if username and password:                # Firebase authentication
                user_role = check_user_credentials(db, username, password)
                if user_role:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.user_role = user_role
                    # Instead of experimental_rerun, use success message and JavaScript to reload
                    st.success("Login successful! Redirecting to dashboard...")
                    st.markdown(
                        """
                        <script>
                        // Add a small delay before reloading to show the success message
                        setTimeout(function() {
                            window.location.reload();
                        }, 1000);
                        </script>
                        """,
                        unsafe_allow_html=True
                    )
                    # Return early to avoid showing login form again
                    return
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
    # Instead of experimental_rerun, use JavaScript to reload
    st.markdown(
        """
        <script>
        // Add a small delay before reloading
        setTimeout(function() {
            window.location.reload();
        }, 500);
        </script>
        """,
        unsafe_allow_html=True
    )

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
                continue    # If viewing 'Today', show modern staff attendance table
    if period == "Today":
        st.markdown("### Today's Attendance Record")
        
        # Add search and filter controls in a row
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            search = st.text_input("", placeholder="Search staff...", key="staff_search")
        with col2:
            department_filter = st.selectbox("", ["All...", "Teaching", "Admin", "Support", "IT"], key="dept_filter")
        with col3:
            status_filter = st.selectbox("", ["All Status", "Present", "Late", "Absent"], key="status_filter")
            
        # Create a button for exporting data
        st.button("Export", key="export_btn", type="primary", help="Export attendance data to CSV")
        
        # Process attendance data for display
        staff_records = []
        for record in filtered_data:
            name = record.get("name", "")
            department = record.get("department", "")
            role = record.get("role", "")
            check_in = record.get("check_in")
            check_out = record.get("check_out")
            status = record.get("status", "Absent")
            
            # Calculate attendance percentage (example: based on total working days)
            attendance_pct = record.get("attendance_percentage", 95)
            
            if name:  # Only add if we have a name
                staff_records.append({
                    "Name": name,
                    "Department": department,
                    "Role": role,
                    "Status": status,
                    "Check In": check_in if check_in else "-",
                    "Check Out": check_out if check_out else "-",
                    "Attendance %": f"{attendance_pct}%"
                })
        
        # Apply search and filters
        if search:
            staff_records = [r for r in staff_records if search.lower() in r["Name"].lower()]
        if department_filter != "All...":
            staff_records = [r for r in staff_records if r["Department"] == department_filter]
        if status_filter != "All Status":
            staff_records = [r for r in staff_records if r["Status"] == status_filter]
            
        # Create custom CSS for the table
        st.markdown("""
        <style>
        .staff-table {
            border-collapse: collapse;
            margin: 20px 0;
            width: 100%;
            border-radius: 5px;
            overflow: hidden;
            box-shadow: 0 0 10px rgba(0,0,0,0.05);
        }
        .staff-table thead {
            background-color: #f5f7f9;
        }
        .staff-table th {
            padding: 12px 15px;
            text-align: left;
            font-size: 14px;
            color: #333;
        }
        .staff-table td {
            padding: 12px 15px;
            font-size: 14px;
            color: #333;
            border-bottom: 1px solid #f0f0f0;
        }
        .status-present {
            background-color: #4CAF50;
            color: white;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 12px;
        }
        .status-late {
            background-color: #FF9800;
            color: white;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 12px;
        }
        .status-absent {
            background-color: #F44336;
            color: white;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 12px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Display the table
        if staff_records:
            # Convert to DataFrame for display
            df = pd.DataFrame(staff_records)
            
            # Add status badges
            def format_status(status):
                status_lower = status.lower()
                if status_lower == 'present':
                    return f'<span class="status-present">{status}</span>'
                elif status_lower == 'late':
                    return f'<span class="status-late">{status}</span>'
                elif status_lower == 'absent':
                    return f'<span class="status-absent">{status}</span>'
                return status
            
            # Apply formatting
            df_styled = df.style.format({
                'Status': lambda x: format_status(x)
            }).hide(axis='index').set_properties(**{
                'font-size': '14px',
                'text-align': 'left'
            })
            
            st.write(df_styled.to_html(escape=False), unsafe_allow_html=True)
        else:
            st.info("No staff attendance records found for today.")
            
            # Add sample data for demonstration if no records
            if st.button("Show Sample Data"):
                sample_data = [
                    {"Name": "Sarah Johnson", "Department": "Teaching", "Role": "Math Teacher", 
                     "Status": "Present", "Check In": "08:15 AM", "Check Out": "04:30 PM", "Attendance %": "96%"},
                    {"Name": "Michael Chen", "Department": "Teaching", "Role": "Science Teacher", 
                     "Status": "Late", "Check In": "08:45 AM", "Check Out": "-", "Attendance %": "89%"},
                    {"Name": "Emily Davis", "Department": "Admin", "Role": "Principal", 
                     "Status": "Present", "Check In": "07:30 AM", "Check Out": "05:15 PM", "Attendance %": "98%"},
                    {"Name": "Robert Wilson", "Department": "Support", "Role": "IT Support", 
                     "Status": "Absent", "Check In": "-", "Check Out": "-", "Attendance %": "92%"},
                    {"Name": "Lisa Martinez", "Department": "Teaching", "Role": "English Teacher", 
                     "Status": "Present", "Check In": "08:10 AM", "Check Out": "04:45 PM", "Attendance %": "94%"}
                ]
                df = pd.DataFrame(sample_data)
                df_styled = df.style.format({
                    'Status': lambda x: format_status(x)
                }).hide(axis='index').set_properties(**{
                    'font-size': '14px',
                    'text-align': 'left'
                })
                st.write(df_styled.to_html(escape=False), unsafe_allow_html=True)
        
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
                        # Use JavaScript to reload the page instead of experimental_rerun
                        st.markdown(
                            """
                            <script>
                            setTimeout(function() {
                                window.location.reload();
                            }, 1000);
                            </script>
                            """,
                            unsafe_allow_html=True
                        )
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
    # Only check authentication and show dashboard
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