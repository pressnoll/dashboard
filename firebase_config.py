import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
import streamlit as st

def initialize_firebase():
    """Initialize Firebase with service account credentials"""
    # Check if already initialized
    if not firebase_admin._apps:
        try:
            # Path to service account key file
            service_account_path = "serviceAccountKey.json"
            # If file exists, use it
            if os.path.exists(service_account_path):
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred)
            else:
                # For Streamlit Cloud or when file doesn't exist
                # Try to use environment variables or secrets
                if 'FIREBASE_SERVICE_ACCOUNT' in st.secrets:
                    import json
                    service_account_info = json.loads(st.secrets["FIREBASE_SERVICE_ACCOUNT"])
                    cred = credentials.Certificate(service_account_info)
                    firebase_admin.initialize_app(cred)
                else:
                    st.error("Firebase credentials not found. Please check setup.")
                    # For development, create a mock database
                    return MockFirestore()
        except Exception as e:
            st.error(f"Failed to initialize Firebase: {e}")
            return MockFirestore()
    # If already initialized, do not re-initialize
    # Get Firestore database
    try:
        db = firestore.client()
        return db
    except Exception as e:
        st.error(f"Failed to get Firestore client: {e}")
        return MockFirestore()

# Mock Firestore class for development when Firebase is not available
class MockFirestore:
    """Mock Firestore client for development"""
    
    def __init__(self):
        self.collections = {
            'users': [
                {'username': 'admin', 'password': 'admin123', 'role': 'admin'},
                {'username': 'staff', 'password': 'staff123', 'role': 'staff'}
            ],
            'staff': [
                {'name': 'John Doe', 'position': 'Developer', 'department': 'IT', 'email': 'john@example.com', 'phone': '1234567890'},
                {'name': 'Jane Smith', 'position': 'HR Manager', 'department': 'HR', 'email': 'jane@example.com', 'phone': '0987654321'},
                {'name': 'Mike Johnson', 'position': 'Accountant', 'department': 'Finance', 'email': 'mike@example.com', 'phone': '5555555555'}
            ],
            'attendance': [
                {'staff_name': 'John Doe', 'date': '2023-08-10', 'check_in': '08:30:00', 'check_out': '17:15:00', 'status': 'present'},
                {'staff_name': 'Jane Smith', 'date': '2023-08-10', 'check_in': '08:45:00', 'check_out': '17:30:00', 'status': 'present'},
                {'staff_name': 'Mike Johnson', 'date': '2023-08-10', 'check_in': None, 'check_out': None, 'status': 'absent'}
            ]
        }
    
    def collection(self, collection_name):
        return MockCollection(self, collection_name)

class MockCollection:
    """Mock collection for development"""
    
    def __init__(self, db, collection_name):
        self.db = db
        self.collection_name = collection_name
    
    def get(self):
        """Return mock documents"""
        return [MockDocument(i, doc) for i, doc in enumerate(self.db.collections.get(self.collection_name, []))]
    
    def add(self, data):
        """Add mock document"""
        if self.collection_name not in self.db.collections:
            self.db.collections[self.collection_name] = []
        self.db.collections[self.collection_name].append(data)
        return "mock-doc-id"
    
    def document(self, doc_id):
        """Get mock document by ID"""
        return MockDocumentRef(self.db, self.collection_name, int(doc_id) if doc_id.isdigit() else 0)
    
    def where(self, field, op, value):
        """Mock query"""
        return MockQuery(self.db, self.collection_name, field, op, value)

class MockDocument:
    """Mock document for development"""
    
    def __init__(self, doc_id, data):
        self.id = str(doc_id)
        self.data = data
    
    def to_dict(self):
        """Return document data"""
        return self.data

class MockDocumentRef:
    """Mock document reference for development"""
    
    def __init__(self, db, collection_name, doc_id):
        self.db = db
        self.collection_name = collection_name
        self.doc_id = doc_id
    
    def set(self, data):
        """Set document data"""
        if self.collection_name not in self.db.collections:
            self.db.collections[self.collection_name] = []
        
        if self.doc_id < len(self.db.collections[self.collection_name]):
            self.db.collections[self.collection_name][self.doc_id] = data
        else:
            self.db.collections[self.collection_name].append(data)
    
    def update(self, data):
        """Update document data"""
        if self.collection_name in self.db.collections and self.doc_id < len(self.db.collections[self.collection_name]):
            self.db.collections[self.collection_name][self.doc_id].update(data)
    
    def delete(self):
        """Delete document"""
        if self.collection_name in self.db.collections and self.doc_id < len(self.db.collections[self.collection_name]):
            self.db.collections[self.collection_name].pop(self.doc_id)

class MockQuery:
    """Mock query for development"""
    
    def __init__(self, db, collection_name, field, op, value):
        self.db = db
        self.collection_name = collection_name
        self.field = field
        self.op = op
        self.value = value
        self.limit_val = None
    
    def limit(self, limit_val):
        """Set query limit"""
        self.limit_val = limit_val
        return self
    
    def get(self):
        """Execute query and return results"""
        results = []
        
        if self.collection_name not in self.db.collections:
            return []
        
        for i, doc in enumerate(self.db.collections[self.collection_name]):
            if self.field in doc:
                if (self.op == '==' and doc[self.field] == self.value) or \
                   (self.op == '>' and doc[self.field] > self.value) or \
                   (self.op == '<' and doc[self.field] < self.value) or \
                   (self.op == '>=' and doc[self.field] >= self.value) or \
                   (self.op == '<=' and doc[self.field] <= self.value):
                    results.append(MockDocument(i, doc))
            
            if self.limit_val is not None and len(results) >= self.limit_val:
                break
        
        return results