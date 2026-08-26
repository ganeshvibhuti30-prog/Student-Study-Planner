from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

DATABASE = "database.db"

# Secret key is required for Flask sessions
app.config["SECRET_KEY"] = "student-study-planner-secret-key"

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def create_database():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            student_id TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            course TEXT NOT NULL,
            semester TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_email
        ON users(email)
    """)

    connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_student_id
        ON users(student_id)
    """)

    connection.commit()
    connection.close()


@app.route("/")
def home():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form["full_name"].strip()
        student_id = request.form["student_id"].strip()
        email = request.form["email"].strip()
        course = request.form["course"].strip()
        semester = request.form["semester"].strip()

        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

                # Server-side validation
        if not full_name:
            return "Full name is required."

        if not student_id:
            return "Student ID is required."

        if not email:
            return "Email is required."

        if not course:
            return "Course is required."

        if not semester:
            return "Semester is required."

        if not password:
            return "Password is required."
        
        if password != confirm_password:
            return "Passwords do not match."

        if len(password) < 8:
            return "Password must contain at least 8 characters."

        if not any(char.isupper() for char in password):
            return "Password must contain at least one uppercase letter."

        if not any(char.islower() for char in password):
            return "Password must contain at least one lowercase letter."

        if not any(char.isdigit() for char in password):
            return "Password must contain at least one number."
        
        connection = get_db_connection()

        existing_email = connection.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if existing_email:
            connection.close()
            return "Email is already registered."

        existing_student = connection.execute(
            "SELECT id FROM users WHERE student_id = ?",
            (student_id,)
        ).fetchone()

        if existing_student:
            connection.close()
            return "Student ID is already registered."

        password_hash = generate_password_hash(password)

        connection.execute("""
            INSERT INTO users
            (
                full_name,
                student_id,
                email,
                course,
                semester,
                password_hash
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            full_name,
            student_id,
            email,
            course,
            semester,
            password_hash
        ))

        connection.commit()
        connection.close()

        return "Registration successful!"

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip()
        password = request.form["password"]

        connection = get_db_connection()

        user = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        connection.close()

        if user is None:
            return render_template(
                "login.html",
                error="Invalid email or password."
            )

        if not check_password_hash(user["password_hash"], password):
            return render_template(
                "login.html",
                error="Invalid email or password."
            )

        # Store logged-in user's ID in session
        session["user_id"] = user["id"]
        session["login_message"] = "Login successful. Welcome back!"

        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    user = connection.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    connection.close()

    if user is None:
        session.clear()
        return redirect(url_for("login"))

    return render_template("dashboard.html", user=user)

@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    user = connection.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    connection.close()

    if user is None:
        session.clear()
        return redirect(url_for("login"))

    return render_template("profile.html", user=user)

@app.route("/logout")
def logout():

    # Remove login information from session
    session.clear()

    return render_template(
        "login.html",
        logout_message="You have been logged out successfully."
    )


if __name__ == "__main__":
    create_database()
    app.run(debug=True)