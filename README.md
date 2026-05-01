# Hostel Room Allocation System

A full-stack web application built with **Python (Flask)** and **SQLite** for managing hostel room allocations — submitted as a DBMS subject project.

---

## Features

| Module | Operations |
|--------|-----------|
| **Hostels** | Add / Edit / Delete hostel blocks |
| **Rooms** | Add / Edit / Delete rooms; filter by hostel |
| **Students** | Add / Edit / Delete students; search |
| **Allocations** | Allocate rooms, vacate allocations |
| **Reports** | Occupancy view, department-wise stats, hostel utilisation |

---

## Database Design

### Tables

```
hostels      → hostel_id (PK), name, type, warden_name, contact
rooms        → room_id (PK), hostel_id (FK), room_number, floor, capacity, room_type, has_ac, is_active
students     → student_id (PK), roll_number (UNIQUE), name, email (UNIQUE), phone, gender, department, year
allocations  → allocation_id (PK), student_id (FK, UNIQUE), room_id (FK), check_in_date, check_out_date, status
```

### ER Diagram (text)

```
HOSTELS (1) ──< ROOMS (1) ──< ALLOCATIONS >── (1) STUDENTS
```

- One hostel has many rooms.
- One room can have many allocations (up to its capacity).
- Each student has at most one active allocation at a time.

### View

`room_occupancy` — pre-built SQL view joining rooms + hostels + allocations showing real-time occupancy status.

---

## Setup & Run

### Prerequisites

- Python 3.9+

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/ecofinds.git
cd ecofinds

# 2. Create and activate virtual environment (recommended)
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python app.py
```

Open your browser at **http://localhost:5000**

> The SQLite database (`hostel.db`) is created automatically on first run with sample seed data.

---

## Project Structure

```
.
├── app.py              ← Flask application (routes, DB helpers)
├── schema.sql          ← SQL schema + seed data
├── requirements.txt
├── hostel.db           ← SQLite DB (auto-generated, git-ignored)
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── hostels.html
│   ├── hostel_form.html
│   ├── rooms.html
│   ├── room_form.html
│   ├── students.html
│   ├── student_form.html
│   ├── allocations.html
│   ├── allocation_form.html
│   └── reports.html
└── static/
    └── css/style.css
```

---

## Key SQL Concepts Demonstrated

1. **DDL** — `CREATE TABLE`, `DROP TABLE`, `CREATE INDEX`, `CREATE VIEW`
2. **DML** — `INSERT`, `UPDATE`, `DELETE`, `SELECT`
3. **Constraints** — `PRIMARY KEY`, `FOREIGN KEY`, `UNIQUE`, `NOT NULL`, `CHECK`
4. **Joins** — `INNER JOIN`, `LEFT JOIN` across 4 tables
5. **Aggregation** — `COUNT`, `SUM`, `GROUP BY`, `HAVING`
6. **Subqueries** — used in availability checks and unallocated student queries
7. **Views** — `room_occupancy` view for reporting
8. **Indexes** — on frequently queried columns for performance
9. **Referential Integrity** — `ON DELETE CASCADE / RESTRICT`
10. **Transactions** — via SQLite's auto-commit in Flask
