-- Lab 3 - Part 2: Library - BONUS (images for books and authors)
-- Run this AFTER problem2_DDL.sql and problem2_DML.sql (optional: the website
-- also adds these columns by itself the first time it starts).
-- It does NOT drop or change existing rows. Running it twice is safe.

USE library;

-- BOOK.image_filename
SET @sql = IF(
    (SELECT COUNT(*) FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'BOOK' AND COLUMN_NAME = 'image_filename') = 0,
    'ALTER TABLE BOOK ADD COLUMN image_filename VARCHAR(255) NULL',
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- AUTHOR.image_filename
SET @sql = IF(
    (SELECT COUNT(*) FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'AUTHOR' AND COLUMN_NAME = 'image_filename') = 0,
    'ALTER TABLE AUTHOR ADD COLUMN image_filename VARCHAR(255) NULL',
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
