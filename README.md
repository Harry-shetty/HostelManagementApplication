# Nestora Student Housing Platform (Django Framework)

Nestora is a university student housing and allocation management system built on the **Django Framework** with a **clean, modular app architecture** and **strict role-based separation**.

---

## Architecture & App Separation

The codebase is organized into dedicated, self-contained apps:

- **`student/`** - Dedicated Student Portal app:
  - Views, URLs, and templates for Hostel Discovery, Roommate Matching quiz, Multi-step Application Wizard, and Allocation Status.
- **`admin/`** - Dedicated Warden Admin Workspace app:
  - Views, URLs, and templates for Administrative Overview, Interactive Bed Map, Draft Allocation Review, and Governance Runs.
- **`housing/`** - Shared domain models, authentication controllers, role guards, SVG template tags, and common assets.
- **`nestora/`** - Main Django project configuration package (`settings.py`, `urls.py`).

Root directory contains only essential project files:
- `manage.py`
- `db.sqlite3`
- `requirements.txt`
- App packages: `nestora/`, `student/`, `admin/`, `housing/`

---

## User Roles & Authentication

1. **Student Role**:
   - Access: **Student Portal** only (`/`, `/hostels/`, `/roommate/`, `/application/`, `/status/`).
   - If a student tries to access admin-only routes, they are blocked with a styled **403 Access Denied** screen.
   - **Default Student Login:** `student` / `student123`

2. **Warden Admin Role**:
   - Access: Full **Warden Admin Workspace** (`/admin-workspace/`, `/inventory/`, `/draft/`, `/runs/`) and Django Administration (`/django-admin/`).
   - **Default Admin Login:** `admin` / `admin123`

---

## Quick Start (Terminal Commands)

No virtual environment (`venv`) needed — run directly with your system `python3`:

### 1. Seed or Reset Campus Data
```bash
python3 manage.py seed_data
```

### 2. Start the Development Server
```bash
python3 manage.py runserver 8000
```

### 3. Open in Browser
- **Sign In Page:** [http://127.0.0.1:8000/login/](http://127.0.0.1:8000/login/) (includes 1-click demo login buttons)
- **Student Portal:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Warden Admin Workspace:** [http://127.0.0.1:8000/admin-workspace/](http://127.0.0.1:8000/admin-workspace/)
- **Django Admin Site:** [http://127.0.0.1:8000/django-admin/](http://127.0.0.1:8000/django-admin/)

---

## Automated Test Suite

Run unit and integration tests across all apps:
```bash
python3 manage.py test
```
