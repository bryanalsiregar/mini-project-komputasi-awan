CREATE DATABASE IF NOT EXISTS db_belajar_bareng;
USE db_belajar_bareng;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE study_groups (
    id INT AUTO_INCREMENT PRIMARY KEY,
    creator_id INT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    storage_path VARCHAR(255),
    db_schema_name VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE group_members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    group_id INT,
    user_id INT,
    role ENUM('admin', 'member') DEFAULT 'member',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES study_groups(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE resources (
    id INT AUTO_INCREMENT PRIMARY KEY,
    group_id INT,
    uploader_id INT,
    type ENUM('file', 'link', 'document'),
    content_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES study_groups(id) ON DELETE CASCADE,
    FOREIGN KEY (uploader_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE scaling_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    group_id INT,
    active_users_count INT,
    action VARCHAR(50),
    log_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES study_groups(id) ON DELETE CASCADE
);