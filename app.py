from datetime import date
import os
import secrets
import sqlite3
from pathlib import Path

from flask import Flask, flash, g, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "gym_tracker.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"

app = Flask(__name__)
configured_secret = os.getenv("SECRET_KEY")
app.config["SECRET_KEY"] = configured_secret or secrets.token_hex(32)
if not configured_secret:
    app.logger.warning(
        "SECRET_KEY is not set. A temporary key is being used and sessions will reset on restart."
    )


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error: Exception | None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db = get_db()
    with open(SCHEMA_PATH, "r", encoding="utf-8") as schema:
        db.executescript(schema.read())
    db.commit()


@app.route("/")
def dashboard():
    db = get_db()
    counts = {
        "members": db.execute("SELECT COUNT(*) AS total FROM members").fetchone()["total"],
        "plans": db.execute("SELECT COUNT(*) AS total FROM plans").fetchone()["total"],
        "memberships": db.execute("SELECT COUNT(*) AS total FROM memberships").fetchone()["total"],
        "payments": db.execute("SELECT COUNT(*) AS total FROM payments").fetchone()["total"],
    }
    recent_memberships = db.execute(
        """
        SELECT m.id, mem.full_name, p.plan_name, m.start_date, m.end_date, m.status
        FROM memberships m
        JOIN members mem ON mem.id = m.member_id
        JOIN plans p ON p.id = m.plan_id
        ORDER BY m.id DESC
        LIMIT 5
        """
    ).fetchall()
    return render_template("index.html", counts=counts, recent_memberships=recent_memberships)


@app.route("/members")
def members():
    all_members = get_db().execute(
        "SELECT id, full_name, email, phone, joined_on FROM members ORDER BY id DESC"
    ).fetchall()
    return render_template("members.html", members=all_members)


@app.route("/members/add", methods=["GET", "POST"])
def add_member():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        joined_on = request.form.get("joined_on", str(date.today()))

        if not full_name or not email:
            flash("Full name and email are required.", "error")
            return redirect(url_for("add_member"))

        db = get_db()
        try:
            db.execute(
                "INSERT INTO members (full_name, email, phone, joined_on) VALUES (?, ?, ?, ?)",
                (full_name, email, phone, joined_on),
            )
            db.commit()
            flash("Member added successfully.", "success")
            return redirect(url_for("members"))
        except sqlite3.IntegrityError:
            flash("A member with this email already exists.", "error")

    return render_template("add_member.html", today=str(date.today()))


@app.route("/plans")
def plans():
    all_plans = get_db().execute(
        "SELECT id, plan_name, duration_months, fee FROM plans ORDER BY id DESC"
    ).fetchall()
    return render_template("plans.html", plans=all_plans)


@app.route("/plans/add", methods=["GET", "POST"])
def add_plan():
    if request.method == "POST":
        plan_name = request.form.get("plan_name", "").strip()
        duration_months = request.form.get("duration_months", "").strip()
        fee = request.form.get("fee", "").strip()

        if not plan_name or not duration_months or not fee:
            flash("All fields are required.", "error")
            return redirect(url_for("add_plan"))

        try:
            parsed_duration = int(duration_months)
            parsed_fee = float(fee)
        except ValueError:
            flash("Duration must be a whole number and fee must be numeric.", "error")
            return redirect(url_for("add_plan"))

        db = get_db()
        db.execute(
            "INSERT INTO plans (plan_name, duration_months, fee) VALUES (?, ?, ?)",
            (plan_name, parsed_duration, parsed_fee),
        )
        db.commit()
        flash("Plan added successfully.", "success")
        return redirect(url_for("plans"))

    return render_template("add_plan.html")


@app.route("/memberships")
def memberships():
    all_memberships = get_db().execute(
        """
        SELECT m.id, mem.full_name, p.plan_name, m.start_date, m.end_date, m.status
        FROM memberships m
        JOIN members mem ON mem.id = m.member_id
        JOIN plans p ON p.id = m.plan_id
        ORDER BY m.id DESC
        """
    ).fetchall()
    return render_template("memberships.html", memberships=all_memberships)


@app.route("/memberships/add", methods=["GET", "POST"])
def add_membership():
    db = get_db()
    members_list = db.execute("SELECT id, full_name FROM members ORDER BY full_name").fetchall()
    plans_list = db.execute("SELECT id, plan_name FROM plans ORDER BY plan_name").fetchall()

    if request.method == "POST":
        member_id = request.form.get("member_id", "").strip()
        plan_id = request.form.get("plan_id", "").strip()
        start_date = request.form.get("start_date", str(date.today())).strip()
        end_date = request.form.get("end_date", str(date.today())).strip()
        status = request.form.get("status", "Active").strip()

        if not member_id or not plan_id:
            flash("Member and plan are required.", "error")
            return redirect(url_for("add_membership"))

        try:
            parsed_member_id = int(member_id)
            parsed_plan_id = int(plan_id)
        except ValueError:
            flash("Selected member and plan are invalid.", "error")
            return redirect(url_for("add_membership"))

        db.execute(
            """
            INSERT INTO memberships (member_id, plan_id, start_date, end_date, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (parsed_member_id, parsed_plan_id, start_date, end_date, status),
        )
        db.commit()
        flash("Membership added successfully.", "success")
        return redirect(url_for("memberships"))

    return render_template(
        "add_membership.html",
        members=members_list,
        plans=plans_list,
        today=str(date.today()),
    )


@app.route("/payments")
def payments():
    all_payments = get_db().execute(
        """
        SELECT pay.id, mem.full_name, p.plan_name, pay.amount, pay.paid_on, pay.payment_mode, pay.notes
        FROM payments pay
        JOIN memberships ms ON ms.id = pay.membership_id
        JOIN members mem ON mem.id = ms.member_id
        JOIN plans p ON p.id = ms.plan_id
        ORDER BY pay.id DESC
        """
    ).fetchall()
    return render_template("payments.html", payments=all_payments)


@app.route("/payments/add", methods=["GET", "POST"])
def add_payment():
    db = get_db()
    memberships_list = db.execute(
        """
        SELECT ms.id, mem.full_name || ' - ' || p.plan_name AS label
        FROM memberships ms
        JOIN members mem ON mem.id = ms.member_id
        JOIN plans p ON p.id = ms.plan_id
        ORDER BY ms.id DESC
        """
    ).fetchall()

    if request.method == "POST":
        membership_id = request.form.get("membership_id", "").strip()
        amount = request.form.get("amount", "").strip()
        paid_on = request.form.get("paid_on", str(date.today())).strip()
        payment_mode = request.form.get("payment_mode", "").strip()
        notes = request.form.get("notes", "").strip()

        if not membership_id or not amount or not payment_mode:
            flash("Membership, amount and mode are required.", "error")
            return redirect(url_for("add_payment"))

        try:
            parsed_membership_id = int(membership_id)
            parsed_amount = float(amount)
        except ValueError:
            flash("Membership must be valid and amount must be numeric.", "error")
            return redirect(url_for("add_payment"))

        db.execute(
            """
            INSERT INTO payments (membership_id, amount, paid_on, payment_mode, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (parsed_membership_id, parsed_amount, paid_on, payment_mode, notes),
        )
        db.commit()
        flash("Payment recorded successfully.", "success")
        return redirect(url_for("payments"))

    return render_template("add_payment.html", memberships=memberships_list, today=str(date.today()))


with app.app_context():
    init_db()


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
