# Gym Membership Tracker (DBMS Mini Project)

A small Flask + SQLite app for tracking gym members, plans, memberships, and payments.

## Features
- Add and list members
- Add and list gym plans
- Create and track memberships
- Record and track payments
- Dashboard with quick counts and recent memberships

## Tech Stack
- Python 3
- Flask
- SQLite

## Project Structure
- `app.py` - Flask application
- `schema.sql` - Database schema
- `templates/` - HTML templates
- `static/style.css` - UI styling

## Setup
```bash
cd <project-folder>
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
cd <project-folder>
source .venv/bin/activate
export SECRET_KEY="your-strong-secret-key"
python app.py
```

Then open: `http://127.0.0.1:5000`

## DBMS Concepts Used
- Relational schema with foreign keys
- One-to-many relationships:
  - `members -> memberships`
  - `plans -> memberships`
  - `memberships -> payments`
- Basic CRUD operations using SQL queries
- Constraints (`UNIQUE`, `CHECK`, `NOT NULL`, `FOREIGN KEY`)
