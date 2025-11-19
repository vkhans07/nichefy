import firebase_admin
from firebase_admin import credentials, firestore
import os

# Initialize Firebase Admin
def init_firebase():
    """
    Initialize Firebase Admin SDK using service account file.
    Expects a service account JSON file at 'serviceAccountKey.json'
    """
    if not firebase_admin._apps:
        # Check if service account file exists
        service_account_path = os.path.join(os.path.dirname(__file__), 'serviceAccountKey.json')
        
        if os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
        else:
            # For development, you can also use environment variable or default credentials
            # This allows flexibility during development
            try:
                firebase_admin.initialize_app()
            except Exception as e:
                print(f"Warning: Could not initialize Firebase. Error: {e}")
                print(f"Please ensure serviceAccountKey.json exists in the backend directory")
                return None
    
    return firestore.client()

# Get Firestore client
def get_db():
    """Get Firestore database client"""
    try:
        return init_firebase()
    except Exception as e:
        print(f"Error getting Firestore client: {e}")
        return None

