# QuMail Render Deployment Guide

This guide will help you deploy your QuMail application to Render.com.

## Prerequisites

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **GitHub Repository**: Your QuMail code should be in a GitHub repository
3. **Environment Variables**: Prepare your configuration values

## Quick Deploy Options

### Option 1: Using render.yaml (Recommended)

1. **Fork/Upload to GitHub**: Ensure your QuMail code is in a GitHub repository
2. **Connect to Render**: 
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Render will automatically detect the `render.yaml` file

### Option 2: Manual Web Service Creation

1. **Create Web Service**:
   - Go to Render Dashboard
   - Click "New" → "Web Service"
   - Connect your GitHub repository

2. **Configure Service**:
   - **Name**: `qumail-app`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python qumail_client/app.py` or `gunicorn --config gunicorn.conf.py qumail_client.app:app`

## Required Environment Variables

Set these in your Render service settings:

### Essential Variables
```bash
# Flask Configuration
SECRET_KEY=your_randomly_generated_secret_key_here
FLASK_ENV=production
PORT=10000

# Database (will be auto-set if using Render PostgreSQL)
DATABASE_URL=postgresql://username:password@hostname:port/database

# Key Manager (for quantum encryption)
NEON_DB_HOST=your_neon_db_host
NEON_DB_NAME=your_neon_db_name
NEON_DB_USER=your_neon_db_user
NEON_DB_PASSWORD=your_neon_db_password
```

### Optional Variables (for full functionality)
```bash
# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SYSTEM_EMAIL=your_email@gmail.com
SYSTEM_EMAIL_PASSWORD=your_app_password

# Blockchain (Polygon Amoy Testnet)
POLYGON_RPC_URL=https://polygon-amoy.g.alchemy.com/v2/YOUR_API_KEY
PRIVATE_KEY=your_wallet_private_key
INTEGRITY_VERIFIER_CONTRACT=your_contract_address

# IPFS (Pinata)
PINATA_API_KEY=your_pinata_api_key
PINATA_SECRET_KEY=your_pinata_secret_key
PINATA_JWT=your_pinata_jwt_token
```

## Database Setup

### Option 1: Render PostgreSQL (Recommended)
1. **Create Database Service**:
   - Click "New" → "PostgreSQL"
   - Name: `qumail-db`
   - The `DATABASE_URL` will be automatically provided

### Option 2: External Database (Neon, Supabase, etc.)
1. **Get Connection String**: From your database provider
2. **Set DATABASE_URL**: In Render environment variables

## Deployment Steps

1. **Push Code to GitHub**:
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Deploy on Render**:
   - Follow Option 1 or 2 above
   - Set environment variables
   - Click "Create Web Service"

3. **Monitor Deployment**:
   - Check logs for any errors
   - Wait for "Live" status

## Post-Deployment Configuration

### 1. Database Initialization
The app will automatically create database tables on first run.

### 2. Test the Application
- Visit your Render URL (e.g., `https://qumail-app.onrender.com`)
- Register a new account
- Test basic functionality

### 3. Custom Domain (Optional)
- Go to service settings
- Add your custom domain
- Update DNS records as instructed

## Troubleshooting

### Common Issues

1. **Build Fails**:
   - Check `requirements.txt` for correct dependencies
   - Ensure Python version is 3.11 (see `runtime.txt`)

2. **App Won't Start**:
   - Check logs for specific errors
   - Verify environment variables are set
   - Ensure `PORT` environment variable is set

3. **Database Connection Issues**:
   - Verify `DATABASE_URL` format
   - Check database service is running
   - Ensure firewall allows connections

4. **Static Files Not Loading**:
   - CSS/JS files should be in `qumail_client/static/`
   - Templates should be in `qumail_client/templates/`

### Log Monitoring
```bash
# View logs in Render dashboard or via CLI
render logs --service qumail-app
```

## Performance Optimization

1. **Use Gunicorn**: Already configured in `Procfile`
2. **Enable Caching**: Set appropriate cache headers
3. **Optimize Database**: Use connection pooling
4. **Monitor Resources**: Check CPU and memory usage

## Security Considerations

1. **Environment Variables**: Never commit secrets to Git
2. **HTTPS**: Render provides SSL certificates automatically
3. **Database Security**: Use strong passwords and limit access
4. **Rate Limiting**: Consider implementing rate limiting for API endpoints

## Maintenance

### Updates
```bash
git push origin main  # Automatic deployment on push
```

### Scaling
- Upgrade Render plan for more resources
- Enable auto-scaling if needed

### Backups
- Enable automatic database backups in Render
- Consider additional backup strategies for critical data

## Support

- **Render Documentation**: [render.com/docs](https://render.com/docs)
- **QuMail Issues**: Create issues in your GitHub repository
- **Community**: Join Render community forums

## Cost Estimation

- **Web Service**: Free tier available (with limitations)
- **PostgreSQL**: Free tier: 1GB storage, 1 month retention
- **Paid Plans**: Start at $7/month for web service, $7/month for database

---

## Quick Commands Reference

```bash
# Local testing
python qumail_client/app.py

# Check dependencies
pip install -r requirements.txt

# Run with Gunicorn locally
gunicorn --config gunicorn.conf.py qumail_client.app:app

# Environment check
python -c "import os; print(f'PORT: {os.getenv(\"PORT\", \"Not set\")}')"
```