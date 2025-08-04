from datetime import datetime
import firebase_admin
from firebase_admin import firestore
import streamlit as st

def check_user_credentials(db, username, password):
    """Verify user credentials and return role if valid"""
    users_ref = db.collection('users')
    query = users_ref.where('username', '==', username).where('password', '==', password).limit(1)
    results = query.get()
    
    if len(results) > 0:
        user_data = results[0].to_dict()
        return user_data.get('role', 'staff')  # Return role or default to 'staff'
    return None

def register_attendance(db, staff_name, action_type, timestamp):
    """Register check-in or check-out"""
    attendance_ref = db.collection('attendance')
    
    # Format for Firestore document ID
    date_str = timestamp.strftime('%Y-%m-%d')
    
    # Check if there's an existing record for today
    query = attendance_ref.where('staff_name', '==', staff_name).where('date', '==', date_str).limit(1)
    results = query.get()
    
    if action_type == "check_in":
        if len(results) == 0:
            # New attendance record
            attendance_ref.add({
                'staff_name': staff_name,
                'date': date_str,
                'check_in': timestamp.strftime('%H:%M:%S'),
                'check_out': None,
                'status': 'present'
            })
        else:
            # Update existing record
            doc_id = results[0].id
            attendance_ref.document(doc_id).update({
                'check_in': timestamp.strftime('%H:%M:%S'),
                'status': 'present'
            })
    elif action_type == "check_out":
        if len(results) > 0:
            # Update existing record
            doc_id = results[0].id
            attendance_ref.document(doc_id).update({
                'check_out': timestamp.strftime('%H:%M:%S')
            })
        else:
            # Unusual case: Check-out without check-in
            attendance_ref.add({
                'staff_name': staff_name,
                'date': date_str,
                'check_in': None,
                'check_out': timestamp.strftime('%H:%M:%S'),
                'status': 'present'
            })
    
    return True

def get_staff_list(db):
    """Get list of all staff members"""
    staff_ref = db.collection('staff')
    staff_docs = staff_ref.get()
    
    staff_list = []
    for doc in staff_docs:
        staff_data = doc.to_dict()
        staff_data['id'] = doc.id  # Add document ID
        staff_list.append(staff_data)
    
    return staff_list

def add_staff_member(db, staff_data):
    """Add a new staff member"""
    staff_ref = db.collection('staff')
    staff_ref.add(staff_data)
    return True

def update_staff_member(db, staff_name, staff_data):
    """Update existing staff member"""
    staff_ref = db.collection('staff')
    query = staff_ref.where('name', '==', staff_name).limit(1)
    results = query.get()
    
    if len(results) > 0:
        doc_id = results[0].id
        staff_ref.document(doc_id).update(staff_data)
        return True
    return False

def delete_staff_member(db, staff_name):
    """Delete staff member"""
    staff_ref = db.collection('staff')
    query = staff_ref.where('name', '==', staff_name).limit(1)
    results = query.get()
    
    if len(results) > 0:
        doc_id = results[0].id
        staff_ref.document(doc_id).delete()
        return True
    return False

def get_staff_details(db, staff_name):
    """Get details of a specific staff member"""
    staff_ref = db.collection('staff')
    query = staff_ref.where('name', '==', staff_name).limit(1)
    results = query.get()
    
    if len(results) > 0:
        return results[0].to_dict()
    return {}

def get_attendance_records(db, start_date=None, end_date=None, staff_name=None):
    """Get attendance records with optional filters"""
    attendance_ref = db.collection('attendance')
    
    # Start with base query
    query = attendance_ref
    
    # Apply filters if provided
    if staff_name and staff_name != "All Staff":
        query = query.where('staff_name', '==', staff_name)
    
    if start_date:
        start_date_str = start_date.strftime('%Y-%m-%d')
        query = query.where('date', '>=', start_date_str)
    
    if end_date:
        end_date_str = end_date.strftime('%Y-%m-%d')
        query = query.where('date', '<=', end_date_str)
    
    # Execute query
    results = query.get()
    
    # Format results
    attendance_records = []
    for doc in results:
        record = doc.to_dict()
        record['id'] = doc.id
        attendance_records.append(record)
    
    return attendance_records

def create_default_users(db):
    """Create default admin and staff users if they don't exist"""
    users_ref = db.collection('users')
    
    # Check if admin exists
    admin_query = users_ref.where('username', '==', 'admin').limit(1)
    if len(admin_query.get()) == 0:
        users_ref.add({
            'username': 'admin',
            'password': 'admin123',
            'role': 'admin'
        })
    
    # Check if staff exists
    staff_query = users_ref.where('username', '==', 'staff').limit(1)
    if len(staff_query.get()) == 0:
        users_ref.add({
            'username': 'staff',
            'password': 'staff123',
            'role': 'staff'
        })