# CORS Setup for Production Deployment

## Issue
The frontend deployed on Netlify/Vercel cannot access the backend API on Render due to CORS restrictions.

## Solution
The backend now supports dynamic CORS configuration via environment variables.

## Setup Instructions

### 1. On Render.com (Backend)

1. Go to your service dashboard: https://dashboard.render.com
2. Select your `app-newsbridge` service
3. Go to **Environment** tab
4. Add a new environment variable:
   - **Key**: `ALLOWED_ORIGINS`
   - **Value**: Your frontend URL(s), comma-separated
   
   Examples:
   ```
   https://app-react-newsbridge.netlify.app,http://localhost:3000,http://localhost:5173
   ```
   
   Or if you don't know the exact URL yet, you can temporarily use `*` to allow all origins (NOT recommended for production):
   ```
   *
   ```

5. Click **Save Changes**
6. Render will automatically redeploy your backend with the new CORS settings

### 2. Find Your Frontend URL

#### On Netlify:
1. Go to https://app.netlify.com
2. Select your site
3. The URL will be shown at the top (e.g., `https://your-site-name.netlify.app`)

#### On Vercel:
1. Go to https://vercel.com/dashboard
2. Select your project
3. The URL will be in the Domains section (e.g., `https://your-project.vercel.app`)

### 3. Update ALLOWED_ORIGINS

Once you have your frontend URL, update the `ALLOWED_ORIGINS` environment variable on Render with the actual URL.

## How It Works

The backend `main.py` now reads the `ALLOWED_ORIGINS` environment variable:

```python
# Get allowed origins from environment or use defaults
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else [
    "http://localhost:3000",
    "http://localhost:5173",  # Vite dev server
]

# Configure CORS with regex support for Netlify/Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origin_regex=r"https://.*\.netlify\.app$|https://.*\.vercel\.app$",
)
```

The `allow_origin_regex` provides a fallback to allow any Netlify or Vercel deployment URL.

## Testing

After deploying:

1. Open your frontend in a browser
2. Open the browser console (F12)
3. Check for CORS errors
4. The articles should load successfully

## Troubleshooting

### Still getting CORS errors?

1. Check that the environment variable is set correctly on Render
2. Verify the backend has been redeployed after setting the variable
3. Check the backend logs on Render for any errors
4. Make sure your frontend URL matches exactly (including https://)

### Want to see what origins are allowed?

Add this endpoint to `main.py`:

```python
@app.get("/cors-check")
async def cors_check():
    return {"allowed_origins": ALLOWED_ORIGINS}
```

Then visit: `https://app-newsbridge.onrender.com/cors-check`
