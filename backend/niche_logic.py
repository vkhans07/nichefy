"""
Niche Artist Discovery Algorithm
Implements a recursive algorithm to find niche artists (low popularity) similar to a popular seed artist.
"""

from importlib import import_module


def _get_spotipy():
    """
    Dynamically import spotipy so static analyzers do not flag missing modules
    in editors where the virtual environment is not activated.
    """
    try:
        return import_module("spotipy")
    except ImportError as exc:  # pragma: no cover - guarded to aid DX
        raise ImportError(
            "spotipy is required to run Nichefy's backend. "
            "Install it with `pip install -r backend/requirements.txt`."
        ) from exc

def find_niche_cousins(seed_artist_id, access_token, max_popularity=20, depth=0, min_length=5):
    """
    Recursively find niche artists (popularity <= max_popularity) related to a seed artist.
    
    Algorithm Strategy:
    1. Get related artists for the seed artist
    2. Separate them into "niche" (popularity <= 20) and "popular" (popularity > 20)
    3. If we found fewer than 3 niche artists and haven't reached max depth:
       - Take the least popular artist from the "popular" list (closest to niche)
       - Recursively search their related artists
    4. Continue until we have enough niche artists or reach max depth (2 levels, more than that will be super messy)
    
    Args:
        seed_artist_id: Spotify artist ID to start the search from
        access_token: Spotify API access token for authentication
        max_popularity: Maximum popularity score to be considered "niche" (default: 20)
                       Spotify popularity is 0-100, where 100 is most popular
        depth: Current recursion depth (default: 0, max: 2)
               Prevents infinite recursion and excessive API calls

        (i asked cursor to annotate the code more but this is all very accurate :thumbs_up:)
    
    Returns:
        List of niche artist objects from Spotify API (each with id, name, popularity, etc.)
    """
    # Initialize Spotify API client with the provided access token.
    # Importing via import_module keeps static analyzers from complaining
    # when the dependency is not installed in the editor environment.
    sp = _get_spotipy().Spotify(auth=access_token)
    
    try:
        # Fetch artists related to the seed artist from Spotify API
        # Returns up to 20 related artists based on Spotify's algorithm
        related = sp.artist_related_artists(seed_artist_id)
    except Exception as e:
        # If API call fails (invalid token, network error, etc.), return empty list
        print(f"Error fetching related artists: {e}")
        return []
    
    # Extract the list of artists from the API response
    artists = related.get('artists', [])
    
    # Separate artists into two categories:
    niche_finds = []  # Artists with popularity <= 20 (these are our target "niche" artists)
    potential_bridges = []  # Popular artists (popularity > 20) that we might use to dig deeper
    
    # Categorize each related artist
    for artist in artists:
        if artist['popularity'] <= max_popularity:
            # This artist is niche enough - add to our results
            niche_finds.append(artist)
        else:
            # This artist is too popular, but might lead us to niche artists
            # Store it as a potential "bridge" to explore further
            potential_bridges.append(artist)
    
    # Recursive step: If we don't have enough niche artists, dig deeper
    # We want at least 3 niche artists, and we'll recurse up to depth 2
    if len(niche_finds) < min_length and depth < 2:
        # Sort potential bridges by popularity (ascending)
        # This means we'll explore the least popular popular artist first
        # (the one closest to being niche, most likely to have niche connections)
        potential_bridges.sort(key=lambda x: x['popularity'])
        
        if potential_bridges:
            # Use the least popular artist as a "bridge" to find more niche artists
            bridge_artist = potential_bridges[0]
            
            # Recursively search the bridge artist's related artists
            # Increment depth to track how deep we've gone
            deeper_finds = find_niche_cousins(
                bridge_artist['id'],  # Use bridge artist as new seed
                access_token, 
                max_popularity, 
                depth + 1,  # Increment depth to prevent infinite recursion
                min_length - len(niche_finds) #we always get to our minimum finds without scumming for poor results
            )
            
            # Add the newly found niche artists to our results
            niche_finds.extend(deeper_finds)
    
    # Return all niche artists found at this level and deeper levels
    return niche_finds


def recommend_niche_for_top_artists(access_token, max_popularity = 20):
    sp = _get_spotipy().Spotify(auth=access_token)

    #get top artists
    top_artists = sp.current_user_top_artists(limit = 8, offset=0, time_range='medium_term').get('items', [])
    # niche_finds will be 'niche-artist': 'original-artist':
    niche_finds = {}
    
    for artist in top_artists:
        niches = find_niche_cousins(artist['id'], access_token, 20, 0, 3)
        for niche in niches:
            # Store niche artist object with reference to original artist
            niche_finds[niche['id']] = {'niche_artist': niche, 'original_artist': artist}
    
    return niche_finds
    

