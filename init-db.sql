-- PlotTwist Database Initialization Script

-- Ensure we're using the correct database
\c plottwist;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For better text search

-- Create custom types if needed
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
        CREATE TYPE user_role AS ENUM ('user', 'admin', 'moderator');
    END IF;
END $$;

-- Grant all privileges to plottwist user
GRANT ALL PRIVILEGES ON DATABASE plottwist TO plottwist;
GRANT ALL ON SCHEMA public TO plottwist;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO plottwist;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO plottwist;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO plottwist;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO plottwist;

-- Create indexes for better performance (these will be created by SQLAlchemy too, but just in case)
-- Note: Tables will be created by SQLAlchemy migrations, these are just preparatory

-- Display database info
SELECT 'Database plottwist initialized successfully' as status;
SELECT current_database() as database_name;
SELECT current_user as connected_as;
SELECT version() as postgresql_version; 