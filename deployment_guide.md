# Render Deployment Guide for Global TimeSync API

This guide outlines the steps to deploy the Global TimeSync API to Render through GitHub.

## Prerequisites

1. GitHub account
2. Render account (free tier available)
3. Git installed
4. Python 3.9+ installed locally for development

## Step 1: Push Your Code to GitHub

1. Create a new GitHub repository
2. Initialize your local repository (if not already done):
   ```
   git init
   git add .
   git commit -m "Initial commit"
   ```
3. Add your GitHub repository as a remote and push your code:
   ```
   git remote add origin https://github.com/yourusername/global-timesync-api.git
   git branch -M main
   git push -u origin main
   ```

## Step 2: Set Up a Render Web Service

1. Log in to your Render dashboard
2. Click "New" and select "Web Service"
3. Connect your GitHub account if you haven't already
4. Select the repository with your Global TimeSync API code
5. Configure the following settings:
   - **Name**: `global-timesync-api` (or your preferred name)
   - **Environment**: Python
   - **Region**: Choose the region closest to your users
   - **Branch**: main (or your default branch)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --reuse-port main:app`
   - **Instance Type**: Free (for testing, upgrade for production)

## Step 3: Configure Environment Variables

In the Render dashboard for your web service, go to the "Environment" tab and add the following variables:

```
FLASK_ENV=production
FLASK_APP=main.py
FLASK_DEBUG=0
JWT_SECRET=your_secure_random_string
PORT=10000
TIMEZONE_INFO_CACHE_TTL=300
DEFAULT_CACHE_TTL=3600
```

For production, you'll want to add:
```
DATABASE_URL=postgresql://username:password@your-db-host:5432/timesync_db
```

## Step 4: Set Up a PostgreSQL Database (Optional)

1. In your Render dashboard, click "New" and select "PostgreSQL"
2. Configure the database:
   - **Name**: `timesync-db` (or your preferred name)
   - **Database**: `timesync_db`
   - **User**: Render will generate this for you
   - **Region**: Choose the same region as your web service
   - **Instance Type**: Free (for testing, upgrade for production)
3. After creation, Render will provide you with the database connection details
4. Update the `DATABASE_URL` environment variable in your web service with these details

## Step 5: Configure Automatic Deployments

Render automatically deploys your application when you push changes to your default branch. No additional configuration is needed for basic CI/CD.

## Step 6: Custom Domain Setup (Optional)

1. In the Render dashboard, go to your web service
2. Click on the "Settings" tab
3. Scroll to "Custom Domain"
4. Click "Add Custom Domain"
5. Follow the instructions to verify ownership and configure DNS settings

## Step 7: Verify Deployment

1. Once deployment is complete, Render will provide a URL for your application
2. Visit the URL to verify the application is running correctly
3. Test the API endpoints using the dashboard or tools like Postman
4. Monitor logs in the Render dashboard

## Troubleshooting

1. Check logs in the Render dashboard under the "Logs" tab
2. Verify environment variables are set correctly
3. If the application fails to start, check the build and start command logs
4. Ensure your `requirements.txt` file includes all necessary dependencies

## Scaling Considerations

When you need to scale beyond the free tier:
1. Upgrade to a paid plan for more resources
2. Consider adding a Redis cache for improved performance
3. Implement a CDN for static assets

## Render vs. Other Platforms

Render offers several advantages for this application:
1. Free tier for development and testing
2. Automatic HTTPS with free SSL certificates
3. Automatic deployments from GitHub
4. Built-in PostgreSQL database service
5. Simple scaling options as your application grows