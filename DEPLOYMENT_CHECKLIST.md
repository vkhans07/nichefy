# Deployment Checklist

Use this checklist to ensure everything is ready for Vercel deployment.

## Pre-Deployment

- [ ] Backend is deployed and accessible via public URL (HTTPS)
- [ ] Backend CORS configuration includes Vercel domain(s)
- [ ] Backend environment variables are set (Spotify credentials, Flask secret key)
- [ ] Spotify app redirect URI includes your backend callback URL
- [ ] Frontend code is pushed to GitHub (or ready for Vercel CLI)

## Vercel Configuration

- [ ] Create Vercel account or login
- [ ] Import project from GitHub (or use Vercel CLI)
- [ ] Set Root Directory to `frontend`
- [ ] Add environment variable `NEXT_PUBLIC_API_URL` pointing to backend
- [ ] Verify build settings (should auto-detect Next.js)

## Backend Updates Required

- [ ] Update CORS in `backend/app.py` to include Vercel domain
- [ ] Update `SPOTIFY_REDIRECT_URI` to use backend production URL
- [ ] Update `SESSION_COOKIE_SECURE = True` for HTTPS
- [ ] Update `SESSION_COOKIE_SAMESITE = 'None'` if cross-domain cookies needed

## Post-Deployment Testing

- [ ] Visit deployed frontend URL
- [ ] Test Spotify OAuth login flow
- [ ] Test artist search functionality
- [ ] Test niche artist recommendations
- [ ] Check browser console for errors
- [ ] Verify API calls are reaching backend

## Optional Enhancements

- [ ] Set up custom domain
- [ ] Configure preview deployments
- [ ] Set up monitoring/analytics
- [ ] Configure environment-specific variables (prod/preview/dev)

