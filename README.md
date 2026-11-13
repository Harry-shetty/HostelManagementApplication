# Nestora Student Housing Platform (Django Framework)

Nestora is a university student housing and allocation management system built on the **Django Framework** with a **clean, modular app architecture** and **strict role-based separation**.

---

## Architecture & App Separation

The codebase separates **backend** logic from **frontend** presentation into dedicated top-level directories:

- **`backend/`** - Django project & application logic:
  - **`backend/student/`** - Views, URLs, and tests for Hostel Discovery, Roommate Matching quiz, Multi-step Application Wizard, Allocation Status, and Student Profile.
  - **`backend/admin/`** - Views, URLs, and tests for Administrative Overview, Interactive Bed Map, Draft Allocation Review, Governance Runs, and Warden Profile.
  - **`backend/housing/`** - Shared domain models, authentication controllers, role guards, management commands, and SVG template tags.
  - **`backend/nestora/`** - Main Django project configuration package (`settings.py`, `urls.py`, `test_runner.py`, `wsgi.py`, `asgi.py`).
- **`frontend/`** - All UI templates and static assets:
  - **`frontend/templates/`** - Base layout, authentication screens (`housing/`), student portal (`student/`), and admin workspace (`admin_panel/`).
  - **`frontend/static/`** - CSS stylesheets, client-side JavaScript, brand logos, and favicon.

Root directory contains only essential entrypoints and project metadata:
- `manage.py`
- `db.sqlite3`
- `requirements.txt`
- `backend/` and `frontend/` directories

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

---

## Real-Time Live Sync (Socket.IO)

Nestora integrates **Socket.IO** (`python-socketio` + client-side `socket.io.min.js`) for instant bi-directional updates:

- **Live Bed Inventory Sync**: Bed reassignments and occupancy updates reflect instantly on the Bed Map without page refreshes.
- **Real-Time Notification Toasts**: Floating animated alerts broadcast in-app notifications to student and warden portals.
- **Warden Activity Feeds**: Live audit logs and allocation overrides update the administrative timeline in real time.
- **Connection Indicator**: Visible `LIVE` status pill indicates real-time socket connectivity state.

---

## PostgreSQL Database Configuration (Track P)

Nestora uses PostgreSQL as its primary relational database with native ACID transactions and constraints:

1. **Configure Connection**: Add your PostgreSQL connection details to `.env`:
   ```env
   # Option A: Full Connection URI
   DATABASE_URL=postgres://postgres:password@localhost:5432/nestora

   # Option B: Individual parameters
   DB_ENGINE=postgresql
   DB_NAME=nestora
   DB_USER=postgres
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=5432
   ```

2. **Run Migrations & Seed Data**:
   ```bash
   python3 manage.py migrate
   python3 manage.py seed_data
   ```

   Populates all housing inventory, students, bed allocations, applications, and roommate compatibility profiles.
