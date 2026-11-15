-- Student database, students table, and sample data.
SET NAMES utf8mb4;
CREATE DATABASE IF NOT EXISTS studentdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE studentdb;
CREATE TABLE IF NOT EXISTS students(
  id INT PRIMARY KEY AUTO_INCREMENT,
  student_id VARCHAR(10),
  fullname VARCHAR(100),
  dob DATE,
  major VARCHAR(50)
);
-- Dates of birth are sample data.
INSERT INTO students(student_id, fullname, dob, major) VALUES
  ('523H0145', 'Nguyễn Nhựt Khang',      '2005-03-15', 'Computer Science'),
  ('523H0164', 'Nguyễn Trần Hoàng Nhân', '2005-07-21', 'Computer Science'),
  ('523H0117', 'Nguyễn Thành Nam',       '2005-11-02', 'Computer Science');
