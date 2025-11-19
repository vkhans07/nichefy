'use client'

import { useState } from 'react'
import axios from 'axios'
import { Search, Music, ExternalLink, Loader2 } from 'lucide-react'

interface Artist {
  id: string
  name: string
  image: string | null
  popularity: number
  spotify_url: string
  genres: string[]
}

export default function Home() {
  const [artistName, setArtistName] = useState('')
  const [artistId, setArtistId] = useState('')
  const [accessToken, setAccessToken] = useState('')
  const [loading, setLoading] = useState(false)
  const [nicheArtists, setNicheArtists] = useState<Artist[]>([])
  const [error, setError] = useState('')

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!artistId || !accessToken) {
      setError('Please provide both Artist ID and Access Token')
      return
    }

    setLoading(true)
    setError('')
    setNicheArtists([])

    try {
      const response = await axios.post('http://localhost:5000/api/recommend/niche', {
        artist_id: artistId,
        access_token: accessToken
      })

      if (response.data.success) {
        setNicheArtists(response.data.artists)
      } else {
        setError('Failed to fetch recommendations')
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'An error occurred while fetching recommendations')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 p-4 md:p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-5xl md:text-6xl font-bold text-white mb-4 flex items-center justify-center gap-3">
            <Music className="w-12 h-12 md:w-16 md:h-16" />
            Nichefy
          </h1>
          <p className="text-xl text-gray-200">
            Discover niche artists similar to your favorite popular musicians
          </p>
        </div>

        {/* Search Form */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 md:p-8 mb-8 shadow-2xl">
          <form onSubmit={handleSearch} className="space-y-4">
            <div>
              <label htmlFor="artistName" className="block text-white font-semibold mb-2">
                Artist Name (for reference)
              </label>
              <input
                id="artistName"
                type="text"
                value={artistName}
                onChange={(e) => setArtistName(e.target.value)}
                placeholder="e.g., Taylor Swift"
                className="w-full px-4 py-3 rounded-lg bg-white/20 text-white placeholder-gray-300 border border-white/30 focus:outline-none focus:ring-2 focus:ring-purple-400"
              />
            </div>

            <div>
              <label htmlFor="artistId" className="block text-white font-semibold mb-2">
                Spotify Artist ID *
              </label>
              <input
                id="artistId"
                type="text"
                value={artistId}
                onChange={(e) => setArtistId(e.target.value)}
                placeholder="e.g., 06HL4z0CvFAxyc27GXpf02"
                required
                className="w-full px-4 py-3 rounded-lg bg-white/20 text-white placeholder-gray-300 border border-white/30 focus:outline-none focus:ring-2 focus:ring-purple-400"
              />
              <p className="text-sm text-gray-300 mt-1">
                Find it in the Spotify artist URL: spotify.com/artist/[ID]
              </p>
            </div>

            <div>
              <label htmlFor="accessToken" className="block text-white font-semibold mb-2">
                Spotify Access Token *
              </label>
              <input
                id="accessToken"
                type="password"
                value={accessToken}
                onChange={(e) => setAccessToken(e.target.value)}
                placeholder="Your Spotify API access token"
                required
                className="w-full px-4 py-3 rounded-lg bg-white/20 text-white placeholder-gray-300 border border-white/30 focus:outline-none focus:ring-2 focus:ring-purple-400"
              />
            </div>

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
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-500/20 border border-red-500 text-white px-6 py-4 rounded-lg mb-8">
            {error}
          </div>
        )}

        {/* Results */}
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
        {!loading && nicheArtists.length === 0 && !error && (
          <div className="text-center text-gray-300 py-12">
            <Music className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p>Enter an artist to discover niche recommendations</p>
          </div>
        )}
      </div>
    </main>
  )
}

