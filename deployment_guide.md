# AWS Free Tier Deployment Guide for Global TimeSync API

This guide outlines the steps to deploy the Global TimeSync API to AWS Free Tier services.

## Prerequisites

1. AWS Account with Free Tier access
2. AWS CLI installed and configured
3. Git installed
4. Python 3.9+ installed

## Step 1: Prepare Your Environment Variables

Before deploying, make sure you've set up the following environment variables in your `.env` file:

```
FLASK_ENV=production
FLASK_APP=main.py
FLASK_DEBUG=0
JWT_SECRET=your_secure_random_string
DATABASE_URL=your_database_connection_string
```

**Important:** Never commit your `.env` file to version control. Instead, these values should be configured in AWS.

## Step 2: Create an RDS PostgreSQL Database Instance

1. Log in to the AWS Management Console
2. Navigate to RDS (Relational Database Service)
3. Click "Create Database"
4. Choose "Standard Create"
5. Select "PostgreSQL"
6. Choose "Free Tier" template
7. Set DB instance identifier (e.g., "timesync-db")
8. Set master username and password
9. Choose DB instance size (t2.micro for Free Tier)
10. Configure storage (20GB is within Free Tier limits)
11. Set database name (e.g., "timesync_db")
12. Under "Connectivity" section, select "Yes" for "Public Access" 
13. Create a new VPC security group
14. Click "Create database"

After creation, note the endpoint, port, username, password, and database name for the DATABASE_URL environment variable.

## Step 3: Deploy to Elastic Beanstalk

AWS Elastic Beanstalk provides a simple way to deploy and manage applications in AWS.

1. In your project directory, create an Elastic Beanstalk configuration file:

```
# .ebextensions/01_flask.config
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: main:app
  aws:elasticbeanstalk:application:environment:
    FLASK_ENV: production
    FLASK_APP: main.py
    FLASK_DEBUG: 0
    JWT_SECRET: your_secure_random_string
    DATABASE_URL: postgresql://username:password@your-db-endpoint:5432/timesync_db
    CACHE_TTL: 3600
    TIMEZONE_INFO_CACHE_TTL: 300
```

2. Initialize Elastic Beanstalk in your project:
```
eb init -p python-3.8 timesync-api --region us-east-1
```

3. Create an Elastic Beanstalk environment:
```
eb create timesync-api-env
```

4. Wait for the environment to be created and deploy the application

## Step 4: Configure Security

1. Navigate to EC2 > Security Groups
2. Find the security group for your EB environment
3. Add inbound rules for:
   - HTTP (port 80) from anywhere
   - HTTPS (port 443) from anywhere
   - Custom TCP (port 5000) from your security group only

## Step 5: Set Up a Custom Domain (Optional)

1. Register a domain in Route 53 or use an existing domain
2. Create a record set in Route 53 that points to your Elastic Beanstalk environment
3. Configure HTTPS with AWS Certificate Manager

## Step 6: Set Up CloudWatch Monitoring

1. In the Elastic Beanstalk console, go to your environment
2. Click on Monitoring
3. Configure basic alarms for:
   - High CPU utilization
   - High memory usage
   - Application error rates

## Step 7: Verify Deployment

1. Navigate to your Elastic Beanstalk URL
2. Test the API endpoints using the dashboard or tools like Postman
3. Monitor logs in CloudWatch

## Cost-Saving Tips for Free Tier

1. Use t2.micro instances which are included in Free Tier
2. Keep RDS storage under 20GB
3. Stop instances when not in use
4. Monitor your Free Tier usage in the AWS Billing Dashboard
5. Set up billing alerts to avoid unexpected charges

## Troubleshooting

1. Check EB logs: `eb logs`
2. SSH into your EB instance: `eb ssh`
3. Test database connectivity
4. Verify environment variables are set correctly
5. Check security group settings

## Scaling Considerations

When you need to scale beyond Free Tier:
1. Upgrade your database instance
2. Use auto-scaling for your EB environment
3. Consider adding a Redis cache (ElastiCache)
4. Implement CloudFront for content delivery

## CI/CD Pipeline (Future Enhancement)

For continuous deployment:
1. Set up AWS CodePipeline
2. Connect to your GitHub repository
3. Automate testing with AWS CodeBuild
4. Configure deployment to Elastic Beanstalk