"""
Niche Artist Discovery Algorithm
Implements a recursive algorithm to find niche artists (low popularity) similar to a popular seed artist.
"""

from importlib import import_module
import os
import json
import re


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


def _query_perplexity_for_related_artists(artist_name, genres=None):
    """
    Query Perplexity API to find artists similar to the given artist.
    
    Args:
        artist_name: Name of the artist to find similar artists for
        genres: Optional list of genres to help refine the search
    
    Returns:
        List of artist names (strings) that are similar to the given artist
    """
    try:
        import requests
        
        perplexity_api_key = os.getenv('PERPLEXITY_API_KEY')
        if not perplexity_api_key:
            print("  ⚠️  PERPLEXITY_API_KEY not set, skipping Perplexity API call")
            return []
        
        # Construct the query - ask for lesser-known/niche artists similar to the given artist
        genre_context = f" in the {', '.join(genres[:3])} genre" if genres else ""
        query = f"List 20 artists similar to {artist_name}{genre_context}. Focus on lesser-known, indie, or niche artists rather than mainstream ones. Provide only artist names, one per line, without numbers or bullet points."
        
        # Perplexity API endpoint (using their chat completions endpoint)
        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Authorization": f"Bearer {perplexity_api_key}",
            "Content-Type": "application/json"
        }
        
        # Try multiple model names as fallbacks (in order of preference)
        model_names = [
            "sonar",  # Simple fallback that works
            "sonar-pro",  # Pro variant
            "llama-3.1-sonar-large-128k-online",  # Latest Llama 3.1 variant
            "llama-3.1-sonar-small-128k-online",  # Small variant
            "llama-3-sonar-large-32k-online",  # Legacy large variant
            "llama-3-sonar-small-32k-online",  # Legacy small variant
        ]
        
        response = None
        last_error = None
        
        for model_name in model_names:
            payload = {
                "model": model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a music expert specializing in discovering lesser-known and niche artists. When asked about similar artists, provide only artist names, one per line, without numbers, bullet points, or explanations. Prioritize indie, underground, or emerging artists over mainstream ones."
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                "temperature": 0.8,  # Slightly higher for more creative suggestions
                "max_tokens": 800  # Reduced since we're not asking for URLs
            }
            
            print(f"  → Querying Perplexity API (model: {model_name}) for artists similar to {artist_name}...")
            try:
                # Reduced timeout to 20 seconds to avoid socket hangup errors
                response = requests.post(url, headers=headers, json=payload, timeout=20)
                if response.status_code == 200:
                    break  # Success, use this response
                elif response.status_code == 400:
                    # Invalid model error, try next model
                    error_data = response.json() if response.text else {}
                    last_error = error_data.get('error', {}).get('message', response.text[:100])
                    print(f"    ⚠️  Model {model_name} not available, trying next...")
                    continue
                else:
                    # Other error, break and handle below
                    break
            except Exception as e:
                last_error = str(e)
                print(f"    ⚠️  Error with model {model_name}: {str(e)}")
                continue
        
        if not response or response.status_code != 200:
            error_msg = last_error or (response.text[:200] if response else "No response")
            print(f"  ⚠️  Perplexity API error: {response.status_code if response else 'No response'} - {error_msg}")
            return []
        
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        # Parse artist names from the response
        lines = content.split('\n')
        artist_names = []
        
        for line in lines:
            # Clean up the line
            line = line.strip()
            if not line or len(line) < 2:
                continue
            
            # Skip lines that are clearly not artist names
            line_lower = line.lower()
            if any(skip in line_lower for skip in ['artist', 'similar', 'genre', 'music', 'here are', 'here is', 'some', 'list of']):
                continue
            
            # Remove leading numbers, bullets, dashes
            name_part = re.sub(r'^[\d\-\*\.\s]+', '', line)
            # Remove trailing punctuation
            name_part = name_part.rstrip('.,;:')
            
            if name_part and len(name_part) > 1:
                artist_names.append(name_part)
        
        # Limit to top 30 artist names
        artist_names = artist_names[:30]
        print(f"  ✓ Perplexity returned {len(artist_names)} artist suggestions")
        
        return artist_names
        
    except ImportError:
        print("  ⚠️  requests module not available, skipping Perplexity API call")
        return []
    except Exception as e:
        print(f"  ⚠️  Error querying Perplexity API: {str(e)}")
        return []


def _search_spotify_for_artists(artist_names, sp, seed_artist_id=None, min_popularity=15, max_popularity=40):
    """
    Search Spotify for artist names and return full artist objects that match popularity criteria.
    Uses multiple search strategies to improve match rate.
    
    Args:
        artist_names: List of artist name strings to search for
        sp: Spotify client instance
        seed_artist_id: Optional artist ID to exclude from results
        min_popularity: Minimum popularity score
        max_popularity: Maximum popularity score
    
    Returns:
        List of artist objects from Spotify API
    """
    found_artists = []
    seen_ids = set()  # Track seen artist IDs to avoid duplicates
    
    for artist_name in artist_names:
        if not artist_name or len(artist_name.strip()) < 2:
            continue
            
        artist_name = artist_name.strip()
        matched = False
        
        # Try multiple search strategies
        search_queries = [
            f'artist:"{artist_name}"',  # Exact match with quotes
            artist_name,  # Simple search without quotes
            f'{artist_name} artist',  # Explicit artist search
        ]
        
        for query in search_queries:
            if matched:
                break
                
            try:
                # Search with more results to improve matching
                results = sp.search(q=query, type='artist', limit=10)
                artists = results.get('artists', {}).get('items', [])
                
                # First, try to find exact or close name matches
                for artist in artists:
                    # Skip if it's the seed artist
                    if seed_artist_id and artist['id'] == seed_artist_id:
                        continue
                    
                    # Skip if we already have this artist
                    if artist['id'] in seen_ids:
                        continue
                    
                    # Check if name is similar (case-insensitive, allow partial matches)
                    artist_name_lower = artist_name.lower()
                    spotify_name_lower = artist.get('name', '').lower()
                    
                    # Check for exact match or close match
                    is_match = (
                        artist_name_lower == spotify_name_lower or
                        artist_name_lower in spotify_name_lower or
                        spotify_name_lower in artist_name_lower
                    )
                    
                    if is_match:
                        # Check popularity range
                        popularity = artist.get('popularity', 0)
                        if min_popularity <= popularity <= max_popularity:
                            found_artists.append(artist)
                            seen_ids.add(artist['id'])
                            matched = True
                            # Don't break - continue to find more matches from this query
                
                # If we found matches, move to next artist name
                if matched:
                    break
                    
            except Exception as e:
                # Continue to next search query if this one fails
                continue
        
        # If no match found, log it for debugging (but don't spam)
        if not matched and len(artist_names) <= 5:
            print(f"    ⚠️  No match found for '{artist_name}' in popularity range {min_popularity}-{max_popularity}")
    
    return found_artists

def find_niche_cousins(seed_artist_id, access_token, max_popularity=40, depth=0, min_length=5, min_popularity=15, progress_callback=None):
    """
    Find niche artists (min_popularity <= popularity <= max_popularity) similar to a seed artist.
    
    Algorithm Strategy:
    1. Query Perplexity API to find artists similar to the seed artist (replacing deprecated /related-artists)
    2. Search Spotify for the suggested artist names and filter by popularity
    3. Separate them into "niche" (within popularity range) and "popular" (above max)
    4. If we found fewer niche artists than needed and haven't reached max depth:
       - Take the least popular artist from the "popular" list (closest to niche)
       - Recursively search their related artists using Perplexity
    5. Use Perplexity with more specific queries (including track names) as fallback
    6. Use genre search only as last resort
    
    Args:
        seed_artist_id: Spotify artist ID to start the search from
        access_token: Spotify API access token for authentication
        max_popularity: Maximum popularity score to be considered "niche" (default: 20)
                       Spotify popularity is 0-100, where 100 is most popular
        min_popularity: Minimum popularity score to be considered (default: 5)
                       Filters out artists that are too obscure
        depth: Current recursion depth (default: 0, max: 2)
               Prevents infinite recursion and excessive API calls
        min_length: Minimum number of niche artists to find (default: 5)
        progress_callback: Optional callback function(message, data) to send progress updates
    
    Returns:
        List of niche artist objects from Spotify API (each with id, name, popularity, etc.)
    """
    # Initialize Spotify API client with the provided access token.
    # Verify token is not None/empty
    if not access_token:
        raise Exception("Access token is required but was not provided")
    
    # Debug: Check token format (should be a string, not empty)
    if not isinstance(access_token, str) or len(access_token.strip()) == 0:
        raise Exception(f"Invalid access token format. Expected non-empty string, got: {type(access_token)}")
    
    # Initialize Spotipy client with access token
    # Spotipy expects either auth token string or auth_manager
    # For user tokens from OAuth, we pass the token string directly
    spotipy_module = _get_spotipy()
    sp = spotipy_module.Spotify(auth=access_token)
    
    niche_finds = []
    seen_artist_ids = set()  # Track seen artist IDs to prevent duplicates
    seen_artist_ids.add(seed_artist_id)  # Don't include the seed artist itself
    
    try:
        # First, get the seed artist's information to understand their genres
        seed_artist = sp.artist(seed_artist_id)
        seed_genres = seed_artist.get('genres', [])
        seed_name = seed_artist.get('name', '')
        
        print(f"✓ Searching for niche artists similar to: {seed_name} (genres: {', '.join(seed_genres[:3])})")
        
        if not seed_genres:
            print(f"⚠️  Artist {seed_artist_id} has no genres")
            seed_genres = []
        
        # Strategy 1: Use Perplexity API to find related artists (replacing deprecated /related-artists endpoint)
        try:
            print(f"  → Querying Perplexity API for related artists...")
            related_artist_data = _query_perplexity_for_related_artists(seed_name, seed_genres)
            
            if related_artist_data:
                print(f"  ✓ Perplexity suggested {len(related_artist_data)} artist names")
                # Search Spotify for these artists by name (filters by popularity automatically)
                found_artists = _search_spotify_for_artists(
                    related_artist_data, 
                    sp, 
                    seed_artist_id, 
                    min_popularity, 
                    max_popularity
                )
                
                if found_artists:
                    if progress_callback:
                        progress_callback("searching_spotify", {
                            "message": f"Searching Spotify for {len(related_artist_data)} artists...",
                            "count": len(related_artist_data)
                        })
                    print(f"  ✓ Found {len(found_artists)} matching artists on Spotify")
                    # Separate artists into niche and potential bridges
                    niche_finds_from_perplexity = []
                    potential_bridges = []
                    
                    for artist in found_artists:
                        # Skip duplicates
                        if artist['id'] in seen_artist_ids:
                            continue
                        seen_artist_ids.add(artist['id'])
                        
                        if min_popularity <= artist['popularity'] <= max_popularity:
                            niche_finds_from_perplexity.append(artist)
                        elif artist['popularity'] > max_popularity:
                            potential_bridges.append(artist)
                    
                    # Add niche artists found (already deduplicated)
                    niche_finds.extend(niche_finds_from_perplexity)
                    if progress_callback:
                        progress_callback("artists_found", {
                            "message": f"Found {len(niche_finds_from_perplexity)} niche artists",
                            "count": len(niche_finds_from_perplexity),
                            "total": len(niche_finds)
                        })
                    print(f"  → Found {len(niche_finds_from_perplexity)} niche artists (popularity {min_popularity}-{max_popularity})")
                    
                    # Recursive step: If we don't have enough niche artists, dig deeper
                    if len(niche_finds) < min_length and depth < 2 and potential_bridges:
                        # Sort potential bridges by popularity (ascending)
                        potential_bridges.sort(key=lambda x: x['popularity'])
                        
                        # Use the least popular artist as a "bridge" to find more niche artists
                        bridge_artist = potential_bridges[0]
                        
                        # Recursively search the bridge artist's related artists
                        try:
                            print(f"  → Recursively searching bridge artist: {bridge_artist['name']} (popularity: {bridge_artist['popularity']})")
                            deeper_finds = find_niche_cousins(
                                bridge_artist['id'],
                                access_token,
                                max_popularity,
                                depth + 1,
                                min_length - len(niche_finds),
                                min_popularity
                            )
                            # Add deeper finds, avoiding duplicates
                            added_count = 0
                            for artist in deeper_finds:
                                if artist['id'] not in seen_artist_ids:
                                    seen_artist_ids.add(artist['id'])
                                    niche_finds.append(artist)
                                    added_count += 1
                            print(f"  → Found {added_count} additional niche artists from bridge")
                        except Exception as e:
                            print(f"  ⚠️  Error in recursive search for bridge artist: {str(e)}")
                            pass
            else:
                print(f"  ⚠️  Perplexity API returned no artist suggestions")
        except Exception as e:
            error_msg = str(e)
            print(f"  ⚠️  Perplexity API query failed: {error_msg[:100]}")
            # Continue to fallback strategies if Perplexity doesn't work
        
        # Strategy 2: Use Perplexity API with more specific query as fallback
        if len(niche_finds) < min_length:
            try:
                print(f"  → Using Perplexity API with more specific query as fallback...")
                # Get artist's top tracks to provide more context
                top_tracks = sp.artist_top_tracks(seed_artist_id, country='US')
                track_names = [track['name'] for track in top_tracks.get('tracks', [])[:5]]  # Get more tracks
                
                # Create a more detailed query with track information, emphasizing niche artists
                tracks_context = f" known for songs like {', '.join(track_names[:3])}" if track_names else ""
                query_context = f"{seed_name}{tracks_context}"
                # Use the same function to get artist names
                related_artist_data = _query_perplexity_for_related_artists(query_context, seed_genres)
                
                if related_artist_data:
                    # Search Spotify for these artists by name (filters by popularity automatically)
                    found_artists = _search_spotify_for_artists(
                        related_artist_data, 
                        sp, 
                        seed_artist_id, 
                        min_popularity, 
                        max_popularity
                    )
                    
                    # Add to niche_finds, avoiding duplicates
                    added_count = 0
                    for artist in found_artists:
                        if artist['id'] not in seen_artist_ids:
                            seen_artist_ids.add(artist['id'])
                            niche_finds.append(artist)
                            added_count += 1
                            
                    print(f"  → Found {added_count} additional niche artists via Perplexity fallback")
            except Exception as e:
                error_str = str(e)
                print(f"  ⚠️  Error in Perplexity fallback query: {error_str}")
        
        # Strategy 3: Last resort - genre search (only if everything else failed)
        # NOTE: This returns general search results, not truly "related" artists
        # Only used when both related-artists and recommendations fail
        if len(niche_finds) < min_length and seed_genres:
            print(f"  ⚠️  Using genre search as last resort (results may not be directly related)...")
            for genre in seed_genres[:2]:  # Limit to top 2 genres
                try:
                    # Search for artists in this genre
                    results = sp.search(q=f'genre:"{genre}"', type='artist', limit=50)
                    artists = results.get('artists', {}).get('items', [])
                    
                    # Filter for niche artists with popularity in range and avoid duplicates
                    filtered_artists = [
                        a for a in artists
                        if min_popularity <= a['popularity'] <= max_popularity
                        and a['id'] != seed_artist_id
                        and a['id'] not in seen_artist_ids
                    ]
                    # Sort by popularity (ascending) to prioritize less popular artists
                    filtered_artists.sort(key=lambda x: x['popularity'])
                    
                    for artist in filtered_artists:
                        if artist['id'] not in seen_artist_ids:
                            seen_artist_ids.add(artist['id'])
                            niche_finds.append(artist)
                        if len(niche_finds) >= min_length * 2:
                            break
                    
                    if len(niche_finds) >= min_length:
                        break
                except Exception as e:
                    print(f"  ⚠️  Error searching genre '{genre}': {str(e)}")
                    continue
        
        # Sort by popularity (ascending) to prioritize less popular niche artists
        niche_finds.sort(key=lambda x: x['popularity'])
        
        print(f"✓ Found {len(niche_finds)} niche artists for {seed_name} (popularity range: {min_popularity}-{max_popularity})")
        return niche_finds[:min_length * 2]  # Return up to 2x min_length for variety
        
    except Exception as e:
        error_msg = str(e)
        print(f"✗ Error finding niche artists for {seed_artist_id}: {error_msg}")
        
        if '401' in error_msg or 'Unauthorized' in error_msg:
            raise Exception("Spotify access token expired or invalid. Please log in again.") from e
        else:
            # For other errors, return empty list to allow graceful degradation
            print(f"  → Returning empty list due to error")
            return []


def recommend_niche_for_top_artists(access_token, max_popularity = 20, min_popularity = 5):
    sp = _get_spotipy().Spotify(auth=access_token)

    #get top artists
    top_artists = sp.current_user_top_artists(limit = 8, offset=0, time_range='medium_term').get('items', [])
    # niche_finds will be 'niche-artist': 'original-artist':
    niche_finds = {}
    
    for artist in top_artists:
        niches = find_niche_cousins(artist['id'], access_token, max_popularity, 0, 3, min_popularity)
        for niche in niches:
            # Store niche artist object with reference to original artist
            niche_finds[niche['id']] = {'niche_artist': niche, 'original_artist': artist}
    
    return niche_finds
    

