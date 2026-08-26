# Authentication Module

## Overview

The authentication module handles student registration, login,
logout, user sessions, profile access, and password security.

## Features

### 1. Student Registration

Students can create an account by providing:

- Full name
- Student ID
- Email
- Course
- Semester
- Password

The application checks required fields and prevents duplicate
email addresses and student IDs.

### 2. Password Security

Passwords are never stored as plain text.

The application uses Werkzeug password hashing:

```python
generate_password_hash()