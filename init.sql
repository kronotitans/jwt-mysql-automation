-- Initialize the database with the required table
CREATE DATABASE IF NOT EXISTS arkane_settings;
USE arkane_settings;

CREATE TABLE IF NOT EXISTS arkane_settings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    AccessToken TEXT,
    Type VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insert initial record
INSERT IGNORE INTO arkane_settings (AccessToken, Type) VALUES ('', 'Arkane');

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS demo;
USE demo;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data
INSERT IGNORE INTO users (username) VALUES 
('john_doe'),
('jane_smith'),
('bob_wilson'),
('alice_johnson'),
('charlie_brown'),
('sarah_connor'),
('mike_tyson'),
('emma_watson');

-- Show the data
SELECT * FROM users;
