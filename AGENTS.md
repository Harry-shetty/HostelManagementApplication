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
- Real-Time Live Sync: Socket.IO enabled at `/socket.io/`

## Project Structure

```text
Django_project/
├── manage.py                  # Root Django CLI entrypoint (adds backend/ to sys.path)
├── db.sqlite3                 # SQLite database
├── requirements.txt           # Python dependencies
│
├── backend/                   # Backend: Django Project Configuration & Apps
│   ├── nestora/               # Project configuration
│   │   ├── settings.py        # Global settings, frontend paths & installed apps
│   │   ├── urls.py            # Main URL router
│   │   ├── test_runner.py     # Custom test runner for backend/ discovery
│   │   └── wsgi.py / asgi.py  # WSGI/ASGI gateways
│   │
│   ├── student/               # Dedicated Student Portal App
│   │   ├── views.py           # Student views (overview, discovery, quiz, wizard, status, profile)
│   │   ├── urls.py            # Student routes
│   │   └── tests.py           # Student test suite
│   │
│   ├── admin/                 # Dedicated Warden Admin Workspace App
│   │   ├── apps.py            # Admin AppConfig (label='admin_portal')
│   │   ├── views.py           # Admin views (overview, bedmap, draft review, runs, profile)
│   │   ├── urls.py            # Admin routes
│   │   └── tests.py           # Admin test suite
│   │
│   └── housing/               # Core Housing Domain & Shared Logic
│       ├── models.py          # Housing & UserProfile models
│       ├── admin.py           # Django admin registrations
│       ├── decorators.py      # Role guards (@student_required, @admin_required)
│       ├── views.py           # Authentication views (login, logout, context)
│       ├── management/        # Custom commands (seed_data)
│       └── templatetags/      # Custom SVG icon template tags
│
└── frontend/                  # Frontend: Templates, Styling, Scripts & Static Assets
    ├── templates/             # HTML templates (configured in TEMPLATES['DIRS'])
    │   ├── base.html          # Shared base layout & navigation
    │   ├── housing/           # Login & access denied screens
    │   ├── student/           # Student portal HTML templates
    │   └── admin_panel/       # Admin workspace HTML templates
    └── static/                # Static files (configured in STATICFILES_DIRS)
        ├── css/               # Stylesheets
        ├── js/                # Client-side scripts
        └── *.svg / *.png      # Brand logos & favicon
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
# Seed initial SQL demo data
python3 manage.py seed_data

# Seed MongoDB Atlas 'nestora' database & collections
python3 manage.py seed_mongodb --uri="mongodb+srv://<user>:<password>@cluster.mongodb.net/nestora?retryWrites=true&w=majority"

# Run tests across all apps
python3 manage.py test
```
