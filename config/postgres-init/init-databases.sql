-- PostgreSQL initialization script for AI Stack
-- This script creates additional databases needed by services

-- Create N8N database
CREATE DATABASE n8n;
GRANT ALL PRIVILEGES ON DATABASE n8n TO postgres;

-- Create any other databases as needed
-- (Add more CREATE DATABASE statements here if needed)