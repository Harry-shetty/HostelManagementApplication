# Nestora - Student Housing & Allocation System

Modular Django web application for university student housing management, roommate matching, and allocation governance with dedicated role separation.

## Development Server

Start the Django development server:

```bash
python3 manage.py runserver 8000
```

- Login: `http://127.0.0.1:8000/login/`
- Student Portal: `http://127.0.0.1:8000/`
- Warden Admin Workspace: `http://127.0.0.1:8000/admin-workspace/`
- Django Admin: `http://127.0.0.1:8000/django-admin/`

## Project Structure

```text
Django_project/
├── manage.py                  # Django CLI entrypoint
├── db.sqlite3                 # SQLite database
├── requirements.txt           # Python dependencies
│
├── nestora/                   # Project configuration
│   ├── settings.py            # Global settings & installed apps
│   ├── urls.py                # Main URL router
│   ├── wsgi.py / asgi.py      # WSGI/ASGI gateways
│
├── student/                   # Dedicated Student Portal App
│   ├── views.py               # Student views (overview, discovery, quiz, wizard, status)
│   ├── urls.py                # Student routes
│   ├── tests.py               # Student test suite
│   └── templates/student/     # Student portal HTML templates
│
├── admin/                     # Dedicated Warden Admin Workspace App
│   ├── apps.py                # Admin AppConfig (label='admin_portal')
│   ├── views.py               # Admin views (overview, bedmap, draft review, runs)
│   ├── urls.py                # Admin routes
│   ├── tests.py               # Admin test suite
│   └── templates/admin_panel/ # Admin workspace HTML templates
│
└── housing/                   # Core Housing Domain & Common Assets
    ├── models.py              # Housing & UserProfile models
    ├── admin.py               # Django admin registrations
    ├── decorators.py          # Role guards (@student_required, @admin_required)
    ├── views.py               # Authentication views (login, logout, context)
    ├── templatetags/          # Custom SVG icon template tags
    ├── static/                # CSS styling, JS interactions, favicon
    └── templates/             # Base layouts, login, and access denied screens
```

## User Roles & Credentials

- **Student Account:**
  - Username: `student` (or `STU-204810`)
  - Password: `student123`
  - Access: Student portal only (`/`, `/hostels/`, `/roommate/`, `/application/`, `/status/`).
  - Restricted from admin routes (displays 403 Access Denied).

- **Warden Administrator:**
  - Username: `admin`
  - Password: `admin123`
  - Access: Full Warden Admin workspace (`/admin-workspace/`, `/inventory/`, `/draft/`, `/runs/`) & Django Admin (`/django-admin/`).

## Database & Testing

```bash
# Seed initial demo data
python3 manage.py seed_data

# Run tests across all apps
python3 manage.py test
```
