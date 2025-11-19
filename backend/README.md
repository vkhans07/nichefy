# Nichefy Backend

Flask backend for the Nichefy application.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Firebase:
   - Download your Firebase service account key JSON file
   - Place it in the `backend/` directory as `serviceAccountKey.json`

3. Run the Flask server:
```bash
python app.py
```

The server will run on `http://localhost:5000`

## API Endpoints

### POST `/api/recommend/niche`
Recommends niche artists based on a seed artist.

**Request Body:**
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

### GET `/health`
Health check endpoint.

