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
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            classes_conducted INTEGER NOT NULL,
            classes_attended INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY (subject_id)
                REFERENCES subjects(id)
                ON DELETE CASCADE,

            UNIQUE(user_id, subject_id)
        )
    """)
    
    connection.execute("""
        CREATE TABLE IF NOT EXISTS marks (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           user_id INTEGER NOT NULL,
           subject_id INTEGER NOT NULL,
           marks_obtained REAL NOT NULL,
           max_marks REAL NOT NULL,
           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
           FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
           FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
           UNIQUE(user_id, subject_id)
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

@app.route("/attendance", methods=["GET", "POST"])
def attendance():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    error = None
    edit_id = request.args.get("edit", type=int)

    if request.method == "POST":

        subject_id = request.form["subject_id"]
        classes_conducted = request.form["classes_conducted"]
        classes_attended = request.form["classes_attended"]
        edit_id = request.form.get("edit_id")

        try:

            subject_id = int(subject_id)
            classes_conducted = int(classes_conducted)
            classes_attended = int(classes_attended)

            # Validation
            if classes_conducted <= 0:
                raise ValueError

            if classes_attended < 0:
                raise ValueError

            if classes_attended > classes_conducted:
                raise ValueError

            # Check subject belongs to logged-in user
            subject = connection.execute("""
                SELECT id
                FROM subjects
                WHERE id = ?
                AND user_id = ?
            """, (
                subject_id,
                session["user_id"]
            )).fetchone()

            if subject is None:
                raise ValueError

            # UPDATE existing attendance
            if edit_id:

                connection.execute("""
                    UPDATE attendance
                    SET subject_id = ?,
                        classes_conducted = ?,
                        classes_attended = ?
                    WHERE id = ?
                    AND user_id = ?
                """, (
                    subject_id,
                    classes_conducted,
                    classes_attended,
                    edit_id,
                    session["user_id"]
                ))

            # INSERT new attendance
            else:

                connection.execute("""
                    INSERT INTO attendance
                    (
                        user_id,
                        subject_id,
                        classes_conducted,
                        classes_attended
                    )
                    VALUES (?, ?, ?, ?)

                    ON CONFLICT(user_id, subject_id)
                    DO UPDATE SET
                        classes_conducted =
                            excluded.classes_conducted,
                        classes_attended =
                            excluded.classes_attended
                """, (
                    session["user_id"],
                    subject_id,
                    classes_conducted,
                    classes_attended
                ))

            connection.commit()
            connection.close()

            return redirect(url_for("attendance"))

        except (ValueError, TypeError):

            error = (
                "Please enter valid attendance. "
                "Attended classes cannot be greater "
                "than conducted classes."
            )

    # Get subjects and attendance
    subjects = connection.execute("""
        SELECT
            subjects.id,
            subjects.subject_code,
            subjects.subject_name,
            subjects.semester,

            attendance.id AS attendance_id,

            attendance.classes_conducted,
            attendance.classes_attended

        FROM subjects

        LEFT JOIN attendance
            ON subjects.id = attendance.subject_id
            AND attendance.user_id = ?

        WHERE subjects.user_id = ?

        ORDER BY subjects.semester, subjects.subject_code
    """, (
        session["user_id"],
        session["user_id"]
    )).fetchall()

    # Calculate attendance percentage
    subject_data = []

    total_conducted = 0
    total_attended = 0

    for subject in subjects:

        item = dict(subject)

        if (
            item["classes_conducted"] is not None
            and item["classes_conducted"] > 0
        ):

            percentage = (
                item["classes_attended"]
                / item["classes_conducted"]
            ) * 100

            item["percentage"] = round(
                percentage,
                2
            )

            total_conducted += item["classes_conducted"]
            total_attended += item["classes_attended"]

        else:

            item["percentage"] = None

        subject_data.append(item)

    # Overall attendance
    if total_conducted > 0:

        overall_attendance = round(
            (total_attended / total_conducted) * 100,
            2
        )

    else:

        overall_attendance = None

    # Attendance warning
    if overall_attendance is not None:

        if overall_attendance < 75:
            attendance_warning = True
        else:
            attendance_warning = False

    else:

        attendance_warning = False

    # Get attendance record being edited
    edit_attendance = None

    if edit_id:

        edit_attendance = connection.execute("""
            SELECT *
            FROM attendance
            WHERE id = ?
            AND user_id = ?
        """, (
            edit_id,
            session["user_id"]
        )).fetchone()

    connection.close()

    return render_template(
        "attendance.html",
        subjects=subject_data,
        error=error,
        edit_attendance=edit_attendance,
        overall_attendance=overall_attendance,
        attendance_warning=attendance_warning
    )

@app.route(
    "/attendance/delete/<int:attendance_id>",
    methods=["POST"]
)
def delete_attendance(attendance_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    connection.execute("""
        DELETE FROM attendance
        WHERE id = ?
        AND user_id = ?
    """, (
        attendance_id,
        session["user_id"]
    ))

    connection.commit()
    connection.close()

    return redirect(url_for("attendance"))

@app.route("/attendance-calculator", methods=["GET", "POST"])
def attendance_calculator():

    if "user_id" not in session:
        return redirect(url_for("login"))

    result = None
    error = None

    if request.method == "POST":

        classes_conducted = request.form.get("classes_conducted")
        classes_attended = request.form.get("classes_attended")
        target_percentage = request.form.get("target_percentage")

        try:

            classes_conducted = int(classes_conducted)
            classes_attended = int(classes_attended)
            target_percentage = float(target_percentage)

            # Validation
            if classes_conducted <= 0:
                raise ValueError

            if classes_attended < 0:
                raise ValueError

            if classes_attended > classes_conducted:
                raise ValueError

            if target_percentage <= 0 or target_percentage >= 100:
                raise ValueError

            # Current attendance percentage
            current_percentage = (
                classes_attended /
                classes_conducted
            ) * 100

            # Already reached target
            if current_percentage >= target_percentage:

                result = {
                    "current_percentage": round(
                        current_percentage,
                        2
                    ),
                    "target_percentage": target_percentage,
                    "classes_needed": 0,
                    "message": (
                        "You have already reached "
                        "your target attendance."
                    )
                }

            else:

                # Formula:
                #
                # (attended + x)
                # ---------------- >= target / 100
                # (conducted + x)
                #
                # x = (target * conducted - attended)
                #     / (100 - target)

                classes_needed = (
                    (
                        target_percentage *
                        classes_conducted
                    ) -
                    (
                        100 *
                        classes_attended
                    )
                ) / (
                    100 -
                    target_percentage
                )

                # Round UP because we cannot attend
                # a fraction of a class
                import math

                classes_needed = math.ceil(
                    classes_needed
                )

                result = {
                    "current_percentage": round(
                        current_percentage,
                        2
                    ),
                    "target_percentage": target_percentage,
                    "classes_needed": classes_needed,
                    "message": (
                        f"You need to attend the next "
                        f"{classes_needed} classes "
                        f"consecutively to reach "
                        f"{target_percentage}% attendance."
                    )
                }

        except (ValueError, TypeError):

            error = (
                "Please enter valid attendance values."
            )

    return render_template(
        "attendance-calculator.html",
        result=result,
        error=error
    )

    
@app.route("/marks", methods=["GET", "POST"])
def marks():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    error = None
    edit_id = request.args.get("edit", type=int)

    if request.method == "POST":

        subject_id = request.form["subject_id"]
        marks_obtained = request.form["marks_obtained"]
        max_marks = request.form["max_marks"]
        edit_id = request.form.get("edit_id")

        try:
            subject_id = int(subject_id)
            marks_obtained = float(marks_obtained)
            max_marks = float(max_marks)

            if max_marks <= 0:
                raise ValueError

            if marks_obtained < 0 or marks_obtained > max_marks:
                raise ValueError

            # UPDATE existing marks
            if edit_id:

                connection.execute("""
                    UPDATE marks
                    SET subject_id = ?,
                        marks_obtained = ?,
                        max_marks = ?
                    WHERE id = ?
                    AND user_id = ?
                """, (
                    subject_id,
                    marks_obtained,
                    max_marks,
                    edit_id,
                    session["user_id"]
                ))

            # INSERT / UPDATE marks
            else:

                connection.execute("""
                    INSERT INTO marks
                    (
                        user_id,
                        subject_id,
                        marks_obtained,
                        max_marks
                    )
                    VALUES (?, ?, ?, ?)

                    ON CONFLICT(user_id, subject_id)
                    DO UPDATE SET
                        marks_obtained = excluded.marks_obtained,
                        max_marks = excluded.max_marks
                """, (
                    session["user_id"],
                    subject_id,
                    marks_obtained,
                    max_marks
                ))

            connection.commit()

            connection.close()

            return redirect(url_for("marks"))

        except (ValueError, TypeError):

            error = "Please enter valid marks. Marks obtained must be between 0 and maximum marks."

    # Get subjects and marks
    subjects = connection.execute("""
        SELECT
            subjects.id,
            subjects.subject_code,
            subjects.subject_name,
            subjects.semester,
            marks.id AS mark_id,
            marks.marks_obtained,
            marks.max_marks
        FROM subjects
        LEFT JOIN marks
            ON subjects.id = marks.subject_id
            AND marks.user_id = ?
        WHERE subjects.user_id = ?
        ORDER BY subjects.semester, subjects.subject_code
    """, (
        session["user_id"],
        session["user_id"]
    )).fetchall()

    # Calculate percentage and grade
    subject_data = []

    for subject in subjects:

        item = dict(subject)

        if item["marks_obtained"] is not None and item["max_marks"]:

            percentage = (
                item["marks_obtained"] /
                item["max_marks"]
            ) * 100

            item["percentage"] = round(percentage, 2)

            # Grade system
            if percentage >= 90:
                item["grade"] = "A+"
            elif percentage >= 80:
                item["grade"] = "A"
            elif percentage >= 70:
                item["grade"] = "B+"
            elif percentage >= 60:
                item["grade"] = "B"
            elif percentage >= 50:
                item["grade"] = "C"
            elif percentage >= 40:
                item["grade"] = "D"
            else:
                item["grade"] = "F"

        else:

            item["percentage"] = None
            item["grade"] = None

        subject_data.append(item)

    # If editing, get the existing mark
    edit_mark = None

    if edit_id:

        edit_mark = connection.execute("""
            SELECT *
            FROM marks
            WHERE id = ?
            AND user_id = ?
        """, (
            edit_id,
            session["user_id"]
        )).fetchone()

    connection.close()

    return render_template(
        "marks.html",
        subjects=subject_data,
        error=error,
        edit_mark=edit_mark
    )   

@app.route("/marks/delete/<int:mark_id>", methods=["POST"])
def delete_mark(mark_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    connection.execute("""
        DELETE FROM marks
        WHERE id = ?
        AND user_id = ?
    """, (
        mark_id,
        session["user_id"]
    ))

    connection.commit()
    connection.close()

    return redirect(url_for("marks"))

@app.route("/performance")
def performance():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    # Get subjects with attendance and marks
    subjects = connection.execute("""
        SELECT
            subjects.id,
            subjects.subject_code,
            subjects.subject_name,
            subjects.semester,

            attendance.classes_conducted,
            attendance.classes_attended,

            marks.marks_obtained,
            marks.max_marks

        FROM subjects

        LEFT JOIN attendance
            ON subjects.id = attendance.subject_id
            AND attendance.user_id = ?

        LEFT JOIN marks
            ON subjects.id = marks.subject_id
            AND marks.user_id = ?

        WHERE subjects.user_id = ?

        ORDER BY subjects.semester, subjects.subject_code
    """, (
        session["user_id"],
        session["user_id"],
        session["user_id"]
    )).fetchall()

    subject_data = []

    total_conducted = 0
    total_attended = 0

    total_marks_obtained = 0
    total_max_marks = 0

    for subject in subjects:

        item = dict(subject)

        # Attendance percentage
        if (
            item["classes_conducted"] is not None
            and item["classes_conducted"] > 0
        ):

            attendance_percentage = (
                item["classes_attended"]
                / item["classes_conducted"]
            ) * 100

            item["attendance_percentage"] = round(
                attendance_percentage,
                2
            )

            total_conducted += item["classes_conducted"]
            total_attended += item["classes_attended"]

        else:

            item["attendance_percentage"] = None

        # Marks percentage and grade
        if (
            item["marks_obtained"] is not None
            and item["max_marks"] is not None
            and item["max_marks"] > 0
        ):

            marks_percentage = (
                item["marks_obtained"]
                / item["max_marks"]
            ) * 100

            item["marks_percentage"] = round(
                marks_percentage,
                2
            )

            # Grade calculation
            if marks_percentage >= 90:
                item["grade"] = "A+"
            elif marks_percentage >= 80:
                item["grade"] = "A"
            elif marks_percentage >= 70:
                item["grade"] = "B+"
            elif marks_percentage >= 60:
                item["grade"] = "B"
            elif marks_percentage >= 50:
                item["grade"] = "C"
            elif marks_percentage >= 40:
                item["grade"] = "D"
            else:
                item["grade"] = "F"

            total_marks_obtained += item["marks_obtained"]
            total_max_marks += item["max_marks"]

        else:

            item["marks_percentage"] = None
            item["grade"] = None

        # Combined performance
        if (
            item["attendance_percentage"] is not None
            and item["marks_percentage"] is not None
        ):

            item["performance_percentage"] = round(
                (
                    item["attendance_percentage"]
                    + item["marks_percentage"]
                ) / 2,
                2
            )

        elif item["marks_percentage"] is not None:

            item["performance_percentage"] = item["marks_percentage"]

        elif item["attendance_percentage"] is not None:

            item["performance_percentage"] = item["attendance_percentage"]

        else:

            item["performance_percentage"] = None

        subject_data.append(item)

    # Overall attendance
    if total_conducted > 0:

        overall_attendance = round(
            (total_attended / total_conducted) * 100,
            2
        )

    else:

        overall_attendance = None

    # Overall marks
    if total_max_marks > 0:

        overall_marks = round(
            (total_marks_obtained / total_max_marks) * 100,
            2
        )

    else:

        overall_marks = None

    # Overall performance
    if (
        overall_attendance is not None
        and overall_marks is not None
    ):

        overall_performance = round(
            (
                overall_attendance
                + overall_marks
            ) / 2,
            2
        )

    elif overall_marks is not None:

        overall_performance = overall_marks

    elif overall_attendance is not None:

        overall_performance = overall_attendance

    else:

        overall_performance = None

    connection.close()

    return render_template(
        "performance.html",
        subjects=subject_data,
        overall_attendance=overall_attendance,
        overall_marks=overall_marks,
        overall_performance=overall_performance
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