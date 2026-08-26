# TaskFlow

TaskFlow is a responsive task-management web application developed for the SD204B Software Development project.

It allows registered users to create, manage, prioritise, complete, drop, review, and track personal tasks through a dashboard, task list, history page, notifications, and profile features.

## Technology Stack

### Backend
- Python
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Flask-WTF
- Flask-Migrate
- Alembic

### Frontend
- HTML
- Jinja2
- Bootstrap
- Bootstrap Icons
- Custom CSS
- Vanilla JavaScript

### Database
- PostgreSQL

### Testing
- pytest
- SQLite temporary test databases

---

## Main Features

TaskFlow includes:

- User registration and login
- Secure password hashing
- Remember Me
- Protected routes
- User-specific task ownership
- Create tasks
- View task details
- Edit tasks
- Complete tasks
- Reopen completed tasks
- Drop tasks
- Four task statuses:
  - Yet-to-do
  - On-going
  - Finished
  - Dropped
- Three priorities:
  - High
  - Medium
  - Low
- Scheduled dates
- Due dates
- Overdue task detection
- Carry-over unfinished tasks
- Early task completion tracking
- Dashboard statistics
- Daily progress
- Task search
- Status filters
- Priority filters
- Due-date filtering
- Task History
- History search
- Remarks
- Reflection
- Task review
- Notifications
- User profile
- Personal task statistics
- Responsive desktop, tablet, and mobile layouts

---

## Project Structure

```text
TaskFlow/
│
├── backend/
│   ├── app.py
│   ├── auth.py
│   ├── extensions.py
│   ├── main.py
│   ├── models.py
│   ├── notifications.py
│   ├── profile_routes.py
│   ├── task_routes.py
│   │
│   ├── migrations/
│   ├── static/
│   ├── templates/
│   ├── tests/
│   │
│   ├── .env
│   ├── .env.example
│   └── requirements.txt
│
└── README.md
```

---

# Local Setup

## 1. Clone the Repository

```powershell
git clone https://github.com/ars1224/TaskFlow.git
cd TaskFlow\backend
```

---

## 2. Create a Virtual Environment

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

The terminal should then display:

```text
(.venv)
```

---

## 3. Install Requirements

```powershell
python -m pip install -r requirements.txt
```

---

# PostgreSQL Setup

TaskFlow uses PostgreSQL as its main database.

Make sure PostgreSQL is installed and running.

Connect to PostgreSQL:

```powershell
psql -U postgres
```

Create the TaskFlow database user:

```sql
CREATE USER taskflow_user
WITH PASSWORD 'your-secure-password';
```

Create the database:

```sql
CREATE DATABASE taskflow
OWNER taskflow_user;
```

Exit PostgreSQL:

```sql
\q
```

---

# Environment Variables

Copy the example environment file:

```powershell
Copy-Item .env.example .env
```

Configure `.env` with your own values:

```env
SECRET_KEY=your-generated-secret-key

DB_HOST=localhost
DB_PORT=5432
DB_NAME=taskflow
DB_USER=taskflow_user
DB_PASSWORD=your-database-password

FLASK_DEBUG=false
```

The real `.env` file must not be committed to Git.

---

## Generate a Secret Key

Generate a strong Flask secret:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copy the generated value into:

```env
SECRET_KEY=
```

TaskFlow will not start if `SECRET_KEY` is missing.

---

# Database Migrations

TaskFlow uses Flask-Migrate and Alembic for database schema management.

Apply the migrations:

```powershell
python -m flask --app app db upgrade
```

Check the current migration:

```powershell
python -m flask --app app db current
```

The current migration should show:

```text
cc73f30e669c (head)
```

The normal PostgreSQL database schema is managed through migrations.

---

# Run TaskFlow

From the `backend` directory:

```powershell
python app.py
```

TaskFlow will normally run at:

```text
http://127.0.0.1:5000
```

Open this address in your browser.

---

# Health Checks

## Application Health

```text
/api/health
```

Expected response:

```json
{
  "message": "TaskFlow is running",
  "status": "success"
}
```

## Database Health

```text
/api/database-health
```

This endpoint checks whether TaskFlow can successfully connect to PostgreSQL.

---

# Automated Testing

TaskFlow uses pytest for automated functional, validation, and security testing.

Run all tests with:

```powershell
python -m pytest -v
```

The current automated test suite contains:

```text
35 tests
```

The tests cover:

- Registration
- Login
- Invalid login
- Duplicate registration
- Logout
- Remember Me
- Protected routes
- Task creation
- Task viewing
- Task editing
- Task completion
- Task reopening
- Task dropping
- Task search
- History search
- Status filtering
- Priority filtering
- Due-date filtering
- Multiple filters
- Validation
- Dashboard counts
- Daily progress
- Overdue tasks
- Carry-over tasks
- Early task completion
- Task History
- Remarks
- Reflection
- Task Review
- User task isolation

Automated tests use temporary SQLite databases and do not modify the main PostgreSQL development database.

---

# Task Lifecycle

TaskFlow stores four task statuses:

```text
yet-to-do
on-going
completed
dropped
```

## Yet-to-do

Future tasks remain Yet-to-do until their scheduled date arrives.

## On-going

Tasks scheduled for today or unfinished tasks carried over from previous days are On-going.

## Finished

Finished tasks use `completed_at` to record the date and time they were actually completed.

A future task completed early keeps its original scheduled date but counts as an accomplishment on the actual completion day.

## Dropped

Dropping a task does not permanently delete it.

The task remains stored in the database with:

```text
status = dropped
```

---

# Overdue Tasks

Overdue is calculated dynamically and is not stored as a separate database status.

A task is overdue when:

```text
due_date < today
```

and its status is not:

```text
completed
dropped
```

An overdue active task remains On-going.

---

# Security

TaskFlow includes:

- Password hashing
- Flask-Login authentication
- Protected routes
- CSRF protection
- HTTP-only session cookies
- HTTP-only Remember Me cookies
- SameSite cookie protection
- User-specific task queries
- Task ownership checks
- Environment-based `SECRET_KEY`
- `.env` excluded from Git

---

# Responsive Design

TaskFlow supports:

- Desktop
- Tablet
- Mobile
- Small mobile screens down to 320px

Responsive testing includes:

- Dashboard
- Task List
- Task History
- Profile
- Task modals
- Navigation
- Notifications

---

# Git Workflow

Check changed files:

```powershell
git status
```

Stage changes:

```powershell
git add .
```

Commit:

```powershell
git commit -m "Update TaskFlow documentation"
```

Push:

```powershell
git push
```

The `.env` file must remain ignored and must never be committed.

---

# Project Status

The core TaskFlow application currently supports the required authentication, task-management, dashboard, search, filtering, history, reflection, notification, profile, and responsive-interface features.

The automated test suite currently passes:

```text
35 tests
```

Additional SD204B assessment work includes formal testing evidence, browser compatibility evidence, requirements traceability, diagrams, documentation, and final submission materials.

---

# Author

Jhon Aries Tayao

SD204B Software Development Project