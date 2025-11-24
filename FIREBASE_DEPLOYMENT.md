# Firebase Functions Deployment Guide

This guide will help you deploy the Nichefy backend to Firebase Cloud Functions.

## Prerequisites

1. Firebase CLI installed: `npm install -g firebase-tools`
2. Firebase project created at [console.firebase.google.com](https://console.firebase.google.com)
3. Logged in: `firebase login`
4. Backend dependencies installed in `backend/functions/`

## Step-by-Step Deployment

### 1. Initialize Firebase (if not already done)

```bash
firebase init functions
```

Select:
- Use an existing project (or create new)
- Python as the language
- Yes to install dependencies now

### 2. Configure Environment Variables

Firebase Functions use Firebase Functions Config. Set environment variables:

```bash
firebase functions:config:set \
  spotify.client_id="your-client-id" \
  spotify.client_secret="your-client-secret" \
  spotify.redirect_uri="https://us-central1-your-project.cloudfunctions.net/nichefy_api/api/auth/callback" \
  frontend.url="https://your-app.vercel.app" \
  flask.secret_key="your-random-secret-key" \
  cors.origins="https://your-app.vercel.app,https://*.vercel.app"
```

**Or use Firebase Console:**
1. Go to Firebase Console > Functions > Configuration
2. Add environment variables in the format above

**Note:** After Firebase Functions v2, use `firebase functions:secrets:set` for sensitive data:

```bash
firebase functions:secrets:set SPOTIFY_CLIENT_SECRET
firebase functions:secrets:set FLASK_SECRET_KEY
```

### 3. Update Code to Read from Firebase Config

The code automatically reads from environment variables. Firebase Functions will inject:
- `SPOTIFY_CLIENT_ID` from config
- `SPOTIFY_CLIENT_SECRET` from config
- `FRONTEND_URL` from config
- `CORS_ORIGINS` from config
- `FLASK_SECRET_KEY` from config

### 4. Update Spotify App Settings

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Select your app
3. Click "Settings"
4. Add Redirect URI: `https://us-central1-your-project.cloudfunctions.net/nichefy_api/api/auth/callback`
   (Replace `us-central1` and `your-project` with your actual values)

### 5. Deploy to Firebase

```bash
firebase deploy --only functions
```

Or deploy a specific function:
```bash
firebase deploy --only functions:nichefy_api
```

### 6. Get Your Function URL

After deployment, Firebase will show you the function URL:
```
https://us-central1-your-project.cloudfunctions.net/nichefy_api
```

Use this URL in your frontend's `NEXT_PUBLIC_API_URL` environment variable.

## Local Testing

### 1. Set Up Local Environment

Create `.env.local` in `backend/functions/`:
```env
SPOTIFY_CLIENT_ID=your-client-id
SPOTIFY_CLIENT_SECRET=your-client-secret
SPOTIFY_REDIRECT_URI=http://localhost:5000/api/auth/callback
FRONTEND_URL=http://localhost:3000
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
FLASK_SECRET_KEY=local-dev-secret
```

### 2. Run Locally

```bash
cd backend/functions
python main.py
```

Or use Firebase emulator:
```bash
firebase emulators:start --only functions
```

## Configuration Reference

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SPOTIFY_CLIENT_ID` | Spotify App Client ID | (from Spotify Dashboard) |
| `SPOTIFY_CLIENT_SECRET` | Spotify App Client Secret | (from Spotify Dashboard) |
| `SPOTIFY_REDIRECT_URI` | OAuth callback URL | `https://us-central1-project.cloudfunctions.net/nichefy_api/api/auth/callback` |
| `FRONTEND_URL` | Frontend URL for redirects | `https://your-app.vercel.app` |
| `FLASK_SECRET_KEY` | Session encryption key | (random secure string) |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:3000` |
| `ALLOW_VERCEL_PREVIEWS` | Allow all `*.vercel.app` domains | `false` |
| `ENVIRONMENT` | Environment identifier | `development` |

## Troubleshooting

### CORS Errors

- Verify `CORS_ORIGINS` includes your frontend URL
- Check that `ALLOW_VERCEL_PREVIEWS=true` if using Vercel preview deployments
- Ensure `supports_credentials=True` is set in CORS config

### OAuth Redirect URI Errors

- Verify the redirect URI in Spotify Dashboard matches exactly
- Check that the function URL is correct (no trailing slash)
- Ensure the function is deployed and accessible

### Session Cookie Issues

- Verify `SESSION_COOKIE_SECURE=True` in production
- Check `SESSION_COOKIE_SAMESITE=None` for cross-domain cookies
- Ensure cookies are allowed by frontend CORS configuration

### Function Timeout

- Increase timeout in `firebase.json` or function decorator
- Optimize your niche finding algorithm if it takes too long

### Cold Start Issues

- Consider using min instances: `min_instances=1` in function options
- Optimize imports and initialization code

## Cost Optimization

- Use `max_instances` to limit concurrent executions
- Consider caching responses for frequently requested artists
- Monitor usage in Firebase Console

## Updating Configuration

To update environment variables after deployment:

```bash
firebase functions:config:set spotify.client_id="new-value"
firebase deploy --only functions
```

Or use Firebase Console > Functions > Configuration.

## Support

For issues:
- Check Firebase Functions logs: `firebase functions:log`
- Review deployment logs in Firebase Console
- Verify environment variables are set correctly
- Check Spotify app settings match redirect URI

