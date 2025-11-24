# Deployment Bug Fixes

This document summarizes all the bug fixes applied for Vercel and Firebase deployment.

## Issues Fixed

### 1. Firebase Functions Integration
**Problem:** Flask app was not properly exported as a Firebase Cloud Function.

**Fix:** 
- Added proper Firebase Functions wrapper using `@https_fn.on_request` decorator
- Wrapped Flask app to handle requests through Firebase Functions
- Added CORS configuration in Firebase Functions decorator

**Files Changed:**
- `backend/functions/main.py` - Added Firebase Functions export
- `backend/functions/requirements.txt` - Added all required dependencies

### 2. CORS Configuration
**Problem:** CORS was hardcoded to localhost only, preventing production deployments.

**Fix:**
- Added `CORS_ORIGINS` environment variable support
- Allows comma-separated list of allowed origins
- Added `ALLOW_VERCEL_PREVIEWS` option for Vercel preview deployments
- CORS now configurable via environment variables

**Files Changed:**
- `backend/functions/main.py` - Dynamic CORS configuration

### 3. Hardcoded Redirect URLs
**Problem:** OAuth callback redirects were hardcoded to `localhost:3000`.

**Fix:**
- Added `FRONTEND_URL` environment variable
- All redirect URLs now use environment variable
- Automatically constructs Firebase Function URL for redirect URI

**Files Changed:**
- `backend/functions/main.py` - Dynamic frontend URL configuration

### 4. Session Cookie Configuration
**Problem:** Session cookies not configured properly for production (cross-domain).

**Fix:**
- `SESSION_COOKIE_SECURE` now set to `True` in production
- `SESSION_COOKIE_SAMESITE` set to `None` for cross-domain cookies
- Automatically detects production environment

**Files Changed:**
- `backend/functions/main.py` - Dynamic session cookie configuration

### 5. Missing Dependencies
**Problem:** Firebase Functions `requirements.txt` was incomplete.

**Fix:**
- Added all required dependencies: Flask, flask-cors, spotipy, firebase-admin, python-dotenv, gunicorn

**Files Changed:**
- `backend/functions/requirements.txt` - Complete dependency list

### 6. Firebase Configuration Missing
**Problem:** No `firebase.json` configuration file.

**Fix:**
- Created `firebase.json` with proper configuration
- Set Python 3.11 runtime
- Configured ignore patterns for deployment

**Files Changed:**
- `firebase.json` - New file created

### 7. Environment Variable Documentation
**Problem:** No clear documentation for Firebase Functions environment variables.

**Fix:**
- Created `FIREBASE_DEPLOYMENT.md` with comprehensive guide
- Added `.env.example` reference in documentation
- Documented all required and optional environment variables

**Files Changed:**
- `FIREBASE_DEPLOYMENT.md` - New deployment guide

## Testing Checklist

After deployment, verify:

- [ ] Backend is accessible via HTTPS
- [ ] CORS allows requests from frontend domain
- [ ] OAuth login flow works correctly
- [ ] Session cookies are set and readable
- [ ] All API endpoints respond correctly
- [ ] Environment variables are set correctly
- [ ] Redirect URIs match in Spotify app settings

## Common Issues and Solutions

### CORS Errors
- Verify `CORS_ORIGINS` includes your frontend URL
- Check browser console for specific CORS error
- Ensure `supports_credentials=True` is set

### OAuth Redirect URI Mismatch
- Verify redirect URI in Spotify Dashboard matches exactly
- Check environment variable `SPOTIFY_REDIRECT_URI`
- Ensure no trailing slashes in URLs

### Session Cookies Not Working
- Verify `SESSION_COOKIE_SECURE=True` in production
- Check `SESSION_COOKIE_SAMESITE=None` for cross-domain
- Ensure frontend sends credentials with requests (`withCredentials: true`)

### Function Not Found
- Verify function is deployed: `firebase functions:list`
- Check function URL format matches expected pattern
- Ensure function name matches in deployment

## Next Steps

1. Deploy backend to Firebase Functions (see `FIREBASE_DEPLOYMENT.md`)
2. Set all environment variables in Firebase Console
3. Update Spotify app redirect URI
4. Deploy frontend to Vercel (see `VERCEL_DEPLOYMENT.md`)
5. Set `NEXT_PUBLIC_API_URL` in Vercel environment variables
6. Test all functionality

