-- ============================================================
-- Hostel Room Allocation System - Database Schema
-- DBMS Subject Project
-- ============================================================

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS allocations;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS rooms;
DROP TABLE IF EXISTS hostels;

-- ============================================================
-- Table: hostels
-- Stores hostel block information
-- ============================================================
CREATE TABLE hostels (
    hostel_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    type        TEXT    NOT NULL CHECK(type IN ('Boys', 'Girls', 'Co-ed')),
    warden_name TEXT    NOT NULL,
    contact     TEXT,
    created_at  TEXT    DEFAULT (datetime('now'))
);

-- ============================================================
-- Table: rooms
-- Stores individual room details inside a hostel
-- ============================================================
CREATE TABLE rooms (
    room_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    hostel_id   INTEGER NOT NULL REFERENCES hostels(hostel_id) ON DELETE CASCADE,
    room_number TEXT    NOT NULL,
    floor       INTEGER NOT NULL DEFAULT 1,
    capacity    INTEGER NOT NULL DEFAULT 2 CHECK(capacity > 0),
    room_type   TEXT    NOT NULL CHECK(room_type IN ('Single', 'Double', 'Triple', 'Dormitory')),
    has_ac      INTEGER NOT NULL DEFAULT 0 CHECK(has_ac IN (0, 1)),
    is_active   INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)),
    UNIQUE(hostel_id, room_number)
);

-- ============================================================
-- Table: students
-- Stores student records
-- ============================================================
CREATE TABLE students (
    student_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_number  TEXT    NOT NULL UNIQUE,
    name         TEXT    NOT NULL,
    email        TEXT    NOT NULL UNIQUE,
    phone        TEXT,
    gender       TEXT    NOT NULL CHECK(gender IN ('Male', 'Female', 'Other')),
    department   TEXT    NOT NULL,
    year         INTEGER NOT NULL CHECK(year BETWEEN 1 AND 5),
    created_at   TEXT    DEFAULT (datetime('now'))
);

-- ============================================================
-- Table: allocations
-- Maps students to rooms (many-to-one: many students per room)
-- ============================================================
CREATE TABLE allocations (
    allocation_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id      INTEGER NOT NULL UNIQUE REFERENCES students(student_id) ON DELETE CASCADE,
    room_id         INTEGER NOT NULL REFERENCES rooms(room_id) ON DELETE RESTRICT,
    check_in_date   TEXT    NOT NULL DEFAULT (date('now')),
    check_out_date  TEXT,
    status          TEXT    NOT NULL DEFAULT 'Active' CHECK(status IN ('Active', 'Vacated', 'Transferred')),
    remarks         TEXT,
    allocated_at    TEXT    DEFAULT (datetime('now'))
);

-- ============================================================
-- Indexes for performance
-- ============================================================
CREATE INDEX idx_allocations_room    ON allocations(room_id);
CREATE INDEX idx_allocations_status  ON allocations(status);
CREATE INDEX idx_rooms_hostel        ON rooms(hostel_id);
CREATE INDEX idx_students_dept       ON students(department);

-- ============================================================
-- View: room_occupancy
-- Useful report view showing current occupancy per room
-- ============================================================
CREATE VIEW room_occupancy AS
SELECT
    r.room_id,
    h.name          AS hostel_name,
    r.room_number,
    r.capacity,
    COUNT(a.allocation_id)                  AS occupied,
    r.capacity - COUNT(a.allocation_id)     AS available,
    CASE
        WHEN COUNT(a.allocation_id) >= r.capacity THEN 'Full'
        WHEN COUNT(a.allocation_id) = 0           THEN 'Empty'
        ELSE 'Partial'
    END AS occupancy_status
FROM rooms r
JOIN hostels h ON r.hostel_id = h.hostel_id
LEFT JOIN allocations a ON r.room_id = a.room_id AND a.status = 'Active'
WHERE r.is_active = 1
GROUP BY r.room_id;

-- ============================================================
-- Sample seed data
-- ============================================================
INSERT INTO hostels (name, type, warden_name, contact) VALUES
    ('Vivekananda Block', 'Boys',  'Mr. Ramesh Kumar',  '9876500001'),
    ('Saraswati Block',   'Girls', 'Ms. Priya Sharma',  '9876500002'),
    ('Gandhi Block',      'Co-ed', 'Dr. Anil Verma',    '9876500003');

INSERT INTO rooms (hostel_id, room_number, floor, capacity, room_type, has_ac) VALUES
    (1, '101', 1, 2, 'Double',  0),
    (1, '102', 1, 1, 'Single',  1),
    (1, '201', 2, 3, 'Triple',  0),
    (1, '202', 2, 2, 'Double',  1),
    (2, '101', 1, 2, 'Double',  0),
    (2, '102', 1, 1, 'Single',  1),
    (2, '201', 2, 2, 'Double',  0),
    (3, '101', 1, 2, 'Double',  1),
    (3, '102', 1, 2, 'Double',  0);

INSERT INTO students (roll_number, name, email, phone, gender, department, year) VALUES
    ('CS2101', 'Arjun Mehta',    'arjun@college.edu',   '9900001111', 'Male',   'Computer Science', 2),
    ('CS2102', 'Sneha Patel',    'sneha@college.edu',   '9900002222', 'Female', 'Computer Science', 2),
    ('EC2101', 'Rohit Singh',    'rohit@college.edu',   '9900003333', 'Male',   'Electronics',      2),
    ('ME2101', 'Kavya Nair',     'kavya@college.edu',   '9900004444', 'Female', 'Mechanical',       2),
    ('CS3101', 'Aditya Roy',     'aditya@college.edu',  '9900005555', 'Male',   'Computer Science', 3),
    ('EC3101', 'Priya Reddy',    'priya@college.edu',   '9900006666', 'Female', 'Electronics',      3);

INSERT INTO allocations (student_id, room_id, check_in_date, status) VALUES
    (1, 1, '2025-07-01', 'Active'),
    (3, 1, '2025-07-01', 'Active'),
    (5, 2, '2025-07-01', 'Active'),
    (2, 5, '2025-07-01', 'Active'),
    (4, 6, '2025-07-01', 'Active'),
    (6, 7, '2025-07-01', 'Active');
