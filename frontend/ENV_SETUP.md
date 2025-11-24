# Environment Variables Setup

## Frontend Environment Variables

### For Local Development

Create a `.env.local` file in the `frontend/` directory:

```env
# Optional: Backend API URL
# Leave empty to use Next.js rewrites (proxies to localhost:5000)
# Or set to your backend URL if running elsewhere
NEXT_PUBLIC_API_URL=
```

### For Vercel Deployment

In your Vercel project settings, add:

```
NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

**Important Notes:**
- `NEXT_PUBLIC_` prefix is required for client-side access
- Do NOT include trailing slash
- Do NOT include `/api` path - it will be added automatically
- Example: `https://nichefy-backend.railway.app` ✅
- Wrong: `https://nichefy-backend.railway.app/` ❌
- Wrong: `https://nichefy-backend.railway.app/api` ❌

### How It Works

1. **Development (no env var set)**: Uses Next.js rewrites to proxy `/api/*` requests to `http://localhost:5000/api/*`

2. **Production (env var set)**: Makes direct requests to `${NEXT_PUBLIC_API_URL}/api/*`

## Backend Environment Variables

See `backend/README.md` for backend environment variable setup.

