"""
Hostel Room Allocation System
Flask + SQLite web application for DBMS subject project
"""

import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, flash, g

app = Flask(__name__)
app.secret_key = "hostel_secret_key_2025"

DATABASE = os.path.join(os.path.dirname(__file__), "hostel.db")
SCHEMA   = os.path.join(os.path.dirname(__file__), "schema.sql")


# ─── Database helpers ────────────────────────────────────────────────────────

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
    return db


@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db():
    """Create tables and load seed data if the database file doesn't exist."""
    if not os.path.exists(DATABASE):
        with app.app_context():
            db = get_db()
            with open(SCHEMA, "r") as f:
                db.executescript(f.read())
            db.commit()


# ─── Routes: Dashboard ────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    db = get_db()
    stats = {
        "total_hostels":    db.execute("SELECT COUNT(*) FROM hostels").fetchone()[0],
        "total_rooms":      db.execute("SELECT COUNT(*) FROM rooms WHERE is_active=1").fetchone()[0],
        "total_students":   db.execute("SELECT COUNT(*) FROM students").fetchone()[0],
        "active_allocs":    db.execute("SELECT COUNT(*) FROM allocations WHERE status='Active'").fetchone()[0],
        "full_rooms":       db.execute("SELECT COUNT(*) FROM room_occupancy WHERE occupancy_status='Full'").fetchone()[0],
        "empty_rooms":      db.execute("SELECT COUNT(*) FROM room_occupancy WHERE occupancy_status='Empty'").fetchone()[0],
        "unallocated":      db.execute(
            "SELECT COUNT(*) FROM students WHERE student_id NOT IN "
            "(SELECT student_id FROM allocations WHERE status='Active')"
        ).fetchone()[0],
    }
    recent = db.execute(
        """SELECT a.allocation_id, s.name AS student_name, s.roll_number,
                  h.name AS hostel_name, r.room_number, a.check_in_date, a.status
           FROM allocations a
           JOIN students s ON a.student_id = s.student_id
           JOIN rooms    r ON a.room_id    = r.room_id
           JOIN hostels  h ON r.hostel_id  = h.hostel_id
           ORDER BY a.allocated_at DESC LIMIT 5"""
    ).fetchall()
    return render_template("dashboard.html", stats=stats, recent=recent)


# ─── Routes: Hostels ──────────────────────────────────────────────────────────

@app.route("/hostels")
def hostels():
    db = get_db()
    rows = db.execute(
        """SELECT h.*, COUNT(r.room_id) AS room_count
           FROM hostels h LEFT JOIN rooms r ON h.hostel_id = r.hostel_id AND r.is_active=1
           GROUP BY h.hostel_id ORDER BY h.name"""
    ).fetchall()
    return render_template("hostels.html", hostels=rows)


@app.route("/hostels/add", methods=["GET", "POST"])
def add_hostel():
    if request.method == "POST":
        name    = request.form["name"].strip()
        htype   = request.form["type"]
        warden  = request.form["warden_name"].strip()
        contact = request.form.get("contact", "").strip()
        try:
            get_db().execute(
                "INSERT INTO hostels(name,type,warden_name,contact) VALUES(?,?,?,?)",
                (name, htype, warden, contact)
            )
            get_db().commit()
            flash("Hostel added successfully.", "success")
            return redirect(url_for("hostels"))
        except sqlite3.IntegrityError:
            flash("A hostel with that name already exists.", "danger")
    return render_template("hostel_form.html", hostel=None)


@app.route("/hostels/edit/<int:hostel_id>", methods=["GET", "POST"])
def edit_hostel(hostel_id):
    db = get_db()
    hostel = db.execute("SELECT * FROM hostels WHERE hostel_id=?", (hostel_id,)).fetchone()
    if not hostel:
        flash("Hostel not found.", "warning")
        return redirect(url_for("hostels"))
    if request.method == "POST":
        name    = request.form["name"].strip()
        htype   = request.form["type"]
        warden  = request.form["warden_name"].strip()
        contact = request.form.get("contact", "").strip()
        try:
            db.execute(
                "UPDATE hostels SET name=?,type=?,warden_name=?,contact=? WHERE hostel_id=?",
                (name, htype, warden, contact, hostel_id)
            )
            db.commit()
            flash("Hostel updated.", "success")
            return redirect(url_for("hostels"))
        except sqlite3.IntegrityError:
            flash("A hostel with that name already exists.", "danger")
    return render_template("hostel_form.html", hostel=hostel)


@app.route("/hostels/delete/<int:hostel_id>", methods=["POST"])
def delete_hostel(hostel_id):
    db = get_db()
    try:
        db.execute("DELETE FROM hostels WHERE hostel_id=?", (hostel_id,))
        db.commit()
        flash("Hostel deleted.", "success")
    except sqlite3.IntegrityError:
        flash("Cannot delete hostel with active rooms/allocations.", "danger")
    return redirect(url_for("hostels"))


# ─── Routes: Rooms ────────────────────────────────────────────────────────────

@app.route("/rooms")
def rooms():
    db = get_db()
    hostel_filter = request.args.get("hostel_id", "")
    query = """
        SELECT r.*, h.name AS hostel_name,
               COUNT(a.allocation_id)              AS occupied,
               r.capacity - COUNT(a.allocation_id) AS available
        FROM rooms r
        JOIN hostels h ON r.hostel_id = h.hostel_id
        LEFT JOIN allocations a ON r.room_id=a.room_id AND a.status='Active'
        WHERE r.is_active=1
    """
    params = []
    if hostel_filter:
        query += " AND r.hostel_id=?"
        params.append(hostel_filter)
    query += " GROUP BY r.room_id ORDER BY h.name, r.room_number"
    rows     = db.execute(query, params).fetchall()
    hostels  = db.execute("SELECT * FROM hostels ORDER BY name").fetchall()
    return render_template("rooms.html", rooms=rows, hostels=hostels,
                           selected_hostel=hostel_filter)


@app.route("/rooms/add", methods=["GET", "POST"])
def add_room():
    db = get_db()
    hostels = db.execute("SELECT * FROM hostels ORDER BY name").fetchall()
    if request.method == "POST":
        hostel_id   = request.form["hostel_id"]
        room_number = request.form["room_number"].strip()
        floor       = int(request.form["floor"])
        capacity    = int(request.form["capacity"])
        room_type   = request.form["room_type"]
        has_ac      = 1 if request.form.get("has_ac") else 0
        try:
            db.execute(
                "INSERT INTO rooms(hostel_id,room_number,floor,capacity,room_type,has_ac) VALUES(?,?,?,?,?,?)",
                (hostel_id, room_number, floor, capacity, room_type, has_ac)
            )
            db.commit()
            flash("Room added successfully.", "success")
            return redirect(url_for("rooms"))
        except sqlite3.IntegrityError:
            flash("Room number already exists in this hostel.", "danger")
    return render_template("room_form.html", room=None, hostels=hostels)


@app.route("/rooms/edit/<int:room_id>", methods=["GET", "POST"])
def edit_room(room_id):
    db = get_db()
    room    = db.execute("SELECT * FROM rooms WHERE room_id=?", (room_id,)).fetchone()
    hostels = db.execute("SELECT * FROM hostels ORDER BY name").fetchall()
    if not room:
        flash("Room not found.", "warning")
        return redirect(url_for("rooms"))
    if request.method == "POST":
        hostel_id   = request.form["hostel_id"]
        room_number = request.form["room_number"].strip()
        floor       = int(request.form["floor"])
        capacity    = int(request.form["capacity"])
        room_type   = request.form["room_type"]
        has_ac      = 1 if request.form.get("has_ac") else 0
        is_active   = 1 if request.form.get("is_active") else 0
        try:
            db.execute(
                """UPDATE rooms SET hostel_id=?,room_number=?,floor=?,capacity=?,
                   room_type=?,has_ac=?,is_active=? WHERE room_id=?""",
                (hostel_id, room_number, floor, capacity, room_type, has_ac, is_active, room_id)
            )
            db.commit()
            flash("Room updated.", "success")
            return redirect(url_for("rooms"))
        except sqlite3.IntegrityError:
            flash("Room number already exists in this hostel.", "danger")
    return render_template("room_form.html", room=room, hostels=hostels)


@app.route("/rooms/delete/<int:room_id>", methods=["POST"])
def delete_room(room_id):
    db = get_db()
    try:
        db.execute("DELETE FROM rooms WHERE room_id=?", (room_id,))
        db.commit()
        flash("Room deleted.", "success")
    except sqlite3.IntegrityError:
        flash("Cannot delete room with active allocations.", "danger")
    return redirect(url_for("rooms"))


# ─── Routes: Students ─────────────────────────────────────────────────────────

@app.route("/students")
def students():
    db = get_db()
    search = request.args.get("q", "").strip()
    if search:
        rows = db.execute(
            """SELECT s.*,
                      a.allocation_id, r.room_number, h.name AS hostel_name
               FROM students s
               LEFT JOIN allocations a ON s.student_id=a.student_id AND a.status='Active'
               LEFT JOIN rooms    r ON a.room_id=r.room_id
               LEFT JOIN hostels  h ON r.hostel_id=h.hostel_id
               WHERE s.name LIKE ? OR s.roll_number LIKE ? OR s.department LIKE ?
               ORDER BY s.name""",
            (f"%{search}%", f"%{search}%", f"%{search}%")
        ).fetchall()
    else:
        rows = db.execute(
            """SELECT s.*,
                      a.allocation_id, r.room_number, h.name AS hostel_name
               FROM students s
               LEFT JOIN allocations a ON s.student_id=a.student_id AND a.status='Active'
               LEFT JOIN rooms    r ON a.room_id=r.room_id
               LEFT JOIN hostels  h ON r.hostel_id=h.hostel_id
               ORDER BY s.name"""
        ).fetchall()
    return render_template("students.html", students=rows, search=search)


@app.route("/students/add", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        db = get_db()
        roll   = request.form["roll_number"].strip().upper()
        name   = request.form["name"].strip()
        email  = request.form["email"].strip().lower()
        phone  = request.form.get("phone", "").strip()
        gender = request.form["gender"]
        dept   = request.form["department"].strip()
        year   = int(request.form["year"])
        try:
            db.execute(
                "INSERT INTO students(roll_number,name,email,phone,gender,department,year) VALUES(?,?,?,?,?,?,?)",
                (roll, name, email, phone, gender, dept, year)
            )
            db.commit()
            flash("Student added successfully.", "success")
            return redirect(url_for("students"))
        except sqlite3.IntegrityError as e:
            flash("Roll number or email already exists.", "danger")
    return render_template("student_form.html", student=None)


@app.route("/students/edit/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    db = get_db()
    student = db.execute("SELECT * FROM students WHERE student_id=?", (student_id,)).fetchone()
    if not student:
        flash("Student not found.", "warning")
        return redirect(url_for("students"))
    if request.method == "POST":
        roll   = request.form["roll_number"].strip().upper()
        name   = request.form["name"].strip()
        email  = request.form["email"].strip().lower()
        phone  = request.form.get("phone", "").strip()
        gender = request.form["gender"]
        dept   = request.form["department"].strip()
        year   = int(request.form["year"])
        try:
            db.execute(
                """UPDATE students SET roll_number=?,name=?,email=?,phone=?,
                   gender=?,department=?,year=? WHERE student_id=?""",
                (roll, name, email, phone, gender, dept, year, student_id)
            )
            db.commit()
            flash("Student updated.", "success")
            return redirect(url_for("students"))
        except sqlite3.IntegrityError:
            flash("Roll number or email already exists.", "danger")
    return render_template("student_form.html", student=student)


@app.route("/students/delete/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    db = get_db()
    db.execute("DELETE FROM students WHERE student_id=?", (student_id,))
    db.commit()
    flash("Student deleted.", "success")
    return redirect(url_for("students"))


# ─── Routes: Allocations ──────────────────────────────────────────────────────

@app.route("/allocations")
def allocations():
    db = get_db()
    rows = db.execute(
        """SELECT a.*, s.name AS student_name, s.roll_number,
                  h.name AS hostel_name, r.room_number
           FROM allocations a
           JOIN students s ON a.student_id=s.student_id
           JOIN rooms    r ON a.room_id=r.room_id
           JOIN hostels  h ON r.hostel_id=h.hostel_id
           ORDER BY a.status, a.allocated_at DESC"""
    ).fetchall()
    return render_template("allocations.html", allocations=rows)


@app.route("/allocations/add", methods=["GET", "POST"])
def add_allocation():
    db = get_db()
    # Students without active allocation
    unallocated = db.execute(
        """SELECT * FROM students WHERE student_id NOT IN
           (SELECT student_id FROM allocations WHERE status='Active')
           ORDER BY name"""
    ).fetchall()
    # Rooms with available space
    available_rooms = db.execute(
        """SELECT r.room_id, h.name||' - Room '||r.room_number AS label,
                  r.capacity - COUNT(a.allocation_id) AS available,
                  r.room_type, r.has_ac
           FROM rooms r
           JOIN hostels h ON r.hostel_id=h.hostel_id
           LEFT JOIN allocations a ON r.room_id=a.room_id AND a.status='Active'
           WHERE r.is_active=1
           GROUP BY r.room_id
           HAVING available > 0
           ORDER BY h.name, r.room_number"""
    ).fetchall()

    if request.method == "POST":
        student_id     = request.form["student_id"]
        room_id        = request.form["room_id"]
        check_in_date  = request.form["check_in_date"]
        remarks        = request.form.get("remarks", "").strip()
        # Verify room still has space
        avail = db.execute(
            """SELECT r.capacity - COUNT(a.allocation_id) AS available
               FROM rooms r LEFT JOIN allocations a ON r.room_id=a.room_id AND a.status='Active'
               WHERE r.room_id=? GROUP BY r.room_id""",
            (room_id,)
        ).fetchone()
        if avail and avail["available"] > 0:
            try:
                db.execute(
                    """INSERT INTO allocations(student_id,room_id,check_in_date,remarks,status)
                       VALUES(?,?,?,?,'Active')""",
                    (student_id, room_id, check_in_date, remarks)
                )
                db.commit()
                flash("Room allocated successfully.", "success")
                return redirect(url_for("allocations"))
            except sqlite3.IntegrityError:
                flash("This student already has an active allocation.", "danger")
        else:
            flash("Selected room is full. Please choose another.", "danger")

    return render_template("allocation_form.html",
                           unallocated=unallocated,
                           available_rooms=available_rooms)


@app.route("/allocations/vacate/<int:allocation_id>", methods=["POST"])
def vacate_allocation(allocation_id):
    db = get_db()
    check_out = request.form.get("check_out_date", "")
    db.execute(
        "UPDATE allocations SET status='Vacated', check_out_date=? WHERE allocation_id=?",
        (check_out or None, allocation_id)
    )
    db.commit()
    flash("Allocation vacated.", "success")
    return redirect(url_for("allocations"))


# ─── Routes: Reports ─────────────────────────────────────────────────────────

@app.route("/reports")
def reports():
    db = get_db()
    occupancy  = db.execute("SELECT * FROM room_occupancy ORDER BY hostel_name, room_number").fetchall()
    dept_stats = db.execute(
        """SELECT s.department, COUNT(s.student_id) AS total,
                  SUM(CASE WHEN a.status='Active' THEN 1 ELSE 0 END) AS allocated
           FROM students s
           LEFT JOIN allocations a ON s.student_id=a.student_id AND a.status='Active'
           GROUP BY s.department ORDER BY s.department"""
    ).fetchall()
    hostel_stats = db.execute(
        """SELECT h.name, h.type,
                  COUNT(r.room_id)   AS total_rooms,
                  SUM(r.capacity)    AS total_capacity,
                  COUNT(a.allocation_id) AS occupied
           FROM hostels h
           LEFT JOIN rooms       r ON h.hostel_id=r.hostel_id AND r.is_active=1
           LEFT JOIN allocations a ON r.room_id=a.room_id AND a.status='Active'
           GROUP BY h.hostel_id ORDER BY h.name"""
    ).fetchall()
    return render_template("reports.html",
                           occupancy=occupancy,
                           dept_stats=dept_stats,
                           hostel_stats=hostel_stats)


# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode, host="0.0.0.0", port=5000)
