# Deployment Guide

## Local Deployment

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Generate password hash and cookie key
python utils/generate_password_hash.py

# Configure secrets.toml (see README.md)

# Start dashboard
streamlit run dashboard/ui_frontend.py
```

## Render.com Deployment

### Prerequisites

1. GitHub account
2. Render.com account (free tier available)
3. Project pushed to GitHub repository

### Step-by-Step Deployment

#### 1. Prepare Repository

```bash
# Ensure all files are committed
git add .
git commit -m "Ready for deployment"
git push origin main
```

#### 2. Create Render Web Service

1. Log in to [Render.com](https://render.com)
2. Click **New** → **Web Service**
3. Connect your GitHub account if not already connected
4. Select your repository: `nifty-options-trader`

#### 3. Configure Service

**Basic Settings:**
- **Name**: `nifty-options-trader` (or your preferred name)
- **Region**: Choose closest to your location
- **Branch**: `main` (or your deployment branch)
- **Runtime**: `Python 3`

**Build & Deploy Settings:**
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `streamlit run dashboard/ui_frontend.py --server.port=$PORT --server.address=0.0.0.0`

#### 4. Environment Variables

Add the following as environment variables or use Render's secrets manager:

**Option A: Environment Variables (Recommended)**

Convert `secrets.toml` content to environment variables:

```
STREAMLIT_CREDENTIALS_NAMES=["Your Name"]
STREAMLIT_CREDENTIALS_USERNAMES=["your_username"]
STREAMLIT_CREDENTIALS_PASSWORDS=["$2b$12$HASHED_PASSWORD"]
STREAMLIT_COOKIE_NAME=nifty_auth
STREAMLIT_COOKIE_KEY=your_random_key_here
STREAMLIT_COOKIE_EXPIRY_DAYS=30
STREAMLIT_BROKER_TYPE=angel
STREAMLIT_BROKER_API_KEY=your_api_key
STREAMLIT_BROKER_ACCESS_TOKEN=your_access_token
STREAMLIT_BROKER_CLIENT_ID=your_client_id
STREAMLIT_BROKER_API_SECRET=your_api_secret
```

**Option B: Secrets File Upload**

Alternatively, you can:
1. Create `secrets.toml` directly in Render's environment
2. Upload via file system or use Render's file management

#### 5. Deploy

1. Click **Create Web Service**
2. Wait for build to complete (first deployment takes 5-10 minutes)
3. Your dashboard will be available at: `https://your-service-name.onrender.com`

### Post-Deployment

1. **Access Dashboard**: Visit the URL provided by Render
2. **Login**: Use credentials from `secrets.toml`
3. **Monitor**: Check Render dashboard for logs and metrics

### Updating Deployment

Any push to the connected branch will trigger automatic redeployment:

```bash
git add .
git commit -m "Update strategy parameters"
git push origin main
```

Render will automatically detect changes and redeploy.

## Other Cloud Platforms

### Heroku

1. Create `Procfile`:
```
web: streamlit run dashboard/ui_frontend.py --server.port=$PORT --server.address=0.0.0.0
```

2. Deploy via Heroku CLI or GitHub integration

### AWS/GCP/Azure

Similar deployment process:
1. Create Python runtime environment
2. Install dependencies
3. Run Streamlit with proper port binding
4. Configure environment variables
5. Set up reverse proxy (if needed)

## Production Considerations

### Security

- ✅ Use strong passwords and secure cookie keys
- ✅ Regularly rotate API keys and tokens
- ✅ Enable HTTPS (Render provides this automatically)
- ✅ Monitor access logs
- ✅ Keep dependencies updated

### Performance

- Monitor resource usage (CPU, memory)
- Consider upgrading plan for higher traffic
- Implement caching for frequently accessed data
- Optimize data loading in dashboard

### Monitoring

- Set up error alerts
- Monitor trade execution logs
- Track API rate limits
- Review performance metrics regularly

### Backup

- Export trade logs regularly
- Backup configuration files
- Version control all code changes
- Document any manual configuration changes

## Troubleshooting

### Build Failures

1. Check `requirements.txt` compatibility
2. Verify Python version (3.10+)
3. Review build logs for specific errors

### Runtime Errors

1. Check `logs/errors.log`
2. Verify all environment variables are set
3. Ensure broker credentials are valid
4. Review Streamlit logs in Render dashboard

### Authentication Issues

1. Verify password hash is correctly generated
2. Check cookie key is properly set
3. Ensure `secrets.toml` format is correct

### Broker Connection Issues

1. Verify API credentials are correct
2. Check broker API status
3. Review rate limiting
4. Test with broker's sandbox/test environment first

## Support

For deployment issues:
1. Review Render documentation
2. Check application logs
3. Verify configuration files
4. Test locally before deploying

---

**Note**: Always test deployment in a staging environment before production use.

