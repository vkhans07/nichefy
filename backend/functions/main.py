"""
Flask Backend API for Nichefy
Main application file that handles HTTP requests and serves the niche artist recommendation API.
"""

# Flask: Web framework for creating the REST API
from flask import Flask, request, jsonify, session, redirect, Response, stream_with_context
# CORS: Allows frontend (running on different port) to make requests to this backend
from flask_cors import CORS
# Import our custom function that finds niche artists using recursive algorithm
from niche_logic import find_niche_cousins, recommend_niche_for_top_artists
# Spotipy: Spotify Web API client library (imported but not directly used here)
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import json
import time
from dotenv import load_dotenv
import secrets

# Welcome to Cloud Functions for Firebase for Python!
# Deploy with `firebase deploy --only functions`

from firebase_functions import https_fn
from firebase_functions.options import set_global_options
from firebase_admin import initialize_app


import time

def get_valid_token_from_session():
    """
    Retrieves token from session, refreshing it if it's expired.
    Returns None if no token is available or refresh fails.
    """
    token = session.get('access_token')
    expires_at = session.get('expires_at')
    
    if not token:
        return None

    # Check if token is expired (or close to expiring, e.g., within 60 seconds)
    if expires_at and time.time() > (expires_at - 60):
        print("⟳ Token expired (or expiring soon), attempting refresh...")
        refresh_token = session.get('refresh_token')
        
        if refresh_token:
            try:
                sp_oauth = get_spotify_oauth()
                token_info = sp_oauth.refresh_access_token(refresh_token)
                
                # Update session
                session['access_token'] = token_info['access_token']
                session['expires_at'] = token_info['expires_at']
                
                print("✓ Token refreshed successfully")
                return token_info['access_token']
            except Exception as e:
                print(f"✗ Failed to refresh token: {e}")
                return None
    return token

# Initialize Firebase Admin (uses default credentials in Cloud Functions)
try:
    initialize_app()
    print("✓ Firebase Admin initialized")
except ValueError:
    # Already initialized
    pass

# For cost control, you can set the maximum number of containers that can be
# running at the same time. This helps mitigate the impact of unexpected
# traffic spikes by instead downgrading performance. This limit is a per-function
# limit. You can override the limit for each function using the max_instances
# parameter in the decorator, e.g. @https_fn.on_request(max_instances=5).
set_global_options(max_instances=10)

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, '.env')

# Load environment variables from .env file
# Try loading from the backend directory explicitly
if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)
    print(f"✓ Loaded .env file from {ENV_PATH}")
else:
    # Fallback to default behavior (look in current working directory)
    load_dotenv()
    if os.path.exists('.env'):
        print(f"✓ Loaded .env file from current directory")
    else:
        print(f"⚠ Warning: .env file not found. Expected at: {ENV_PATH}")
        print(f"  Or in current working directory: {os.getcwd()}")

# Initialize Flask application instance
app = Flask(__name__)
# Set secret key for session management (used for OAuth)
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(16))
app.config['SESSION_COOKIE_NAME'] = 'nichefy_session'
app.config['SESSION_COOKIE_HTTPONLY'] = True
# Increase timeout for long-running requests (e.g., Perplexity API calls)
# This helps prevent connection timeouts during API processing
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development
# Note: For production, consider using a proper WSGI server (gunicorn, uwsgi) with timeout settings
# Session cookie configuration for production
is_production = os.getenv('ENVIRONMENT', '').lower() == 'production' or os.getenv('GCP_PROJECT') is not None
app.config['SESSION_COOKIE_SAMESITE'] = 'None' if is_production else 'Lax'  # None for cross-domain in production
app.config['SESSION_COOKIE_SECURE'] = is_production  # True in production with HTTPS
app.config['SESSION_COOKIE_DOMAIN'] = None  # Let browser set domain
app.config['SESSION_COOKIE_PATH'] = '/'  # Make cookie available for all paths

# Enable CORS (Cross-Origin Resource Sharing) to allow requests from frontend
# Get allowed origins from environment variable, with fallback for local development
CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://127.0.0.1:3000,http://localhost:3000')
# Split comma-separated origins into list
allowed_origins = [origin.strip() for origin in CORS_ORIGINS.split(',')]

# Configure CORS
# Note: For Vercel preview deployments, add specific URLs to CORS_ORIGINS
# or set ALLOW_VERCEL_PREVIEWS=true and we'll use a more permissive CORS
if os.getenv('ALLOW_VERCEL_PREVIEWS', 'false').lower() == 'true':
    # Allow all origins when ALLOW_VERCEL_PREVIEWS is true (for development/testing)
    CORS(app, supports_credentials=True)
    print(f"✓ CORS configured to allow all origins (ALLOW_VERCEL_PREVIEWS=true)")
else:
    CORS(app, origins=allowed_origins, supports_credentials=True)
    print(f"✓ CORS configured for origins: {allowed_origins}")

# Frontend URL for OAuth redirects (used in callback)
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

# Spotify OAuth configuration
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
# For Firebase Functions, construct redirect URI from function URL or use env var
FUNCTION_REGION = os.getenv('FUNCTION_REGION', 'us-central1')
PROJECT_ID = os.getenv('GCP_PROJECT', os.getenv('GCLOUD_PROJECT', ''))
FUNCTION_NAME = os.getenv('FUNCTION_TARGET', 'nichefy_api')

# Build Firebase Function URL if not provided
if PROJECT_ID:
    default_redirect_uri = f"https://{FUNCTION_REGION}-{PROJECT_ID}.cloudfunctions.net/{FUNCTION_NAME}/api/auth/callback"
else:
    default_redirect_uri = os.getenv('BACKEND_URL', 'http://localhost:5000') + '/api/auth/callback'

SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI', default_redirect_uri)

# Debug: Print credential status (without showing actual values)
if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
    print(f"✓ Spotify credentials loaded (Client ID: {SPOTIFY_CLIENT_ID[:10]}...)")
    print(f"✓ Redirect URI configured: {SPOTIFY_REDIRECT_URI}")
    print(f"  ⚠️  IMPORTANT: Make sure this EXACT URI is added to your Spotify app's Redirect URIs:")
    print(f"     https://developer.spotify.com/dashboard -> Your App -> Settings -> Redirect URIs")
    print(f"     Add: {SPOTIFY_REDIRECT_URI}")
else:
    print("✗ Spotify credentials not found!")
    print(f"  SPOTIFY_CLIENT_ID: {'Set' if SPOTIFY_CLIENT_ID else 'NOT SET'}")
    print(f"  SPOTIFY_CLIENT_SECRET: {'Set' if SPOTIFY_CLIENT_SECRET else 'NOT SET'}")
    print(f"  Please create a .env file in {BASE_DIR} with your Spotify credentials.")

# Required scopes for Spotify OAuth
SCOPE = "user-read-private user-read-email user-top-read"

def get_spotify_oauth():
    """Create and return a SpotifyOAuth instance"""
    return SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SCOPE,
        show_dialog=True
    )

def _recommend_niche_stream(artist_id, access_token):
    """
    Stream progress updates using Server-Sent Events (SSE) while finding niche artists.
    """
    import queue
    import threading
    
    def generate():
        try:
            # Use a queue to pass progress updates from callback to generator
            progress_queue = queue.Queue()
            
            def progress_callback(event_type, data):
                progress_queue.put({
                    'type': event_type,
                    'data': data,
                    'timestamp': time.time()
                })
            
            # Send initial message
            yield f"data: {json.dumps({'type': 'start', 'message': 'Starting search for niche artists...'})}\n\n"
            
            niche_artists = []
            error_occurred = None
            search_complete = threading.Event()
            
            def run_search():
                nonlocal niche_artists, error_occurred
                try:
                    niche_artists = find_niche_cousins(
                        artist_id, 
                        access_token, 
                        max_popularity=40, 
                        min_popularity=15,
                        progress_callback=progress_callback
                    )
                except Exception as e:
                    error_occurred = str(e)
                finally:
                    search_complete.set()
            
            # Start search in a thread
            search_thread = threading.Thread(target=run_search, daemon=True)
            search_thread.start()
            
            # Monitor for progress updates and completion
            while not search_complete.is_set() or not progress_queue.empty():
                try:
                    # Get progress update with timeout
                    update = progress_queue.get(timeout=0.1)
                    yield f"data: {json.dumps(update)}\n\n"
                except queue.Empty:
                    # No update available, continue waiting
                    continue
            
            # Wait for thread to complete
            search_thread.join(timeout=1)
            
            if error_occurred:
                yield f"data: {json.dumps({'type': 'error', 'message': error_occurred})}\n\n"
                return
            
            # Process and send final results
            seen_ids = set()
            unique_artists = []
            
            for artist in niche_artists:
                if artist['id'] not in seen_ids:
                    seen_ids.add(artist['id'])
                    unique_artists.append({
                        'id': artist['id'],
                        'name': artist['name'],
                        'image': artist['images'][0]['url'] if artist.get('images') else None,
                        'popularity': artist['popularity'],
                        'spotify_url': artist['external_urls'].get('spotify', ''),
                        'genres': artist.get('genres', [])
                    })
            
            # Send final result
            yield f"data: {json.dumps({'type': 'complete', 'artists': unique_artists, 'count': len(unique_artists)})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'  # Disable buffering in nginx
        }
    )

@app.route('/api/recommend/niche', methods=['POST'])
def recommend_niche():
    """
    Main API endpoint for finding niche artists.
    Supports both regular JSON response and Server-Sent Events (SSE) streaming.
    
    Accepts POST request with:
    - artist_id: Spotify artist ID to use as seed
    - stream: (optional) If true, returns SSE stream with progress updates
    
    Access token is obtained from session (if logged in via OAuth) or request body (for backwards compatibility).
    
    Returns JSON with list of niche artists (popularity <= 20) that are similar to the seed artist.
    """
    try:
        data = request.get_json() or {}
        artist_id = data.get('artist_id')
        stream_mode = data.get('stream', False)
        
        # --- CHANGE START ---
        # Try to get a valid (refreshed) token from session first
        access_token = get_valid_token_from_session()
        
        # If not in session, try request body (backwards compatibility)
        if not access_token:
             access_token = data.get('access_token')
        # --- CHANGE END ---
        
        if not artist_id:
            return jsonify({"error": "artist_id is required"}), 400
            
        if not access_token:
            return jsonify({"error": "Not authenticated or session expired."}), 401
        
        # Debug: Verify token format
        if not isinstance(access_token, str) or len(access_token.strip()) == 0:
            return jsonify({"error": "Invalid access token format"}), 401
        
        print(f"✓ Calling find_niche_cousins with artist_id={artist_id}, token length={len(access_token)}")
        
        # If streaming mode, use SSE
        if stream_mode:
            return _recommend_niche_stream(artist_id, access_token)
        
        # Call the recursive algorithm to find niche artists
        # This function searches through related artists and their related artists
        # to find artists with popularity between 5 and 20
        try:
            niche_artists = find_niche_cousins(artist_id, access_token, max_popularity=40, min_popularity=15)
        except Exception as e:
            error_msg = str(e)
            print(f"✗ Error in find_niche_cousins: {error_msg}")
            # Return error response instead of empty list
            return jsonify({
                "success": False,
                "error": f"Failed to find niche artists: {error_msg}",
                "artists": [],
                "count": 0
            }), 500
        
        # Remove duplicates based on artist ID
        # The recursive algorithm might return the same artist multiple times
        seen_ids = set()  # Track which artist IDs we've already seen
        unique_artists = []  # Store unique artists only
        
        if not niche_artists:
            # Log why no niche artists were found
            print(f"⚠️  No niche artists found for artist_id: {artist_id}")
            print(f"   Possible reasons:")
            print(f"   1. All related artists have popularity > 20")
            print(f"   2. The artist has no related artists (404 error from Spotify)")
            print(f"   3. The recursive search couldn't find niche artists even at depth 2")
            print(f"   4. The access token may have insufficient permissions")
        
        for artist in niche_artists:
            if artist['id'] not in seen_ids:
                seen_ids.add(artist['id'])
                # Transform Spotify API response to our simplified format
                unique_artists.append({
                    'id': artist['id'],  # Spotify artist ID
                    'name': artist['name'],  # Artist name
                    # Get first image URL if available, otherwise None
                    'image': artist['images'][0]['url'] if artist.get('images') and len(artist['images']) > 0 else None,
                    'popularity': artist['popularity'],  # Popularity score (0-100)
                    'spotify_url': artist['external_urls'].get('spotify', ''),  # Link to Spotify page
                    'genres': artist.get('genres', [])  # List of genre tags
                })
        
        # Return successful response with the list of unique niche artists
        return jsonify({
            "success": True,
            "artists": unique_artists,
            "count": len(unique_artists)  # Total number of niche artists found
        }), 200
        
    except Exception as e:
        # Catch any errors and return a 500 error response
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint.
    Used to verify the API server is running and responsive.
    """
    return jsonify({"status": "healthy"}), 200

@app.route('/api/auth/config', methods=['GET'])
def auth_config():
    """
    Return OAuth configuration details for debugging.
    Useful for verifying redirect URI setup.
    """
    return jsonify({
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "client_id_configured": bool(SPOTIFY_CLIENT_ID),
        "client_secret_configured": bool(SPOTIFY_CLIENT_SECRET),
        "instructions": {
            "step1": "Go to https://developer.spotify.com/dashboard",
            "step2": "Select your app",
            "step3": "Click 'Settings'",
            "step4": f"Scroll to 'Redirect URIs' section",
            "step5": f"Click 'Add' and enter: {SPOTIFY_REDIRECT_URI}",
            "step6": "Click 'Save' at the bottom",
            "important": "The redirect URI must match EXACTLY (including http:// and no trailing slash)"
        }
    }), 200

@app.route('/api/auth/login', methods=['GET'])
def spotify_login():
    """
    Initiate Spotify OAuth login flow.
    Redirects user to Spotify authorization page.
    """
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        error_msg = (
            "Spotify credentials not configured. "
            "Please create a .env file in the backend directory with: "
            "SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, and SPOTIFY_REDIRECT_URI. "
            f"See {BASE_DIR}/README.md for setup instructions."
        )
        print(f"ERROR: {error_msg}")
        return jsonify({
            "error": "Spotify credentials not configured",
            "details": "Missing SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET in .env file",
            "help": f"Create a .env file in {BASE_DIR} with your Spotify app credentials"
        }), 500
    
    try:
        sp_oauth = get_spotify_oauth()
        auth_url = sp_oauth.get_authorize_url()
        print(f"✓ Generated OAuth URL with redirect URI: {SPOTIFY_REDIRECT_URI}")
        return jsonify({"auth_url": auth_url}), 200
    except Exception as e:
        error_msg = str(e)
        print(f"✗ Error generating OAuth URL: {error_msg}")
        
        # Check if it's a redirect URI error
        if "redirect_uri" in error_msg.lower() or "invalid" in error_msg.lower():
            return jsonify({
                "error": "Invalid redirect URI",
                "details": error_msg,
                "redirect_uri": SPOTIFY_REDIRECT_URI,
                "help": f"Please add this EXACT redirect URI to your Spotify app settings:\n{SPOTIFY_REDIRECT_URI}\n\nGo to: https://developer.spotify.com/dashboard -> Your App -> Settings -> Redirect URIs"
            }), 400
        
        return jsonify({
            "error": "Failed to initiate OAuth",
            "details": error_msg
        }), 500

@app.route('/api/auth/callback', methods=['GET'])
def spotify_callback():
    """
    Handle Spotify OAuth callback.
    Exchanges authorization code for access token.
    """
    try:
        code = request.args.get('code')
        error = request.args.get('error')
        error_description = request.args.get('error_description', '')
        
        if error:
            error_msg = f"{error}"
            if error_description:
                error_msg += f": {error_description}"
            print(f"✗ OAuth error received: {error_msg}")
            
            # Provide helpful message for redirect URI errors
            if "redirect_uri" in error_description.lower() or "invalid" in error_description.lower():
                error_msg += f"\n\nMake sure you've added this EXACT redirect URI to your Spotify app:\n{SPOTIFY_REDIRECT_URI}"
            
            return redirect(f"{FRONTEND_URL}?error={error}&details={error_description}")
        
        if not code:
            print("✗ No authorization code received in callback")
            return redirect(f"{FRONTEND_URL}?error=no_code")
        
        print(f"✓ Received authorization code, exchanging for token...")
        sp_oauth = get_spotify_oauth()
        # Explicitly use as_dict=True to avoid deprecation warning and get full token info
        # This ensures we get a dict with access_token, refresh_token, and expires_at
        token_info = sp_oauth.get_access_token(code, as_dict=True)
        
        if not token_info:
            print("✗ Failed to exchange code for token")
            return redirect(f"{FRONTEND_URL}?error=token_failed")
        
        # Extract token information from dict response
        access_token = token_info['access_token']
        refresh_token = token_info.get('refresh_token')
        expires_at = token_info.get('expires_at', 0)
        
        # Store token in session (could also store in cookie or return to frontend)
        session['access_token'] = access_token
        session['refresh_token'] = refresh_token
        session['expires_at'] = expires_at
        
        # Force session to be saved
        session.permanent = True
        
        print("✓ Successfully authenticated with Spotify")
        print(f"✓ Access token stored in session: {bool(session.get('access_token'))}")
        print(f"✓ Session cookie will be set: {app.config['SESSION_COOKIE_NAME']}")
        
        # In production, try to use cookies only. For development or if cookies fail,
        # pass token in URL as fallback
        redirect_url = f"{FRONTEND_URL}?logged_in=true&token={access_token}"
        print(f"✓ Redirecting to frontend: {FRONTEND_URL}")
        
        # Create response to ensure cookie is set before redirect
        from flask import make_response
        response = make_response(redirect(redirect_url))
        
        return response
    
    except Exception as e:
        error_msg = str(e)
        print(f"✗ Exception in OAuth callback: {error_msg}")
        
        # Check if it's a redirect URI error
        if "redirect_uri" in error_msg.lower() or "invalid" in error_msg.lower():
            error_msg += f"\n\nMake sure you've added this EXACT redirect URI to your Spotify app:\n{SPOTIFY_REDIRECT_URI}"
        
        return redirect(f"{FRONTEND_URL}?error=callback_error&details={error_msg}")

@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    """
    Check if user is authenticated and return token info.
    """
    try:
        print(f"✓ Auth status check - Session keys: {list(session.keys())}")
        # Also check for token in query params (fallback for cross-domain issues)
        access_token = request.args.get('access_token') or session.get('access_token')
        expires_at = session.get('expires_at', 0)
        
        if not access_token:
            print("✗ No access token found in session or query params")
            return jsonify({"authenticated": False}), 200
        
        print(f"✓ Access token found in session")
        
        # Check if token is expired
        import time
        if expires_at and time.time() > expires_at:
            # Try to refresh token
            refresh_token = session.get('refresh_token')
            if refresh_token:
                try:
                    sp_oauth = get_spotify_oauth()
                    token_info = sp_oauth.refresh_access_token(refresh_token)
                    access_token = token_info['access_token']
                    session['access_token'] = access_token
                    session['expires_at'] = token_info.get('expires_at', 0)
                except:
                    session.clear()
                    return jsonify({"authenticated": False}), 200
            else:
                session.clear()
                return jsonify({"authenticated": False}), 200
        
        return jsonify({
            "authenticated": True,
            "access_token": access_token
        }), 200
        
    except Exception as e:
        print(f"✗ Error in auth status check: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "authenticated": False,
            "error": str(e)
        }), 200

@app.route('/api/auth/logout', methods=['POST'])
def spotify_logout():
    """
    Logout user by clearing session.
    """
    session.clear()
    return jsonify({"success": True}), 200

@app.route('/api/user/profile', methods=['GET'])
def user_profile():
    """
    Get current user's Spotify profile information.
    
    Access token is obtained from session (if logged in via OAuth) or request query parameter.
    """
    try:
        # Get access token from session or request
        access_token = request.args.get('access_token') or session.get('access_token')
        
        if not access_token:
            return jsonify({"error": "Not authenticated. Please log in with Spotify."}), 401
        
        # Create Spotify client
        sp = spotipy.Spotify(auth=access_token)
        
        # Get current user's profile
        user = sp.current_user()
        
        return jsonify({
            "success": True,
            "user": {
                "id": user.get('id'),
                "display_name": user.get('display_name'),
                "email": user.get('email'),
                "image": user['images'][0]['url'] if user.get('images') and len(user['images']) > 0 else None,
                "country": user.get('country'),
                "product": user.get('product')  # free, premium, etc.
            }
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/search/artists', methods=['GET'])
def search_artists():
    """
    Search for artists by name using Spotify API.
    
    Query parameters:
    - q: Search query (artist name)
    - access_token: Spotify access token (optional if logged in via OAuth)
    """
    try:
        query = request.args.get('q')
        if not query:
            return jsonify({"error": "Query parameter 'q' is required"}), 400
        
        # Get access token from session or request
        access_token = request.args.get('access_token') or session.get('access_token')
        
        if not access_token:
            return jsonify({"error": "Not authenticated. Please log in with Spotify."}), 401
        
        # Create Spotify client
        sp = spotipy.Spotify(auth=access_token)
        
        # Search for artists
        results = sp.search(q=query, type='artist', limit=10)
        artists = results.get('artists', {}).get('items', [])
        
        # Transform to simplified format
        artist_results = []
        for artist in artists:
            artist_results.append({
                'id': artist['id'],
                'name': artist['name'],
                'image': artist['images'][0]['url'] if artist.get('images') else None,
                'popularity': artist['popularity'],
                'spotify_url': artist['external_urls'].get('spotify', ''),
                'genres': artist.get('genres', [])
            })
        
        return jsonify({
            "success": True,
            "artists": artist_results,
            "count": len(artist_results)
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/recommend/user', methods=['POST'])
def user_top_artists_recommendations():
    """
    Get niche recommendations based on user's top artists.
    
    Access token is obtained from session (if logged in via OAuth) or request body (for backwards compatibility).
    """
    try:
        data = request.get_json() or {}
        
        # Get access token from session (OAuth) or request body (backwards compatibility)
        access_token = session.get('access_token') or data.get('access_token')

        if not access_token:
            return jsonify({"error": "Not authenticated. Please log in with Spotify."}), 401

        niche_artists = recommend_niche_for_top_artists(access_token)

        seen_ids = set()
        unique_artists = []
        
        for niche_id, data in niche_artists.items():
            niche_artist = data['niche_artist']
            original_artist = data['original_artist']
            
            if niche_artist['id'] not in seen_ids:
                seen_ids.add(niche_artist['id'])
                # Transform Spotify API response to our simplified format
                unique_artists.append({
                    'id': niche_artist['id'],  # Spotify artist ID
                    'name': niche_artist['name'],  # Artist name
                    'recommended_from': original_artist['id'],  # Original artist ID
                    # Get first image URL if available, otherwise None
                    'image': niche_artist['images'][0]['url'] if niche_artist.get('images') else None,
                    'popularity': niche_artist['popularity'],  # Popularity score (0-100)
                    'spotify_url': niche_artist['external_urls'].get('spotify', ''),  # Link to Spotify page
                    'genres': niche_artist.get('genres', [])  # List of genre tags
                })
        
        # Return successful response with the list of unique niche artists
        return jsonify({
            "success": True,
            "artists": unique_artists,
            "count": len(unique_artists)  # Total number of niche artists found
        }), 200

    except Exception as e:
        # Catch any errors and return a 500 error response
        return jsonify({"error": str(e)}), 500


# Export Flask app as Firebase Cloud Function
# For Firebase Functions Python SDK, we wrap the Flask app
# This allows Firebase to route all HTTP requests through Flask

# WSGI adapter for Firebase Functions
from werkzeug.wrappers import Request as WerkzeugRequest

def create_wsgi_environ(firebase_req: https_fn.Request) -> dict:
    """Convert Firebase Functions Request to WSGI environ dict."""
    # Parse URL
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(firebase_req.url)
    
    # Build WSGI environ
    environ = {
        'REQUEST_METHOD': firebase_req.method,
        'SCRIPT_NAME': '',
        'PATH_INFO': parsed.path,
        'QUERY_STRING': parsed.query,
        'CONTENT_TYPE': firebase_req.headers.get('Content-Type', ''),
        'CONTENT_LENGTH': str(len(firebase_req.get_data())) if firebase_req.method in ['POST', 'PUT', 'PATCH'] else '0',
        'SERVER_NAME': parsed.hostname or 'localhost',
        'SERVER_PORT': str(parsed.port) if parsed.port else ('443' if parsed.scheme == 'https' else '80'),
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': parsed.scheme,
        'wsgi.input': firebase_req.get_data(),
        'wsgi.errors': None,
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
    }
    
    # Add HTTP headers
    for key, value in firebase_req.headers.items():
        key = key.upper().replace('-', '_')
        if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            environ[f'HTTP_{key}'] = value
    
    return environ

@https_fn.on_request(
    max_instances=10
)
def nichefy_api(req: https_fn.Request) -> https_fn.Response:
    """
    Firebase Cloud Function handler.
    Routes all HTTP requests to the Flask application.
    """
    # Create WSGI environ from Firebase request
    environ = create_wsgi_environ(req)
    
    # Call Flask app as WSGI application
    response_data = []
    status_code = [200]
    response_headers = [{}]
    
    def start_response(status, headers):
        status_code[0] = int(status.split()[0])
        response_headers[0] = dict(headers)
    
    # Call Flask app with WSGI interface
    try:
        for data in app(environ, start_response):
            if data:
                response_data.append(data)
        
        # Combine response data
        body = b''.join(response_data) if response_data else b''
        
        return https_fn.Response(
            body,
            status=status_code[0],
            headers=response_headers[0],
        )
    except Exception as exc:
        app.logger.exception(exc)
        return https_fn.Response(
            b'Internal Server Error',
            status=500,
        )

# Run the Flask development server when this file is executed directly
if __name__ == '__main__':
    print("\n" + "="*60)
    print("Starting Nichefy Backend Server")
    print("="*60)
    
    # Check if Spotify credentials are configured
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        print("\n⚠️  WARNING: Spotify credentials not configured!")
        print("\nTo set up Spotify OAuth:")
        print("1. Create a .env file in the backend/functions directory")
        print(f"2. Add the following variables to {BASE_DIR}\\.env:")
        print("   SPOTIFY_CLIENT_ID=your-client-id")
        print("   SPOTIFY_CLIENT_SECRET=your-client-secret")
        print("   SPOTIFY_REDIRECT_URI=http://localhost:5000/api/auth/callback")
        print("   FLASK_SECRET_KEY=any-random-string-here")
        print("   FRONTEND_URL=http://localhost:3000")
        print("\n3. Get your credentials from: https://developer.spotify.com/dashboard")
        print("4. Make sure to add the redirect URI to your Spotify app settings\n")
    else:
        print("\n✓ Spotify OAuth configured successfully")
    
    print("="*60 + "\n")
    
    # debug=True enables auto-reload on code changes and detailed error pages
    # port=5000 is the default Flask port
    app.run(debug=True, port=5000)

