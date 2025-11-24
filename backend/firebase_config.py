"""
Firebase Configuration
Handles initialization of Firebase Admin SDK and Firestore database connection.
Note: Firebase is set up but not actively used in the MVP. It's ready for future features like caching.
"""

import firebase_admin
from firebase_admin import credentials, firestore
import os

def init_firebase():
    """
    Initialize Firebase Admin SDK using service account file.
    
    This function sets up the connection to Firebase/Firestore for potential future use cases:
    - Caching artist recommendations
    - Storing user preferences
    - Analytics and usage tracking
    
    Expects a service account JSON file at 'serviceAccountKey.json' in the backend directory.
    You can download this from Firebase Console > Project Settings > Service Accounts.
    
    Returns:
        Firestore client instance if successful, None otherwise
    """
    # Check if Firebase has already been initialized (prevents re-initialization errors)
    if not firebase_admin._apps:
        # Build path to service account key file in the same directory as this script
        service_account_path = os.path.join(os.path.dirname(__file__), 'serviceAccountKey.json')
        
        # Check if the service account file exists
        if os.path.exists(service_account_path):
            # Load credentials from the service account JSON file
            cred = credentials.Certificate(service_account_path)
            # Initialize Firebase Admin with these credentials
            firebase_admin.initialize_app(cred)
        else:
            # Fallback: Try to use default credentials (useful for cloud deployments)
            # This allows flexibility during development if service account isn't set up yet
            try:
                firebase_admin.initialize_app()
            except Exception as e:
                # If initialization fails, print warning but don't crash the app
                # The app can still function without Firebase (it's optional for MVP)
                print(f"Warning: Could not initialize Firebase. Error: {e}")
                print(f"Please ensure serviceAccountKey.json exists in the backend directory")
                return None
    
    # Return Firestore client for database operations
    return firestore.client()

def get_db():
    """
    Get Firestore database client instance.
    
    This is a convenience function that initializes Firebase if needed
    and returns a Firestore client for database operations.
    
    Returns:
        Firestore client instance if successful, None if initialization failed
    """
    try:
        return init_firebase()
    except Exception as e:
        # Log error but don't crash - Firebase is optional for MVP
        print(f"Error getting Firestore client: {e}")
        return None

