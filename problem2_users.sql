-- Lab 3 - Part 2: Library - users table for Login / Registration
-- Run this AFTER problem2_DDL.sql and problem2_DML.sql.
-- It does NOT drop or change the AUTHOR and BOOK tables or their data,
-- and running it a second time does nothing (IF NOT EXISTS).

USE library;

CREATE TABLE IF NOT EXISTS users (
    user_id INT NOT NULL AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    registration_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),
    UNIQUE (email)
);
