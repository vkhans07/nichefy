import spotipy

def find_niche_cousins(seed_artist_id, access_token, max_popularity=20, depth=0):
    """
    Recursively find niche artists (popularity <= max_popularity) related to a seed artist.
    
    Args:
        seed_artist_id: Spotify artist ID to start from
        access_token: Spotify API access token
        max_popularity: Maximum popularity score for niche artists (default: 20)
        depth: Current recursion depth (default: 0, max: 2)
    
    Returns:
        List of niche artist objects from Spotify API
    """
    sp = spotipy.Spotify(auth=access_token)
    
    try:
        related = sp.artist_related_artists(seed_artist_id)
    except Exception as e:
        print(f"Error fetching related artists: {e}")
        return []
    
    artists = related.get('artists', [])
    niche_finds = []
    potential_bridges = []
    
    for artist in artists:
        if artist['popularity'] <= max_popularity:
            niche_finds.append(artist)
        else:
            potential_bridges.append(artist)
    
    # If we don't have enough niche artists and haven't reached max depth, recurse
    if len(niche_finds) < 3 and depth < 2:
        # Sort by least popular (ascending)
        potential_bridges.sort(key=lambda x: x['popularity'])
        if potential_bridges:
            bridge_artist = potential_bridges[0]
            deeper_finds = find_niche_cousins(
                bridge_artist['id'], 
                access_token, 
                max_popularity, 
                depth + 1
            )
            niche_finds.extend(deeper_finds)
    
    return niche_finds

