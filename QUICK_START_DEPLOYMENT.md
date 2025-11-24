# Quick Start Deployment Guide

This is a quick reference for deploying Nichefy to Vercel (frontend) and Firebase Functions (backend).

## Prerequisites Checklist

- [ ] Firebase project created
- [ ] Vercel account created
- [ ] Spotify app created at [developer.spotify.com](https://developer.spotify.com/dashboard)
- [ ] Firebase CLI installed: `npm install -g firebase-tools`
- [ ] Vercel CLI installed (optional): `npm install -g vercel`

## Step 1: Deploy Backend to Firebase Functions

### 1.1 Initialize Firebase

```bash
firebase login
firebase init functions
```

Select:
- Use existing project
- Python
- Yes to install dependencies

### 1.2 Set Environment Variables

```bash
firebase functions:config:set \
  spotify.client_id="YOUR_CLIENT_ID" \
  spotify.client_secret="YOUR_CLIENT_SECRET" \
  frontend.url="https://your-app.vercel.app" \
  flask.secret_key="RANDOM_SECRET_KEY" \
  cors.origins="https://your-app.vercel.app,https://*.vercel.app"
```

**Get your function URL after deployment:**
```
https://us-central1-YOUR-PROJECT.cloudfunctions.net/nichefy_api
```

Set redirect URI in Spotify Dashboard:
```
https://us-central1-YOUR-PROJECT.cloudfunctions.net/nichefy_api/api/auth/callback
```

### 1.3 Deploy

```bash
cd backend/functions
firebase deploy --only functions
```

## Step 2: Deploy Frontend to Vercel

### 2.1 Push to GitHub

```bash
git add .
git commit -m "Ready for deployment"
git push
```

### 2.2 Deploy via Vercel Dashboard

1. Go to [vercel.com](https://vercel.com)
2. Click "Add New Project"
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
5. Add Environment Variable:
   - Key: `NEXT_PUBLIC_API_URL`
   - Value: `https://us-central1-YOUR-PROJECT.cloudfunctions.net/nichefy_api`
6. Click "Deploy"

### 2.3 Or Deploy via CLI

```bash
cd frontend
vercel
# Follow prompts, set root directory to "frontend"
# Add environment variable: NEXT_PUBLIC_API_URL
```

## Step 3: Update Spotify Settings

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Select your app
3. Settings → Redirect URIs
4. Add:
   - `https://us-central1-YOUR-PROJECT.cloudfunctions.net/nichefy_api/api/auth/callback`
5. Save

## Step 4: Verify Deployment

1. Visit your Vercel URL
2. Test login flow
3. Test artist search
4. Test niche recommendations

## Troubleshooting

### CORS Errors
- Check `CORS_ORIGINS` includes your Vercel URL
- Verify `ALLOW_VERCEL_PREVIEWS=true` if using preview deployments

### OAuth Errors
- Verify redirect URI in Spotify Dashboard matches exactly
- Check environment variables are set correctly
- View Firebase Functions logs: `firebase functions:log`

### API Connection Errors
- Verify `NEXT_PUBLIC_API_URL` is set correctly in Vercel
- Check Firebase Function is deployed and accessible
- Test function URL directly in browser

## Environment Variables Summary

### Firebase Functions
- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`
- `SPOTIFY_REDIRECT_URI`
- `FRONTEND_URL`
- `CORS_ORIGINS`
- `FLASK_SECRET_KEY`

### Vercel (Frontend)
- `NEXT_PUBLIC_API_URL`

## Next Steps

- [ ] Set up custom domain (optional)
- [ ] Configure monitoring/analytics
- [ ] Set up CI/CD for automatic deployments
- [ ] Review Firebase Functions logs for optimization

## Support

For detailed guides:
- [FIREBASE_DEPLOYMENT.md](./FIREBASE_DEPLOYMENT.md) - Full Firebase setup
- [VERCEL_DEPLOYMENT.md](./VERCEL_DEPLOYMENT.md) - Full Vercel setup
- [DEPLOYMENT_BUGFIXES.md](./DEPLOYMENT_BUGFIXES.md) - All fixes applied

