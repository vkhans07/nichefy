# Nichefy Backend

Flask backend for the Nichefy application.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Spotify OAuth:
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Create a new app or use an existing one
   - Note your Client ID and Client Secret
   - **IMPORTANT**: Add the redirect URI to your app's settings:
     1. Click on your app in the dashboard
     2. Click "Settings" button
     3. Scroll to "Redirect URIs" section
     4. Click "Add" and enter: `http://127.0.0.1:5000/api/auth/callback`
     5. **Make sure it matches EXACTLY** (including `http://`, no trailing slash)
     6. Click "Save" at the bottom
   - If you see an "invalid redirect uri" error, verify the URI in your Spotify app matches exactly what's shown in your server console

3. Create a `.env` file:
   
   **Option A: Use the setup helper script (recommended)**
   ```bash
   python setup_env.py
   ```
   Then edit the created `.env` file with your actual credentials.
   
   **Option B: Create manually**
   Create a `.env` file in the `backend/` directory with:
   ```env
   FLASK_SECRET_KEY=your-secret-key-here-generate-a-random-string
   SPOTIFY_CLIENT_ID=your-spotify-client-id
   SPOTIFY_CLIENT_SECRET=your-spotify-client-secret
   SPOTIFY_REDIRECT_URI=http://127.0.0.1:5000/api/auth/callback
   ```

4. (Optional) Set up Firebase:
   - Download your Firebase service account key JSON file
   - Place it in the `backend/` directory as `serviceAccountKey.json`

5. Run the Flask server:
```bash
python app.py
```

The server will run on `http://127.0.0.1:5000`

## API Endpoints

### GET `/api/auth/login`
Initiates Spotify OAuth login flow. Returns authorization URL.

### GET `/api/auth/callback`
Spotify OAuth callback endpoint. Handles the OAuth redirect and stores access token in session.

### GET `/api/auth/status`
Check authentication status. Returns whether user is authenticated and access token (if authenticated).

### POST `/api/auth/logout`
Logout user and clear session.

### GET `/api/search/artists?q=<artist_name>`
Search for artists by name using Spotify API.
Requires authentication (via session cookie or access_token query parameter).

**Response:**
```json
{
  "success": true,
  "artists": [
    {
      "id": "artist_id",
      "name": "Artist Name",
      "image": "image_url",
      "popularity": 80,
      "spotify_url": "https://open.spotify.com/artist/...",
      "genres": ["genre1", "genre2"]
    }
  ],
  "count": 10
}
```

### POST `/api/recommend/niche`
Recommends niche artists based on a seed artist.
Requires authentication (via session cookie or access_token in request body).

**Request Body:**
```json
{
  "artist_id": "spotify_artist_id"
}
```

**Response:**
```json
{
  "success": true,
  "artists": [
    {
      "id": "artist_id",
      "name": "Artist Name",
      "image": "image_url",
      "popularity": 15,
      "spotify_url": "https://open.spotify.com/artist/...",
      "genres": ["genre1", "genre2"]
    }
  ],
  "count": 5
}
```

### GET `/health`
Health check endpoint.

