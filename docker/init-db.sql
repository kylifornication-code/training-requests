-- Chef's Training Kitchen - Database Initialization
-- This script sets up the development database with proper permissions

-- Create the database if it doesn't exist
SELECT 'CREATE DATABASE chef_kitchen_dev'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'chef_kitchen_dev')\gexec

-- Grant all privileges to the user
GRANT ALL PRIVILEGES ON DATABASE chef_kitchen_dev TO chef_user;

-- Set up extensions (if needed)
\c chef_kitchen_dev;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create a test user for development (optional)
-- This will be created by Django migrations, but we can prepare the structure