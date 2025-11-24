/**
 * Nichefy Main Page Component
 * 
 * This is the main page of the Nichefy application. It provides a UI for:
 * - Logging in with Spotify OAuth
 * - Searching for artists by name
 * - Finding niche artists similar to the selected artist
 * - Displaying the results in a beautiful card-based layout
 */

'use client' // Next.js directive: This component runs on the client side (browser)

// React hooks for managing component state
import { useState, useEffect } from 'react'
// Axios: HTTP client for making API requests to the backend
import axios from 'axios'
// Lucide React: Icon library for UI icons
import { Search, Music, ExternalLink, Loader2, LogIn, LogOut, User, CheckCircle, X } from 'lucide-react'
// API utility functions for handling base URLs
import { getApiUrl } from '@/lib/api'

// Configure axios to include credentials for session cookies
axios.defaults.withCredentials = true

/**
 * TypeScript interface defining the structure of an Artist object
 * This ensures type safety when working with artist data
 */
interface Artist {
  id: string              // Spotify artist ID
  name: string            // Artist name
  image: string | null    // URL to artist image (or null if no image)
  popularity: number      // Spotify popularity score (0-100)
  spotify_url: string     // Link to artist's Spotify page
  genres: string[]        // Array of genre tags
}

/**
 * Main Home component - the entry point of the application
 */
export default function Home() {
  // React state hooks to manage form inputs and application state
  
  // Authentication state
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [checkingAuth, setCheckingAuth] = useState(true)
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [userProfile, setUserProfile] = useState<{
    id: string
    display_name: string
    email?: string
    image?: string | null
    country?: string
    product?: string
  } | null>(null)
  const [loginSuccess, setLoginSuccess] = useState(false)
  
  // Artist search state
  const [artistSearchQuery, setArtistSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<Artist[]>([])
  const [selectedArtist, setSelectedArtist] = useState<Artist | null>(null)
  const [searching, setSearching] = useState(false)
  
  // Loading state - true when API request is in progress
  const [loading, setLoading] = useState(false)
  
  // Array of niche artists returned from the API
  const [nicheArtists, setNicheArtists] = useState<Artist[]>([])
  
  // Error message to display if something goes wrong
  const [error, setError] = useState('')

  /**
   * Fetch user profile information from Spotify
   */
  const fetchUserProfile = async (token?: string | null) => {
    const tokenToUse = token || accessToken
    if (!tokenToUse) {
      console.log('No token available for fetching user profile')
      return
    }
    
    try {
      console.log('Fetching user profile...')
      const params: any = {}
      // Add access token to params if available (fallback if cookies don't work)
      if (tokenToUse) {
        params.access_token = tokenToUse
      }
      
      const response = await axios.get(getApiUrl('user/profile'), {
        params,
        withCredentials: true
      })
      
      console.log('User profile response:', response.data)
      if (response.data.success && response.data.user) {
        setUserProfile(response.data.user)
        console.log('User profile set:', response.data.user)
      }
    } catch (err: any) {
      // Log error but don't fail completely - user profile is not critical
      console.error('Failed to fetch user profile:', err.response?.data || err.message)
    }
  }

  // Check authentication status on component mount
  useEffect(() => {
    const initializeAuth = async () => {
      // Check URL parameters for OAuth callback
      const params = new URLSearchParams(window.location.search)
      const loggedIn = params.get('logged_in')
      const errorParam = params.get('error')
      
      console.log('Initializing auth, URL params:', { loggedIn, errorParam })
      
      if (loggedIn === 'true') {
        console.log('Login success detected, checking auth status...')
        setError('')
        setLoginSuccess(true)
        
        // Check if token is in URL (fallback for localhost development)
        const tokenFromUrl = params.get('token')
        if (tokenFromUrl) {
          console.log('Token found in URL, using it directly')
          setAccessToken(tokenFromUrl)
          setIsAuthenticated(true)
          await fetchUserProfile(tokenFromUrl)
        } else {
          // Small delay to ensure session cookie is set
          await new Promise(resolve => setTimeout(resolve, 100))
          // Check auth status from session
          await checkAuthStatus()
        }
        
        // Clean up URL (remove both logged_in and token params)
        window.history.replaceState({}, '', window.location.pathname)
        // Hide success message after 5 seconds
        setTimeout(() => setLoginSuccess(false), 5000)
      } else if (errorParam) {
        const error = errorParam
        const details = params.get('details') || ''
        
        console.error('Login error detected:', error, details)
        
        let errorMessage = `Login failed: ${error}`
        
        // Provide helpful message for redirect URI errors
        if (error.includes('redirect_uri') || error.includes('invalid') || details.includes('redirect_uri')) {
          errorMessage = `Invalid Redirect URI Error\n\n${details || error}\n\n` +
            `To fix this:\n` +
            `1. Go to https://developer.spotify.com/dashboard\n` +
            `2. Select your app\n` +
            `3. Click "Settings"\n` +
            `4. Scroll to "Redirect URIs"\n` +
            `5. Add exactly: http://localhost:5000/api/auth/callback\n` +
            `6. Click "Add" and "Save"\n` +
            `7. Try logging in again`
        }
        
        setError(errorMessage)
        // Clean up URL
        window.history.replaceState({}, '', window.location.pathname)
      } else {
        // Normal page load - just check auth status
        console.log('Normal page load, checking auth status...')
        await checkAuthStatus()
      }
    }
    
    initializeAuth()
  }, [])

  /**
   * Check if user is authenticated with Spotify
   */
  const checkAuthStatus = async () => {
    try {
      setCheckingAuth(true)
      console.log('Checking auth status...')
      const response = await axios.get(getApiUrl('auth/status'), {
        withCredentials: true
      })
      console.log('Auth status response:', response.data)
      const authenticated = response.data.authenticated
      setIsAuthenticated(authenticated)
      if (authenticated && response.data.access_token) {
        const token = response.data.access_token
        console.log('User is authenticated, setting token and fetching profile...')
        setAccessToken(token)
        // Fetch user profile when authenticated
        await fetchUserProfile(token)
      } else {
        console.log('User is not authenticated')
        setAccessToken(null)
        setSelectedArtist(null)
        setNicheArtists([])
        setUserProfile(null)
      }
    } catch (err: any) {
      console.error('Error checking auth status:', err)
      setIsAuthenticated(false)
      setAccessToken(null)
      setUserProfile(null)
    } finally {
      setCheckingAuth(false)
    }
  }

  /**
   * Initiate Spotify OAuth login
   */
  const handleLogin = async () => {
    try {
      const response = await axios.get(getApiUrl('auth/login'))
      if (response.data.auth_url) {
        // Redirect to Spotify authorization page
        window.location.href = response.data.auth_url
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to initiate login')
    }
  }

  /**
   * Logout user
   */
  const handleLogout = async () => {
    try {
      await axios.post(getApiUrl('auth/logout'), {}, {
        withCredentials: true
      })
      setIsAuthenticated(false)
      setAccessToken(null)
      setUserProfile(null)
      setSelectedArtist(null)
      setNicheArtists([])
      setSearchResults([])
      setArtistSearchQuery('')
      setError('')
      setLoginSuccess(false)
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to logout')
    }
  }

  /**
   * Search for artists by name
   */
  const handleArtistSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!artistSearchQuery.trim()) {
      setError('Please enter an artist name to search')
      return
    }

    setSearching(true)
    setError('')
    setSearchResults([])

    try {
      const params: any = { q: artistSearchQuery }
      // Add access token to params if available (fallback if cookies don't work)
      if (accessToken) {
        params.access_token = accessToken
      }
      
      const response = await axios.get(getApiUrl('search/artists'), {
        params,
        withCredentials: true
      })

      if (response.data.success) {
        setSearchResults(response.data.artists)
        if (response.data.artists.length === 0) {
          setError('No artists found. Try a different search term.')
        }
      } else {
        setError('Failed to search for artists')
      }
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError('Not authenticated. Please log in with Spotify.')
        setIsAuthenticated(false)
      } else {
        setError(err.response?.data?.error || 'An error occurred while searching for artists')
      }
    } finally {
      setSearching(false)
    }
  }

  /**
   * Select an artist from search results
   */
  const selectArtist = (artist: Artist) => {
    setSelectedArtist(artist)
    setSearchResults([])
    setArtistSearchQuery(artist.name)
    setNicheArtists([])
  }

  /**
   * Handle form submission - search for niche artists
   */
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!selectedArtist) {
      setError('Please select an artist from the search results')
      return
    }

    setLoading(true)
    setError('')
    setNicheArtists([])

    try {
      // Make POST request to backend API endpoint
      const requestBody: any = { artist_id: selectedArtist.id }
      // Add access token to body if available (fallback if cookies don't work)
      if (accessToken) {
        requestBody.access_token = accessToken
      }
      
      const response = await axios.post(getApiUrl('recommend/niche'), requestBody, {
        withCredentials: true
      })

      // Check if the API request was successful
      if (response.data.success) {
        setNicheArtists(response.data.artists)
        if (response.data.artists.length === 0) {
          setError('No niche artists found. Try a different artist.')
        }
      } else {
        setError('Failed to fetch recommendations')
      }
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError('Not authenticated. Please log in with Spotify.')
        setIsAuthenticated(false)
      } else {
        setError(err.response?.data?.error || 'An error occurred while fetching recommendations')
      }
    } finally {
      setLoading(false)
    }
  }

  /**
   * Render the UI
   */
  return (
    <main className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 p-4 md:p-8">
      {/* Content wrapper with max width for better readability on large screens */}
      <div className="max-w-6xl mx-auto">
        {/* Header Section */}
        <div className="text-center mb-8">
          {/* App title with music icon */}
          <h1 className="text-5xl md:text-6xl font-bold text-white mb-4 flex items-center justify-center gap-3">
            <Music className="w-12 h-12 md:w-16 md:h-16" />
            Nichefy
          </h1>
          {/* Subtitle describing what the app does */}
          <p className="text-xl text-gray-200">
            Discover niche artists similar to your favorite popular musicians
          </p>
        </div>

        {/* Success Message Display */}
        {loginSuccess && isAuthenticated && (
          <div className="bg-green-500/20 border border-green-500 text-white px-6 py-4 rounded-lg mb-8 flex items-center justify-between animate-in fade-in slide-in-from-top-2">
            <div className="flex items-center gap-3">
              <CheckCircle className="w-6 h-6 text-green-400" />
              <div>
                <div className="font-semibold">Successfully logged in!</div>
                {userProfile && (
                  <div className="text-sm text-gray-200">
                    Welcome back, {userProfile.display_name || 'there'}! 🎵
                  </div>
                )}
              </div>
            </div>
            <button
              onClick={() => setLoginSuccess(false)}
              className="text-white/70 hover:text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        )}

        {/* Authentication Section */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 mb-8 shadow-2xl">
          {checkingAuth ? (
            <div className="flex items-center justify-center gap-2 text-white">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Checking authentication...</span>
            </div>
          ) : isAuthenticated ? (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3 text-white">
                {userProfile?.image ? (
                  <img
                    src={userProfile.image}
                    alt={userProfile.display_name || 'User'}
                    className="w-10 h-10 rounded-full object-cover"
                  />
                ) : (
                  <div className="w-10 h-10 rounded-full bg-purple-600 flex items-center justify-center">
                    <User className="w-6 h-6" />
                  </div>
                )}
                <div>
                  <div className="font-semibold">
                    {userProfile?.display_name || 'Logged in with Spotify'}
                  </div>
                  {userProfile?.email && (
                    <div className="text-sm text-gray-300">{userProfile.email}</div>
                  )}
                </div>
              </div>
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </button>
            </div>
          ) : (
            <div className="text-center">
              <p className="text-white mb-4">Please log in with Spotify to continue</p>
              <button
                onClick={handleLogin}
                className="inline-flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
              >
                <LogIn className="w-5 h-5" />
                Login with Spotify
              </button>
            </div>
          )}
        </div>

        {/* Error Message Display */}
        {error && (
          <div className="bg-red-500/20 border border-red-500 text-white px-6 py-4 rounded-lg mb-8 whitespace-pre-line">
            <div className="font-semibold mb-2">Error:</div>
            <div>{error}</div>
          </div>
        )}

        {/* Search Form Section - Only show if authenticated */}
        {isAuthenticated && (
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 md:p-8 mb-8 shadow-2xl">
            {/* Artist Search Form */}
            <form onSubmit={handleArtistSearch} className="space-y-4 mb-6">
              <div>
                <label htmlFor="artistSearch" className="block text-white font-semibold mb-2">
                  Search for an Artist
                </label>
                <div className="flex gap-2">
                  <input
                    id="artistSearch"
                    type="text"
                    value={artistSearchQuery}
                    onChange={(e) => {
                      setArtistSearchQuery(e.target.value)
                      setSelectedArtist(null)
                      setSearchResults([])
                    }}
                    placeholder="e.g., Taylor Swift, The Beatles, Radiohead"
                    className="flex-1 px-4 py-3 rounded-lg bg-white/20 text-white placeholder-gray-300 border border-white/30 focus:outline-none focus:ring-2 focus:ring-purple-400"
                  />
                  <button
                    type="submit"
                    disabled={searching || !artistSearchQuery.trim()}
                    className="bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    {searching ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <Search className="w-5 h-5" />
                    )}
                    Search
                  </button>
                </div>
              </div>
            </form>

            {/* Search Results */}
            {searchResults.length > 0 && (
              <div className="mb-6">
                <h3 className="text-white font-semibold mb-3">Select an artist:</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {searchResults.map((artist) => (
                    <button
                      key={artist.id}
                      onClick={() => selectArtist(artist)}
                      className={`bg-white/10 hover:bg-white/20 rounded-lg p-4 text-left transition-all ${
                        selectedArtist?.id === artist.id ? 'ring-2 ring-purple-400 bg-white/20' : ''
                      }`}
                    >
                      {artist.image && (
                        <img
                          src={artist.image}
                          alt={artist.name}
                          className="w-full h-32 object-cover rounded-lg mb-2"
                        />
                      )}
                      <h4 className="text-white font-semibold">{artist.name}</h4>
                      <p className="text-gray-300 text-sm">Popularity: {artist.popularity}</p>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Selected Artist Display */}
            {selectedArtist && (
              <div className="mb-6 p-4 bg-purple-600/20 rounded-lg border border-purple-400/30">
                <div className="flex items-center gap-4">
                  {selectedArtist.image && (
                    <img
                      src={selectedArtist.image}
                      alt={selectedArtist.name}
                      className="w-16 h-16 rounded-full object-cover"
                    />
                  )}
                  <div className="flex-1">
                    <h3 className="text-white font-bold text-lg">{selectedArtist.name}</h3>
                    <p className="text-gray-300 text-sm">Ready to find niche artists similar to this one</p>
                  </div>
                </div>
              </div>
            )}

            {/* Find Niche Artists Button */}
            {selectedArtist && (
              <form onSubmit={handleSearch}>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-bold py-3 px-6 rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Finding Niche Artists...
                    </>
                  ) : (
                    <>
                      <Search className="w-5 h-5" />
                      Find Niche Artists
                    </>
                  )}
                </button>
              </form>
            )}
          </div>
        )}

        {/* Results Section */}
        {nicheArtists.length > 0 && (
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-white mb-6">
              Found {nicheArtists.length} Niche Artist{nicheArtists.length !== 1 ? 's' : ''}
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {nicheArtists.map((artist) => (
                <div
                  key={artist.id}
                  className="bg-white/10 backdrop-blur-lg rounded-xl p-6 hover:bg-white/20 transition-all duration-200 shadow-lg"
                >
                  {artist.image && (
                    <img
                      src={artist.image}
                      alt={artist.name}
                      className="w-full h-48 object-cover rounded-lg mb-4"
                    />
                  )}
                  <h3 className="text-xl font-bold text-white mb-2">{artist.name}</h3>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm text-gray-300">
                      Popularity: {artist.popularity}
                    </span>
                    <a
                      href={artist.spotify_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-purple-400 hover:text-purple-300 transition-colors"
                    >
                      <ExternalLink className="w-5 h-5" />
                    </a>
                  </div>
                  {artist.genres.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {artist.genres.slice(0, 3).map((genre, idx) => (
                        <span
                          key={idx}
                          className="text-xs bg-purple-600/30 text-purple-200 px-2 py-1 rounded-full"
                        >
                          {genre}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {isAuthenticated && !loading && nicheArtists.length === 0 && !error && !selectedArtist && (
          <div className="text-center text-gray-300 py-12">
            <Music className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p>Search for an artist to discover niche recommendations</p>
          </div>
        )}
      </div>
    </main>
  )
}
