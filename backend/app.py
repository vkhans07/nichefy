from flask import Flask, request, jsonify
from flask_cors import CORS
from niche_logic import find_niche_cousins
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])

@app.route('/api/recommend/niche', methods=['POST'])
def recommend_niche():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        artist_id = data.get('artist_id')
        access_token = data.get('access_token')
        
        if not artist_id:
            return jsonify({"error": "artist_id is required"}), 400
        
        if not access_token:
            return jsonify({"error": "access_token is required"}), 400
        
        # Find niche artists using the recursive algorithm
        niche_artists = find_niche_cousins(artist_id, access_token)
        
        # Remove duplicates based on artist ID
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
        
        return jsonify({
            "success": True,
            "artists": unique_artists,
            "count": len(unique_artists)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)

