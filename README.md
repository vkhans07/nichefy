# Nichefy MVP

A web application where users input a popular music artist, and the app recommends "niche" artists (Spotify Popularity Score < 20) that sound similar.

## Tech Stack

- **Frontend:** Next.js 14 (App Router), Tailwind CSS, Lucide React, Axios
- **Backend:** Python Flask, Spotipy (Spotify Client), Firebase-Admin (Firestore)
- **Database:** Google Firestore (NoSQL)

## Project Structure

```
.
├── frontend/          # Next.js 14 application
├── backend/           # Flask API server
└── README.md
```

## Quick Start

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up Firebase:
   - Download your Firebase service account key JSON file from Firebase Console
   - Place it in the `backend/` directory as `serviceAccountKey.json`

5. Run the Flask server:
```bash
python app.py
```

The backend will run on `http://127.0.0.1:5000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

The frontend will be available at `http://127.0.0.1:3000`

## How It Works

1. User enters a popular artist's Spotify ID and provides a Spotify access token
2. The backend uses a recursive algorithm to find related artists
3. Artists with popularity ≤ 20 are identified as "niche"
4. If fewer than 3 niche artists are found, the algorithm recursively searches through less popular related artists (up to depth 2)
5. Results are displayed in a beautiful, responsive UI

## API Endpoints

### POST `/api/recommend/niche`

Recommends niche artists based on a seed artist.

**Request:**
```json
{
  "artist_id": "spotify_artist_id",
  "access_token": "spotify_access_token"
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

## Getting Spotify Credentials

To use this app, you'll need:

1. **Spotify Artist ID**: Found in the Spotify artist URL
   - Example: `https://open.spotify.com/artist/06HL4z0CvFAxyc27GXpf02`
   - The ID is: `06HL4z0CvFAxyc27GXpf02`

2. **Spotify Access Token**: Get from Spotify Web API
   - Use the [Spotify Web API Console](https://developer.spotify.com/console/)
   - Or implement OAuth flow in your application
   - Token should have `user-read-private` and `user-read-email` scopes (or use Client Credentials flow)

## Development Notes

- The backend uses CORS to allow requests from `http://127.0.0.1:3000`
- Firebase is set up but not actively used in the MVP (ready for future features like caching)
- The niche finding algorithm has a maximum recursion depth of 2 to prevent excessive API calls

## License

MIT

