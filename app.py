from flask import Flask, render_template, request
import sqlite3
from werkzeug.security import generate_password_hash

app = Flask(__name__)

DATABASE = "database.db"


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
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

    connection.commit()
    connection.close()


@app.route("/")
def home():
    return "Student Study Planner is running!"


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

        # Check password match
        if password != confirm_password:
            return "Passwords do not match."

        # Check password length
        if len(password) < 8:
            return "Password must contain at least 8 characters."

        connection = get_db_connection()

        # Check if email already exists
        existing_email = connection.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if existing_email:
            connection.close()
            return "Email is already registered."

        # Check if student ID already exists
        existing_student = connection.execute(
            "SELECT id FROM users WHERE student_id = ?",
            (student_id,)
        ).fetchone()

        if existing_student:
            connection.close()
            return "Student ID is already registered."

        # Hash the password
        password_hash = generate_password_hash(password)

        # Save student
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


if __name__ == "__main__":
    create_database()
    app.run(debug=True)