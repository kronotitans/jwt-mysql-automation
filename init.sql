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

-- Create demo database and users table
CREATE DATABASE IF NOT EXISTS demo;
USE demo;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL
);

INSERT INTO users (username) VALUES ('alice'), ('bob'), ('charlie');
