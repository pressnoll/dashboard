import pandas as pd
import datetime
import plotly.express as px
import streamlit as st

def format_time(timestamp):
    """Format a Firebase timestamp to readable time"""
    if timestamp:
        try:
            if isinstance(timestamp, datetime.datetime):
                return timestamp.strftime('%H:%M:%S')
            else:
                return timestamp.ToDatetime().strftime('%H:%M:%S')
        except:
            return "N/A"
    return "N/A"

def format_date(timestamp):
    """Format a Firebase timestamp to readable date"""
    if timestamp:
        try:
            if isinstance(timestamp, datetime.datetime):
                return timestamp.strftime('%Y-%m-%d')
            else:
                return timestamp.ToDatetime().strftime('%Y-%m-%d')
        except:
            return "N/A"
    return "N/A"

def calculate_hours(check_in, check_out):
    """Calculate hours worked between check-in and check-out"""
    if not check_in or not check_out:
        return 0
        
    try:
        if not isinstance(check_in, datetime.datetime):
            check_in = check_in.ToDatetime()
        if not isinstance(check_out, datetime.datetime):
            check_out = check_out.ToDatetime()
            
        diff = check_out - check_in
        return round(diff.total_seconds() / 3600, 2)  # Hours with 2 decimal places
    except:
        return 0

def generate_attendance_summary(df):
    """Generate attendance summary statistics"""
    if df.empty:
        return None, None, None
        
    # Make sure check_in and check_out are datetime objects
    df['check_in_dt'] = pd.to_datetime(df['check_in'], errors='coerce')
    df['check_out_dt'] = pd.to_datetime(df['check_out'], errors='coerce')
    
    # Calculate hours for each row
    df['hours'] = df.apply(lambda row: calculate_hours(row['check_in_dt'], row['check_out_dt']), axis=1)
    
    # Prepare summary by staff
    staff_summary = df.groupby(['staff_name', 'department']).agg(
        total_days=pd.NamedAgg(column='date', aggfunc='nunique'),
        avg_hours=pd.NamedAgg(column='hours', aggfunc='mean'),
        total_hours=pd.NamedAgg(column='hours', aggfunc='sum')
    ).reset_index()
    
    # Prepare summary by date
    date_summary = df.groupby('date').agg(
        staff_count=pd.NamedAgg(column='staff_id', aggfunc='nunique'),
        avg_hours=pd.NamedAgg(column='hours', aggfunc='mean')
    ).reset_index()
    
    # Prepare department summary
    dept_summary = df.groupby('department').agg(
        staff_count=pd.NamedAgg(column='staff_id', aggfunc='nunique'),
        avg_hours=pd.NamedAgg(column='hours', aggfunc='mean'),
        total_hours=pd.NamedAgg(column='hours', aggfunc='sum')
    ).reset_index()
    
    return staff_summary, date_summary, dept_summary

def plot_attendance_over_time(date_summary):
    """Create a line chart for attendance over time"""
    if date_summary is None or date_summary.empty:
        return None
        
    fig = px.line(
        date_summary, 
        x='date', 
        y='staff_count',
        title='Daily Attendance Count',
        labels={'staff_count': 'Number of Staff', 'date': 'Date'}
    )
    return fig

def plot_department_attendance(dept_summary):
    """Create a bar chart for department attendance"""
    if dept_summary is None or dept_summary.empty:
        return None
        
    fig = px.bar(
        dept_summary, 
        x='department', 
        y='staff_count',
        title='Attendance by Department',
        color='department',
        labels={'staff_count': 'Number of Staff', 'department': 'Department'}
    )
    return fig

def plot_hours_by_department(dept_summary):
    """Create a bar chart for hours worked by department"""
    if dept_summary is None or dept_summary.empty:
        return None
        
    fig = px.bar(
        dept_summary, 
        x='department', 
        y='total_hours',
        title='Total Hours by Department',
        color='department',
        labels={'total_hours': 'Total Hours', 'department': 'Department'}
    )
    return fig