# Vercel Deployment Guide

This guide will help you deploy the Nichefy frontend to Vercel.

## Prerequisites

1. A Vercel account ([sign up here](https://vercel.com/signup))
2. The backend deployed and accessible via a public URL:
   - **Firebase Cloud Functions** (recommended) - see [FIREBASE_DEPLOYMENT.md](./FIREBASE_DEPLOYMENT.md)
   - Railway, Render, Heroku, etc.
3. Environment variables configured

## Step-by-Step Deployment

### 1. Deploy Backend First

Before deploying the frontend, ensure your Flask backend is deployed and accessible. You can deploy it to:
- **Firebase Cloud Functions** (recommended) - see [FIREBASE_DEPLOYMENT.md](./FIREBASE_DEPLOYMENT.md)
- **Railway**: [railway.app](https://railway.app)
- **Render**: [render.com](https://render.com)
- **Heroku**: [heroku.com](https://heroku.com)
- **Fly.io**: [fly.io](https://fly.io)

Make sure your backend:
- Has CORS configured to allow requests from your Vercel domain
- Is accessible via HTTPS
- Has all environment variables set (Spotify credentials, etc.)
- For Firebase Functions: URL format is `https://region-project.cloudfunctions.net/nichefy_api`

### 2. Update Backend CORS Configuration

Update `backend/app.py` to include your Vercel domain in the CORS origins:

```python
CORS(app, origins=[
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "https://your-app-name.vercel.app",  # Add your Vercel URL
    "https://*.vercel.app"  # Or allow all Vercel preview deployments
], supports_credentials=True)
```

Also update the Spotify redirect URI in your `.env`:
```
SPOTIFY_REDIRECT_URI=https://your-backend-url.com/api/auth/callback
```

And add this URI to your Spotify app settings in the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).

### 3. Deploy to Vercel

#### Option A: Deploy via Vercel CLI

1. Install Vercel CLI:
```bash
npm i -g vercel
```

2. Navigate to the project root:
```bash
cd "path/to/Indie Matcher"
```

3. Login to Vercel:
```bash
vercel login
```

4. Deploy:
```bash
vercel
```

5. Follow the prompts:
   - Set up and deploy? **Yes**
   - Which scope? Select your account
   - Link to existing project? **No** (or Yes if you've deployed before)
   - Project name: Enter a name or press Enter for default
   - Directory: **frontend**
   - Override settings? **No**

#### Option B: Deploy via GitHub (Recommended)

1. Push your code to GitHub

2. Go to [vercel.com](https://vercel.com) and click "Add New Project"

3. Import your GitHub repository

4. Configure the project:
   - **Framework Preset**: Next.js (auto-detected)
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (auto-filled)
   - **Output Directory**: `.next` (auto-filled)
   - **Install Command**: `npm install` (auto-filled)

5. Add Environment Variables:
   - Click "Environment Variables"
   - Add: `NEXT_PUBLIC_API_URL` = `https://your-backend-url.com`

6. Click "Deploy"

### 4. Configure Environment Variables

In your Vercel project settings, add the following environment variables:

**Required:**
- `NEXT_PUBLIC_API_URL`: Your deployed backend URL (e.g., `https://your-backend.railway.app`)

**Example:**
```
NEXT_PUBLIC_API_URL=https://nichefy-backend.railway.app
```

**Note:** 
- `NEXT_PUBLIC_` prefix makes the variable available in the browser
- Do NOT include trailing slash in the URL
- For production and preview deployments, you may want to set different values

### 5. Update Production Domain (Optional)

If you have a custom domain:
1. Go to your project settings in Vercel
2. Navigate to "Domains"
3. Add your custom domain
4. Update your backend CORS to include the custom domain

### 6. Verify Deployment

1. Visit your Vercel deployment URL
2. Test the authentication flow
3. Test searching for artists
4. Test finding niche recommendations

## Troubleshooting

### CORS Errors

If you see CORS errors:
- Ensure your backend CORS configuration includes your Vercel domain
- Check that `supports_credentials=True` is set in your Flask CORS config

### Authentication Issues

If authentication doesn't work:
- Verify `SPOTIFY_REDIRECT_URI` in your backend matches your backend URL
- Check that the redirect URI is added to your Spotify app settings
- Ensure session cookies are configured correctly (check `SESSION_COOKIE_SECURE` and `SESSION_COOKIE_SAMESITE` in production)

### API Connection Issues

If API calls fail:
- Verify `NEXT_PUBLIC_API_URL` is set correctly in Vercel environment variables
- Check that your backend is accessible and running
- Review browser console and network tab for specific error messages

### Build Failures

If the build fails:
- Check that all dependencies are in `package.json`
- Ensure TypeScript errors are resolved
- Review build logs in Vercel dashboard

## Environment Variables Reference

### Frontend (Vercel)

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `https://your-backend.railway.app` |

### Backend (Railway/Render/etc.)

| Variable | Description | Example |
|----------|-------------|---------|
| `SPOTIFY_CLIENT_ID` | Spotify App Client ID | (from Spotify Dashboard) |
| `SPOTIFY_CLIENT_SECRET` | Spotify App Client Secret | (from Spotify Dashboard) |
| `SPOTIFY_REDIRECT_URI` | OAuth callback URL | `https://your-backend.com/api/auth/callback` |
| `FLASK_SECRET_KEY` | Session encryption key | (random secure string) |

## Additional Notes

- Vercel automatically handles Next.js builds and deployments
- Preview deployments are created for every push to branches (great for testing!)
- Environment variables can be set per environment (Production, Preview, Development)
- The frontend uses serverless functions if you later add API routes to Next.js

## Support

For issues specific to:
- **Vercel**: Check [Vercel Documentation](https://vercel.com/docs)
- **Next.js**: Check [Next.js Documentation](https://nextjs.org/docs)
- **Backend deployment**: Refer to your hosting provider's documentation

