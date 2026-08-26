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

    connection.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject_code TEXT NOT NULL,
            subject_name TEXT NOT NULL,
            credits INTEGER NOT NULL,
            semester TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, subject_code)
        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            deadline TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            exam_date TEXT NOT NULL,
            exam_time TEXT NOT NULL,
            exam_type TEXT NOT NULL,
            preparation_status TEXT NOT NULL DEFAULT 'Not Started',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
        )
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

@app.route("/subjects", methods=["GET", "POST"])
def subjects():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    if request.method == "POST":

        subject_code = request.form["subject_code"].strip()
        subject_name = request.form["subject_name"].strip()
        credits = request.form["credits"].strip()
        semester = request.form["semester"].strip()

        if not subject_code or not subject_name or not credits or not semester:

            subjects = connection.execute("""
                SELECT *
                FROM subjects
                WHERE user_id = ?
                ORDER BY semester, subject_code
            """, (session["user_id"],)).fetchall()

            connection.close()

            return render_template(
                "subjects.html",
                error="All subject fields are required.",
                subjects=subjects
            )

        try:
            credits = int(credits)

            if credits < 1 or credits > 4:

                subjects = connection.execute("""
                    SELECT *
                    FROM subjects
                    WHERE user_id = ?
                    ORDER BY semester, subject_code
                """, (session["user_id"],)).fetchall()

                connection.close()

                return render_template(
                    "subjects.html",
                    error="Credits must be between 1 and 4.",
                    subjects=subjects
                )

            connection.execute("""
                INSERT INTO subjects
                (
                    user_id,
                    subject_code,
                    subject_name,
                    credits,
                    semester
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                session["user_id"],
                subject_code,
                subject_name,
                credits,
                semester
            ))

            connection.commit()

        except ValueError:

            subjects = connection.execute("""
                SELECT *
                FROM subjects
                WHERE user_id = ?
                ORDER BY semester, subject_code
            """, (session["user_id"],)).fetchall()

            connection.close()

            return render_template(
                "subjects.html",
                error="Credits must be a valid number.",
                subjects=subjects
            )

        except sqlite3.IntegrityError:

            subjects = connection.execute("""
                SELECT *
                FROM subjects
                WHERE user_id = ?
                ORDER BY semester, subject_code
            """, (session["user_id"],)).fetchall()

            connection.close()

            return render_template(
                "subjects.html",
                error="This subject code already exists.",
                subjects=subjects
            )

    subjects = connection.execute("""
        SELECT *
        FROM subjects
        WHERE user_id = ?
        ORDER BY semester, subject_code
    """, (session["user_id"],)).fetchall()

    connection.close()

    return render_template(
        "subjects.html",
        subjects=subjects
    )


@app.route("/subjects/delete/<int:subject_id>", methods=["POST"])
def delete_subject(subject_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    connection.execute("""
        DELETE FROM subjects
        WHERE id = ? AND user_id = ?
    """, (
        subject_id,
        session["user_id"]
    ))

    connection.commit()
    connection.close()

    return redirect(url_for("subjects"))
@app.route("/assignments", methods=["GET", "POST"])
def assignments():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    if request.method == "POST":

        subject_id = request.form["subject_id"].strip()
        description = request.form["description"].strip()
        deadline = request.form["deadline"].strip()
        priority = request.form["priority"].strip()
        status = request.form["status"].strip()

        if not subject_id or not description or not deadline or not priority or not status:
            subjects = connection.execute("""
                SELECT *
                FROM subjects
                WHERE user_id = ?
                ORDER BY subject_name
            """, (session["user_id"],)).fetchall()

            assignments_list = connection.execute("""
                SELECT assignments.*, subjects.subject_name
                FROM assignments
                JOIN subjects ON assignments.subject_id = subjects.id
                WHERE assignments.user_id = ?
                ORDER BY assignments.deadline
            """, (session["user_id"],)).fetchall()

            connection.close()

            return render_template(
                "assignments.html",
                subjects=subjects,
                assignments=assignments_list,
                error="All assignment fields are required."
            )

        connection.execute("""
            INSERT INTO assignments
            (
                user_id,
                subject_id,
                description,
                deadline,
                priority,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            subject_id,
            description,
            deadline,
            priority,
            status
        ))

        connection.commit()

    subjects = connection.execute("""
        SELECT *
        FROM subjects
        WHERE user_id = ?
        ORDER BY subject_name
    """, (session["user_id"],)).fetchall()

    assignments_list = connection.execute("""
        SELECT assignments.*, subjects.subject_name
        FROM assignments
        JOIN subjects ON assignments.subject_id = subjects.id
        WHERE assignments.user_id = ?
        ORDER BY assignments.deadline
    """, (session["user_id"],)).fetchall()

    connection.close()

    return render_template(
        "assignments.html",
        subjects=subjects,
        assignments=assignments_list
    )


@app.route("/assignments/edit/<int:assignment_id>", methods=["GET", "POST"])
def edit_assignment(assignment_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    assignment = connection.execute("""
        SELECT *
        FROM assignments
        WHERE id = ? AND user_id = ?
    """, (
        assignment_id,
        session["user_id"]
    )).fetchone()

    if assignment is None:
        connection.close()
        return redirect(url_for("assignments"))

    if request.method == "POST":

        subject_id = request.form["subject_id"].strip()
        description = request.form["description"].strip()
        deadline = request.form["deadline"].strip()
        priority = request.form["priority"].strip()
        status = request.form["status"].strip()

        connection.execute("""
            UPDATE assignments
            SET subject_id = ?,
                description = ?,
                deadline = ?,
                priority = ?,
                status = ?
            WHERE id = ? AND user_id = ?
        """, (
            subject_id,
            description,
            deadline,
            priority,
            status,
            assignment_id,
            session["user_id"]
        ))

        connection.commit()
        connection.close()

        return redirect(url_for("assignments"))

    subjects = connection.execute("""
        SELECT *
        FROM subjects
        WHERE user_id = ?
        ORDER BY subject_name
    """, (session["user_id"],)).fetchall()

    connection.close()

    return render_template(
        "edit_assignment.html",
        assignment=assignment,
        subjects=subjects
    )


@app.route("/assignments/delete/<int:assignment_id>", methods=["POST"])
def delete_assignment(assignment_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    connection.execute("""
        DELETE FROM assignments
        WHERE id = ? AND user_id = ?
    """, (
        assignment_id,
        session["user_id"]
    ))

    connection.commit()
    connection.close()

    return redirect(url_for("assignments"))


@app.route("/assignments/complete/<int:assignment_id>", methods=["POST"])
def complete_assignment(assignment_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    connection.execute("""
        UPDATE assignments
        SET status = 'Completed'
        WHERE id = ? AND user_id = ?
    """, (
        assignment_id,
        session["user_id"]
    ))

    connection.commit()
    connection.close()

    return redirect(url_for("assignments"))
@app.route("/exams", methods=["GET", "POST"])
def exams():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    if request.method == "POST":

        subject_id = request.form["subject_id"].strip()
        exam_date = request.form["exam_date"].strip()
        exam_time = request.form["exam_time"].strip()
        exam_type = request.form["exam_type"].strip()
        preparation_status = request.form["preparation_status"].strip()

        if not subject_id or not exam_date or not exam_time or not exam_type or not preparation_status:

            subjects = connection.execute("""
                SELECT *
                FROM subjects
                WHERE user_id = ?
                ORDER BY subject_name
            """, (session["user_id"],)).fetchall()

            exams_list = connection.execute("""
                SELECT exams.*, subjects.subject_name
                FROM exams
                JOIN subjects ON exams.subject_id = subjects.id
                WHERE exams.user_id = ?
                ORDER BY exams.exam_date, exams.exam_time
            """, (session["user_id"],)).fetchall()

            connection.close()

            return render_template(
                "exams.html",
                subjects=subjects,
                exams=exams_list,
                error="All exam fields are required."
            )

        connection.execute("""
            INSERT INTO exams
            (
                user_id,
                subject_id,
                exam_date,
                exam_time,
                exam_type,
                preparation_status
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            subject_id,
            exam_date,
            exam_time,
            exam_type,
            preparation_status
        ))

        connection.commit()

    subjects = connection.execute("""
        SELECT *
        FROM subjects
        WHERE user_id = ?
        ORDER BY subject_name
    """, (session["user_id"],)).fetchall()

    exams_list = connection.execute("""
        SELECT exams.*, subjects.subject_name
        FROM exams
        JOIN subjects ON exams.subject_id = subjects.id
        WHERE exams.user_id = ?
        ORDER BY exams.exam_date, exams.exam_time
    """, (session["user_id"],)).fetchall()

    connection.close()

    return render_template(
        "exams.html",
        subjects=subjects,
        exams=exams_list
    )


@app.route("/exams/edit/<int:exam_id>", methods=["GET", "POST"])
def edit_exam(exam_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    exam = connection.execute("""
        SELECT *
        FROM exams
        WHERE id = ? AND user_id = ?
    """, (
        exam_id,
        session["user_id"]
    )).fetchone()

    if exam is None:
        connection.close()
        return redirect(url_for("exams"))

    if request.method == "POST":

        subject_id = request.form["subject_id"].strip()
        exam_date = request.form["exam_date"].strip()
        exam_time = request.form["exam_time"].strip()
        exam_type = request.form["exam_type"].strip()
        preparation_status = request.form["preparation_status"].strip()

        connection.execute("""
            UPDATE exams
            SET subject_id = ?,
                exam_date = ?,
                exam_time = ?,
                exam_type = ?,
                preparation_status = ?
            WHERE id = ? AND user_id = ?
        """, (
            subject_id,
            exam_date,
            exam_time,
            exam_type,
            preparation_status,
            exam_id,
            session["user_id"]
        ))

        connection.commit()
        connection.close()

        return redirect(url_for("exams"))

    subjects = connection.execute("""
        SELECT *
        FROM subjects
        WHERE user_id = ?
        ORDER BY subject_name
    """, (session["user_id"],)).fetchall()

    connection.close()

    return render_template(
        "edit_exam.html",
        exam=exam,
        subjects=subjects
    )


@app.route("/exams/delete/<int:exam_id>", methods=["POST"])
def delete_exam(exam_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    connection.execute("""
        DELETE FROM exams
        WHERE id = ? AND user_id = ?
    """, (
        exam_id,
        session["user_id"]
    ))

    connection.commit()
    connection.close()

    return redirect(url_for("exams"))

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