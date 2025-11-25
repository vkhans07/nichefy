"""
Helper script to create a .env file for Nichefy backend.
This script will create a template .env file if it doesn't exist.
"""

import os

def create_env_file():
    """Create a .env file template if it doesn't exist"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(base_dir, '.env')
    
    if os.path.exists(env_path):
        print(f"✓ .env file already exists at: {env_path}")
        print("  Please check it contains all required variables:")
        print("  - FLASK_SECRET_KEY")
        print("  - SPOTIFY_CLIENT_ID")
        print("  - SPOTIFY_CLIENT_SECRET")
        print("  - SPOTIFY_REDIRECT_URI (optional, defaults to http://127.0.0.1:5000/api/auth/callback)")
        print("  - PERPLEXITY_API_KEY (optional, for finding related artists)")
        return
    
    # Create template .env file
    template = """# Flask Configuration
# Generate a random secret key for session management
FLASK_SECRET_KEY=change-me-to-a-random-string

# Spotify OAuth Configuration
# Get these from https://developer.spotify.com/dashboard
# 1. Create a new app or use an existing one
# 2. Copy the Client ID and Client Secret
# 3. Add this redirect URI to your app: http://127.0.0.1:5000/api/auth/callback
SPOTIFY_CLIENT_ID=your-spotify-client-id-here
SPOTIFY_CLIENT_SECRET=your-spotify-client-secret-here

# Spotify OAuth Redirect URI
# Must match the redirect URI configured in your Spotify app settings
SPOTIFY_REDIRECT_URI=http://127.0.0.1:5000/api/auth/callback

# Perplexity API Configuration (Optional)
# Get your API key from https://www.perplexity.ai/settings/api
# Used for finding related artists (replaces deprecated Spotify endpoints)
PERPLEXITY_API_KEY=your-perplexity-api-key-here
"""
    
    try:
        with open(env_path, 'w') as f:
            f.write(template)
        print(f"✓ Created .env file at: {env_path}")
        print("\n⚠️  IMPORTANT: Please edit the .env file and add your actual credentials!")
        print("   1. Get your Spotify credentials from: https://developer.spotify.com/dashboard")
        print("   2. Replace 'your-spotify-client-id-here' with your actual Client ID")
        print("   3. Replace 'your-spotify-client-secret-here' with your actual Client Secret")
        print("   4. Generate a random string for FLASK_SECRET_KEY")
        print("   5. Add http://127.0.0.1:5000/api/auth/callback to your Spotify app's Redirect URIs")
    except Exception as e:
        print(f"✗ Failed to create .env file: {e}")

if __name__ == '__main__':
    print("Nichefy Backend - .env Setup Helper")
    print("=" * 50)
    create_env_file()
    print("=" * 50)

