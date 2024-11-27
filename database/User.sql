CREATE DATABASE TRENDNEST;
USE TRENDNEST;

-- Create 'user' table to store user details
CREATE TABLE user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    verification_token VARCHAR(36) DEFAULT NULL, -- UUID token for email verification
    is_verified BOOLEAN DEFAULT FALSE, -- Indicates if the user's email is verified
    role ENUM('user', 'admin', 'moderator') DEFAULT 'user', -- Default role is 'user'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
INSERT INTO `user`(`username`,`email`,`password`,`verification_token`,`is_verified`,`role`,`created_at`,`updated_at`) VALUES('Tias Pal','pal.tias2007@gmail.com','pbkdf2:sha256:1000000$NDb67MKOy3uvkMQX$1e093fc28a259d57f04cd683edc4f370a207e101019b2c33016cbcced5b0b085','2014007b-258c-4f2e-9a9c-88c3d8713edc',1,'admin','2024-11-19 22:16:01','2024-11-19 22:49:46');

-- Create 'user_activity' table to log user actions (e.g., login, account updates)
CREATE TABLE user_activity (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    action VARCHAR(50) NOT NULL, -- Description of the action
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE -- Cascade deletes with user table
);

-- Create 'user_sessions' table to track user session data
CREATE TABLE user_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_start TIMESTAMP NOT NULL,  -- When the session started
    session_duration INT NOT NULL,       -- Duration of the session in seconds
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE -- Link to user table
);

