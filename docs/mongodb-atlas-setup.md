# MongoDB Atlas Setup Guide

## 1. Create MongoDB Atlas Account

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Click "Try Free" and create an account or sign in

## 2. Create a Cluster

1. Click "Build a Database"
2. Choose the FREE tier (M0 Sandbox)
3. Select your preferred cloud provider (AWS/Google Cloud/Azure)
4. Choose the region closest to your deployment
5. Click "Create"

## 3. Set Up Database Access

1. In the security menu, click "Database Access"
2. Click "Add New Database User"
3. Choose "Password" authentication
4. Create a username and password (save these securely)
5. Set user privileges to "Read and write to any database"
6. Click "Add User"

## 4. Configure Network Access

1. In the security menu, click "Network Access"
2. Click "Add IP Address"
3. For development: Click "Allow Access from Anywhere" (0.0.0.0/0)
   - Note: For production, restrict to specific IP addresses
4. Click "Confirm"

## 5. Get Connection String

1. Click "Connect" on your cluster
2. Choose "Connect your application"
3. Select "Python" as your driver
4. Copy the connection string
5. Replace `<password>` with your database user's password
6. Replace `myFirstDatabase` with your desired database name

## 6. Update Environment Variables

Add the following to your `.env` file:

```
MONGODB_URL=your_connection_string_here
MONGODB_DB_NAME=your_database_name
```

## Security Notes

- Never commit your MongoDB connection string to version control
- Use environment variables for sensitive information
- Restrict IP access in production
- Regularly rotate database user passwords
- Enable MongoDB Atlas backup for production databases
