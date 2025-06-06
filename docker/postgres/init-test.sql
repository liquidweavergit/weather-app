-- Temperature Display App - Test Database Initialization
-- This script sets up the test database with optimizations for testing

-- Create extensions (same as production but optimized for testing)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS weather;
CREATE SCHEMA IF NOT EXISTS users;
CREATE SCHEMA IF NOT EXISTS cache;

-- Set timezone
SET timezone = 'UTC';

-- Create test tables (simplified for faster testing)
-- Weather cache table
CREATE TABLE IF NOT EXISTS weather.weather_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    temperature INTEGER NOT NULL,
    feels_like INTEGER,
    humidity INTEGER,
    condition VARCHAR(100),
    cached_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    api_source VARCHAR(50) DEFAULT 'openweathermap'
);

-- User preferences table
CREATE TABLE IF NOT EXISTS users.preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) UNIQUE NOT NULL,
    preferred_units VARCHAR(10) DEFAULT 'metric' CHECK (preferred_units IN ('metric', 'imperial')),
    saved_locations JSONB DEFAULT '[]'::jsonb,
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
    cached_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Create minimal indexes for testing (fewer than production)
CREATE INDEX IF NOT EXISTS idx_weather_cache_location ON weather.weather_cache (latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_weather_cache_expires ON weather.weather_cache (expires_at);
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON users.preferences (user_id);
CREATE INDEX IF NOT EXISTS idx_location_cache_query ON cache.locations (query_text);

-- Insert test data for automated testing
INSERT INTO users.preferences (user_id, preferred_units, saved_locations)
VALUES 
    ('test_user_1', 'metric', '[{"name": "Test City", "lat": 40.7128, "lon": -74.0060}]'::jsonb),
    ('test_user_2', 'imperial', '[{"name": "Test Location", "lat": 37.7749, "lon": -122.4194}]'::jsonb),
    ('integration_test_user', 'metric', '[]'::jsonb)
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO cache.locations (query_text, latitude, longitude, city, country, expires_at)
VALUES 
    ('test city', 40.7128, -74.0060, 'Test City', 'Test Country', CURRENT_TIMESTAMP + INTERVAL '1 hour'),
    ('mock location', 37.7749, -122.4194, 'Mock Location', 'Mock Country', CURRENT_TIMESTAMP + INTERVAL '1 hour')
ON CONFLICT DO NOTHING;

-- Insert test weather data
INSERT INTO weather.weather_cache (latitude, longitude, temperature, feels_like, humidity, condition, expires_at, api_source)
VALUES 
    (40.7128, -74.0060, 20, 18, 65, 'Clear', CURRENT_TIMESTAMP + INTERVAL '5 minutes', 'mock_api'),
    (37.7749, -122.4194, 15, 12, 70, 'Cloudy', CURRENT_TIMESTAMP + INTERVAL '5 minutes', 'mock_api'),
    (51.5074, -0.1278, 10, 8, 80, 'Rainy', CURRENT_TIMESTAMP + INTERVAL '5 minutes', 'mock_api')
ON CONFLICT DO NOTHING;

-- Log test database initialization
DO $$
BEGIN
    RAISE NOTICE 'Test database initialized successfully';
    RAISE NOTICE 'Test data inserted for automated testing';
    RAISE NOTICE 'Schemas: weather, users, cache';
    RAISE NOTICE 'Test users: test_user_1, test_user_2, integration_test_user';
END
$$; 