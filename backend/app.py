"""
Flask Backend API for Nichefy
Main application file that handles HTTP requests and serves the niche artist recommendation API.
"""

# Flask: Web framework for creating the REST API
from flask import Flask, request, jsonify, session, redirect
# CORS: Allows frontend (running on different port) to make requests to this backend
from flask_cors import CORS
# Import our custom function that finds niche artists using recursive algorithm
from niche_logic import find_niche_cousins, recommend_niche_for_top_artists
# Spotipy: Spotify Web API client library (imported but not directly used here)
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv
import secrets

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
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Use Lax for same-site requests
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_DOMAIN'] = None  # Allow cross-port cookies on localhost
app.config['SESSION_COOKIE_PATH'] = '/'  # Make cookie available for all paths

# Enable CORS (Cross-Origin Resource Sharing) to allow requests from frontend
# This allows the Next.js app on localhost:3000 to call this API on localhost:5000
CORS(app, origins=["http://127.0.0.1:3000","http://localhost:3000"], supports_credentials=True)

# Spotify OAuth configuration
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:5000/api/auth/callback')

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

@app.route('/api/recommend/niche', methods=['POST'])
def recommend_niche():
    """
    Main API endpoint for finding niche artists.
    
    Accepts POST request with:
    - artist_id: Spotify artist ID to use as seed
    
    Access token is obtained from session (if logged in via OAuth) or request body (for backwards compatibility).
    
    Returns JSON with list of niche artists (popularity <= 20) that are similar to the seed artist.
    """
    try:
        # Extract JSON data from the request body
        data = request.get_json() or {}
        
        # Extract required fields from the request
        artist_id = data.get('artist_id')  # Spotify artist ID (e.g., "06HL4z0CvFAxyc27GXpf02")
        
        # Get access token from session (OAuth) or request body (backwards compatibility)
        access_token = session.get('access_token') or data.get('access_token')
        
        # Validate required fields are present
        if not artist_id:
            return jsonify({"error": "artist_id is required"}), 400
        
        if not access_token:
            return jsonify({"error": "Not authenticated. Please log in with Spotify."}), 401
        
        # Call the recursive algorithm to find niche artists
        # This function searches through related artists and their related artists
        # to find artists with popularity <= 20
        niche_artists = find_niche_cousins(artist_id, access_token)
        
        # Remove duplicates based on artist ID
        # The recursive algorithm might return the same artist multiple times
        seen_ids = set()  # Track which artist IDs we've already seen
        unique_artists = []  # Store unique artists only
        
        for artist in niche_artists:
            if artist['id'] not in seen_ids:
                seen_ids.add(artist['id'])
                # Transform Spotify API response to our simplified format
                unique_artists.append({
                    'id': artist['id'],  # Spotify artist ID
                    'name': artist['name'],  # Artist name
                    # Get first image URL if available, otherwise None
                    'image': artist['images'][0]['url'] if artist.get('images') else None,
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
            
            return redirect(f"http://localhost:3000?error={error}&details={error_description}")
        
        if not code:
            print("✗ No authorization code received in callback")
            return redirect("http://localhost:3000?error=no_code")
        
        print(f"✓ Received authorization code, exchanging for token...")
        sp_oauth = get_spotify_oauth()
        token_info = sp_oauth.get_access_token(code)
        
        if not token_info:
            print("✗ Failed to exchange code for token")
            return redirect("http://localhost:3000?error=token_failed")
        
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
        
        # For localhost development: pass token in URL as fallback since cookies
        # set on port 5000 may not be accessible from port 3000
        # In production with same domain, remove token from URL and use only cookies
        redirect_url = f"http://localhost:3000?logged_in=true&token={access_token}"
        print(f"✓ Redirecting to frontend with logged_in=true")
        
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
        
        return redirect(f"http://localhost:3000?error=callback_error&details={error_msg}")

@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    """
    Check if user is authenticated and return token info.
    """
    print(f"✓ Auth status check - Session keys: {list(session.keys())}")
    access_token = session.get('access_token')
    expires_at = session.get('expires_at', 0)
    
    if not access_token:
        print("✗ No access token found in session")
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


# Run the Flask development server when this file is executed directly
if __name__ == '__main__':
    print("\n" + "="*60)
    print("Starting Nichefy Backend Server")
    print("="*60)
    
    # Check if Spotify credentials are configured
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        print("\n⚠️  WARNING: Spotify credentials not configured!")
        print("\nTo set up Spotify OAuth:")
        print("1. Create a .env file in the backend directory")
        print(f"2. Add the following variables to {BASE_DIR}\\.env:")
        print("   SPOTIFY_CLIENT_ID=your-client-id")
        print("   SPOTIFY_CLIENT_SECRET=your-client-secret")
        print("   SPOTIFY_REDIRECT_URI=http://localhost:5000/api/auth/callback")
        print("   FLASK_SECRET_KEY=any-random-string-here")
        print("\n3. Get your credentials from: https://developer.spotify.com/dashboard")
        print("4. Make sure to add the redirect URI to your Spotify app settings\n")
    else:
        print("\n✓ Spotify OAuth configured successfully")
    
    print("="*60 + "\n")
    
    # debug=True enables auto-reload on code changes and detailed error pages
    # port=5000 is the default Flask port
    app.run(debug=True, port=5000)

