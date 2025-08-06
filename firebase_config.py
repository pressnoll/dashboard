import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
import streamlit as st

def initialize_firebase():
    """Initialize Firebase with service account credentials"""
    # First, check if we already have our named app
    try:
        existing_app = firebase_admin.get_app('staff-attendance')
        # If we get here, the app already exists, so we can use it
    except ValueError:
        # App doesn't exist, so we need to initialize it
        try:
            # Path to service account key file
            service_account_path = "serviceAccountKey.json"
            # If file exists, use it
            if os.path.exists(service_account_path):
                cred = credentials.Certificate(service_account_path)
                # Check if default app exists
                try:
                    default_app = firebase_admin.get_app()
                    # Default app exists, so use a named app
                    firebase_admin.initialize_app(cred, name='staff-attendance')
                except ValueError:
                    # No default app, initialize with a name to avoid future conflicts
                    firebase_admin.initialize_app(cred, name='staff-attendance')
            else:                # For Streamlit Cloud or when file doesn't exist
                # Try to use environment variables or secrets
                if 'FIREBASE_SERVICE_ACCOUNT' in st.secrets:
                    import json
                    try:
                        # Try to parse as JSON
                        service_account_info = json.loads(st.secrets["FIREBASE_SERVICE_ACCOUNT"])
                        
                        # Special handling for private_key to fix PEM format issues
                        if 'private_key' in service_account_info:
                            # Replace escaped newlines with actual newlines
                            service_account_info['private_key'] = service_account_info['private_key'].replace('\\n', '\n')
                        
                        cred = credentials.Certificate(service_account_info)
                        # Check if default app exists
                        try:
                            default_app = firebase_admin.get_app()
                            # Default app exists, so use a named app
                            firebase_admin.initialize_app(cred, name='staff-attendance')
                        except ValueError:
                            # No default app, initialize with a name to avoid future conflicts
                            firebase_admin.initialize_app(cred, name='staff-attendance')
                    except json.JSONDecodeError:
                        # If not valid JSON, try to handle it as a string with manual newline replacement
                        st.error("Failed to parse Firebase credentials as JSON. Please check format.")
                        raise Exception("Invalid Firebase credentials format")
                else:
                    st.error("Firebase credentials not found. Please check setup.")
                    raise Exception("Firebase credentials not found")
        except Exception as e:
            st.error(f"Failed to initialize Firebase: {e}")
            raise Exception(f"Firebase initialization failed: {str(e)}")
    
    # Get Firestore database from our named app
    try:
        db = firestore.client(app=firebase_admin.get_app('staff-attendance'))
        return db
    except Exception as e:
        st.error(f"Failed to get Firestore client: {e}")
        raise Exception(f"Failed to get Firestore client: {str(e)}")

# The MockFirestore implementation has been removed.
# Only real Firebase connections will be used now.