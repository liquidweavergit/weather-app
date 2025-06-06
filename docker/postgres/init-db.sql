-- Temperature Display App - Database Initialization
-- This script runs once when the PostgreSQL container is first created

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS weather;
CREATE SCHEMA IF NOT EXISTS users;
CREATE SCHEMA IF NOT EXISTS cache;

-- Set timezone
SET timezone = 'UTC';

-- Create database user for application (if not exists)
DO $$ 
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_user') THEN
      CREATE ROLE app_user WITH LOGIN PASSWORD 'app_password';
   END IF;
END
$$;

-- Grant necessary permissions
GRANT CONNECT ON DATABASE temperature_app TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT CREATE ON SCHEMA public TO app_user;

-- Create initial schemas if needed
-- (Alembic will handle actual table creation)

-- Create application user (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'temperature_app_user') THEN
        CREATE ROLE temperature_app_user LOGIN PASSWORD 'app_password';
    END IF;
END
$$;

-- Grant permissions
GRANT USAGE ON SCHEMA weather TO temperature_app_user;
GRANT USAGE ON SCHEMA users TO temperature_app_user;
GRANT USAGE ON SCHEMA cache TO temperature_app_user;

GRANT CREATE ON SCHEMA weather TO temperature_app_user;
GRANT CREATE ON SCHEMA users TO temperature_app_user;
GRANT CREATE ON SCHEMA cache TO temperature_app_user;

-- Create basic tables for development
-- Weather cache table
CREATE TABLE IF NOT EXISTS weather.weather_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    temperature INTEGER NOT NULL,
    feels_like INTEGER,
    humidity INTEGER,
    pressure INTEGER,
    condition VARCHAR(100),
    uv_index INTEGER,
    wind_speed DECIMAL(5, 2),
    wind_direction INTEGER,
    visibility DECIMAL(5, 2),
    cached_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    api_source VARCHAR(50) DEFAULT 'openweathermap',
    CONSTRAINT valid_coordinates CHECK (
        latitude BETWEEN -90 AND 90 AND 
        longitude BETWEEN -180 AND 180
    )
);

-- User preferences table
CREATE TABLE IF NOT EXISTS users.preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) UNIQUE NOT NULL,
    preferred_units VARCHAR(10) DEFAULT 'metric' CHECK (preferred_units IN ('metric', 'imperial')),
    saved_locations JSONB DEFAULT '[]'::jsonb,
    theme VARCHAR(20) DEFAULT 'system' CHECK (theme IN ('light', 'dark', 'system')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Location cache table
CREATE TABLE IF NOT EXISTS cache.locations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_text VARCHAR(255) NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    city VARCHAR(255),
    country VARCHAR(100),
    country_code VARCHAR(5),
    formatted_address TEXT,
    cached_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_weather_cache_location ON weather.weather_cache (latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_weather_cache_expires ON weather.weather_cache (expires_at);
CREATE INDEX IF NOT EXISTS idx_weather_cache_cached_at ON weather.weather_cache (cached_at);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON users.preferences (user_id);
CREATE INDEX IF NOT EXISTS idx_user_preferences_updated ON users.preferences (updated_at);

CREATE INDEX IF NOT EXISTS idx_location_cache_query ON cache.locations (query_text);
CREATE INDEX IF NOT EXISTS idx_location_cache_location ON cache.locations (latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_location_cache_expires ON cache.locations (expires_at);

-- Grant table permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA weather TO temperature_app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA users TO temperature_app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA cache TO temperature_app_user;

-- Grant sequence permissions
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA weather TO temperature_app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA users TO temperature_app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA cache TO temperature_app_user;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for user preferences
DROP TRIGGER IF EXISTS update_user_preferences_updated_at ON users.preferences;
CREATE TRIGGER update_user_preferences_updated_at
    BEFORE UPDATE ON users.preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert some test data for development
INSERT INTO users.preferences (user_id, preferred_units, saved_locations, theme)
VALUES 
    ('test_user_1', 'metric', '[{"name": "San Francisco", "lat": 37.7749, "lon": -122.4194}]'::jsonb, 'light'),
    ('test_user_2', 'imperial', '[{"name": "New York", "lat": 40.7128, "lon": -74.0060}]'::jsonb, 'dark')
ON CONFLICT (user_id) DO NOTHING;

-- Log completion
INSERT INTO cache.locations (query_text, latitude, longitude, city, country, country_code, formatted_address, expires_at)
VALUES 
    ('san francisco', 37.7749, -122.4194, 'San Francisco', 'United States', 'US', 'San Francisco, CA, USA', CURRENT_TIMESTAMP + INTERVAL '1 hour'),
    ('new york', 40.7128, -74.0060, 'New York', 'United States', 'US', 'New York, NY, USA', CURRENT_TIMESTAMP + INTERVAL '1 hour')
ON CONFLICT DO NOTHING;

-- Create a view for active weather cache (non-expired)
CREATE OR REPLACE VIEW weather.active_weather_cache AS
SELECT *
FROM weather.weather_cache
WHERE expires_at > CURRENT_TIMESTAMP;

GRANT SELECT ON weather.active_weather_cache TO temperature_app_user;

-- Log database initialization
DO $$
BEGIN
    RAISE NOTICE 'Temperature Display App database initialized successfully';
    RAISE NOTICE 'Schemas created: weather, users, cache';
    RAISE NOTICE 'Extensions enabled: uuid-ossp, pg_stat_statements, btree_gin, btree_gist';
    RAISE NOTICE 'Application user: temperature_app_user (created with necessary permissions)';
END
$$; 