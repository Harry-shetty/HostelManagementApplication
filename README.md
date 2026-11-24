# Nestora — University Student Housing & Allocation System

<p align="center">
  <img src="frontend/static/logo.svg" alt="Nestora Logo" width="88" height="88">
</p>

<p align="center">
  <strong>An intelligent, university-grade student housing management, roommate compatibility matching, and quota allocation platform.</strong>
</p>

<p align="center">
  <a href="#features"><img src="https://img.shields.io/badge/Django-5.1-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django"></a>
  <a href="#features"><img src="https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"></a>
  <a href="#features"><img src="https://img.shields.io/badge/PostgreSQL-Neon_Cloud-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL"></a>
  <a href="#features"><img src="https://img.shields.io/badge/Real--Time-Socket.IO-010101?style=for-the-badge&logo=socketdotio&logoColor=white" alt="Socket.IO"></a>
  <a href="#features"><img src="https://img.shields.io/badge/Theme-Light%20%26%20Dark%20Mode-c8f169?style=for-the-badge&logoColor=103a2e" alt="Theme Support"></a>
  <a href="#license"><img src="https://img.shields.io/badge/License-Academic%20Use-green?style=for-the-badge" alt="License"></a>
</p>

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [User Roles & Access Control](#user-roles--access-control)
- [Live Synchronization & Socket.IO](#live-synchronization--socketio)
- [Theme Engine (Light & Dark Mode)](#theme-engine-light--dark-mode)
- [Quick Start Guide](#quick-start-guide)
- [Database Configuration](#database-configuration)
- [Testing & Quality Assurance](#testing--quality-assurance)
- [Directory Structure](#directory-structure)
- [Security & Governance](#security--governance)
- [License](#license)

---

## Overview

**Nestora** is a single-tenant, modular web application built for higher-education residential governance. It replaces archaic paper-based forms and spreadsheet tracking with an auditable, algorithmically governed platform that addresses:

1. **Student Housing Discovery:** Search, filter, and inspect campus dormitories with real-time seat inventory, floor amenities, and price tier structures.
2. **Roommate Compatibility Profiling:** Privacy-by-design questionnaire calculating compatibility scores across sleep schedules, cleanliness, noise tolerances, and study habits.
3. **Application Lifecycle & Mandatory Prerequisite Barrier:** Step-by-step application wizard guarded by prerequisite locks preventing premature submissions without roommate profiling.
4. **Administrative Allocation Engine:** Seed-locked algorithmic draft batches (`reproducibility_seed`) with automated exception reporting and audit trails.
5. **Post-Allocation Governance:** Digitally signed official allotment letters, real-time spatial bed map, and hostel change cart with instant ledger reconciliations.

---

## Key Features

### 🏢 Student Portal
- **Hostel Catalog & Explorer:** Real-time search with filter facets by bathroom style, catering options, AC cooling, and semester budgets.
- **Roommate Matching Engine:** Multi-factor lifestyle questionnaire with encrypted responses and voluntary match browsing.
- **Prerequisite Application Gate:** Full barrier preventing application access until roommate habits are confirmed.
- **6-Step Application Wizard:** Profile verification, eligibility criteria, hostel priority rankings, room preferences, document uploads, and final submission.
- **Allocation Status Tracker:** Real-time status pipeline (*Submitted → Under Review → Allocated / Waitlisted*), official allotment download, and room change appeals.
- **Hostel Change & Cart Settlement:** Self-service room reassignment request with real-time ledger differential calculations.

### 🛡️ Warden Administrator Workspace
- **Executive Operations Dashboard:** Real-time KPIs for campus bed occupancy, quota allocations, medical exception counts, and pending transfers.
- **Interactive Visual Bed Map:** Spatial floor-by-floor room grid showing student names, occupancy status (Occupied, Reserved, Vacant), and instant bed swap actions.
- **Draft Allocation Review:** Algorithmic run audits, manual override controls, student profile deep-dives, and one-click bulk allotment publishing.
- **Allocation Run Governance:** Historical run records (`AR-2025-04`), reproducibility seed verification, policy rule sets, and unallocated queue triage.
- **Immutable Audit Trail:** Append-only transaction logging tracking administrative overrides, room swaps, and application status changes.

---

## System Architecture

Nestora follows a strict **Separation of Concerns (SoC)** separating core domain logic, student workflows, admin workspaces, and frontend assets into decoupled modules:

```text
                                 [ Client Browser ]
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   ▼                                           ▼
          [ HTTP / REST APIs ]                        [ WebSocket Engine ]
            (Django WSGI)                              (python-socketio)
                   │                                           │
       ┌───────────┴───────────┐                               │
       ▼                       ▼                               ▼
 [ Student App ]        [ Admin Portal ]             [ Real-Time Events ]
 (Hostels, Quiz,        (Bed Map, Runs,              (Live Bed Reassignments,
  Application)           Draft Review)                Toast Notifications)
       │                       │                               │
       └───────────┬───────────┘                               │
                   ▼                                           │
         [ Housing Domain Core ] ◄─────────────────────────────┘
         (Models, Guards, Signals, RBAC)
                   │
                   ▼
         [ PostgreSQL / SQLite3 ]
```

---

## User Roles & Access Control

Nestora implements strict **Role-Based Access Control (RBAC)** enforced through Django decorators (`@student_required`, `@admin_required`) and session role validation.

| Feature / Route | Student Portal (`student`) | Warden Admin (`admin`) | Django Superuser |
| :--- | :---: | :---: | :---: |
| **Browse Hostels (`/hostels/`)** | ✅ Allowed | ✅ Allowed | ✅ Allowed |
| **Roommate Matching (`/roommate/`)** | ✅ Allowed | ❌ Denied (403) | ✅ Allowed |
| **Housing Application (`/application/`)** | ✅ Allowed | ❌ Denied (403) | ✅ Allowed |
| **Allocation Status (`/status/`)** | ✅ Allowed | ❌ Denied (403) | ✅ Allowed |
| **Hostel Change Cart (`/hostel-change/`)** | ✅ Allowed | ❌ Denied (403) | ✅ Allowed |
| **Warden Dashboard (`/admin-workspace/`)** | ❌ Blocked (403) | ✅ Allowed | ✅ Allowed |
| **Interactive Bed Map (`/bedmap/`)** | ❌ Blocked (403) | ✅ Allowed | ✅ Allowed |
| **Draft Allocation Review (`/draft/`)** | ❌ Blocked (403) | ✅ Allowed | ✅ Allowed |
| **Allocation Governance Runs (`/runs/`)** | ❌ Blocked (403) | ✅ Allowed | ✅ Allowed |
| **Django Admin Site (`/django-admin/`)** | ❌ Blocked (403) | ✅ Allowed | ✅ Allowed |

### Default Demo Credentials

| Role | Username | Password | Default Landing Page |
| :--- | :--- | :--- | :--- |
| **Student** | `student` *(or `STU-204810`)* | `student123` | `http://127.0.0.1:8000/` |
| **Warden Admin** | `admin` | `admin123` | `http://127.0.0.1:8000/admin-workspace/` |

---

## Live Synchronization & Socket.IO

Nestora features bi-directional event distribution via **python-socketio**:

- **Real-Time Bed Map Sync:** Whenever an administrator overrides a bed assignment or approves an allotment, the change reflects on all active screens without refreshing.
- **Global Toast Broadcaster:** Dynamic notification toasts inform students and wardens of allotment publications and waitlist promotions.
- **Activity Stream:** Live audit feed tracks actions across the residential campus in real time.
- **Live Connection Pill:** Active heartbeat indicator displays real-time connectivity status.

---

## Theme Engine (Light & Dark Mode)

Nestora includes a zero-dependency, high-contrast theme switching engine built on CSS custom properties:

- **Clean Light Mode (Default):** Warm Ivory background (`#f8f7f2`), pure white elevated cards (`#ffffff`), and Nestora forest green branding (`#174c3c`).
- **Deep Forest Dark Mode:** Tailored dark night palette (`#0b1511`) with dark pine surfaces (`#12221b`) and vivid electric lime accents (`#c8f169`).
- **Instant Persistence:** Theme preferences are stored in `localStorage` and applied before initial HTML rendering in `<head>` to prevent Flash of Unstyled Content (FOC).
- **Accessible Controls:** Theme toggle buttons available on desktop navigation, mobile headers, and sign-in screens.

---

## Quick Start Guide

### 1. Prerequisites
- Python 3.10+ (Tested through Python 3.14)
- PostgreSQL (or local SQLite for zero-config testing)
- pip package manager

### 2. Installation & Setup

Clone the repository and install required dependencies:

```bash
git clone https://github.com/Harry-shetty/HostelManagementApplication.git
cd HostelManagementApplication
pip install -r requirements.txt
```

### 3. Database Migration & Data Seeding

Apply database migrations and populate realistic campus demo records:

```bash
# Run database schema migrations
python3 manage.py migrate

# Seed comprehensive demo campus data (hostels, rooms, beds, students, applications)
python3 manage.py seed_data
```

### 4. Run Development Server

```bash
python3 manage.py runserver 8000
```

Visit the application in your browser:
- **Sign In (with 1-click demo logins):** [http://127.0.0.1:8000/login/](http://127.0.0.1:8000/login/)
- **Student Portal:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Warden Admin Workspace:** [http://127.0.0.1:8000/admin-workspace/](http://127.0.0.1:8000/admin-workspace/)
- **Django Admin Site:** [http://127.0.0.1:8000/django-admin/](http://127.0.0.1:8000/django-admin/)

---

## Database Configuration

Nestora defaults to SQLite for immediate out-of-the-box development, and natively supports cloud-hosted PostgreSQL (Neon Database) for production workloads.

Configure your database in `.env` or system environment variables:

```env
# Cloud / Production PostgreSQL (e.g. Neon, AWS RDS, Supabase)
DATABASE_URL=postgresql://user:password@ep-sample-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require

# Or Individual Parameters
DB_ENGINE=postgresql
DB_NAME=nestora
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

---

## Testing & Quality Assurance

Nestora includes comprehensive test suites across both student and warden workflows.

```bash
# Run all tests across backend apps
python3 manage.py test

# Run tests reusing existing database (faster execution)
python3 manage.py test --keepdb

# Target specific modules
python3 manage.py test student --keepdb
python3 manage.py test admin --keepdb
```

---

## Directory Structure

```text
Django_project/
├── manage.py                          # Root Django CLI entrypoint
├── requirements.txt                   # Production Python dependencies
├── README.md                          # Comprehensive project documentation
├── AGENTS.md                          # Agent instructions & workspace rules
│
├── backend/                           # Django Backend Architecture
│   ├── nestora/                       # Core Project Configuration
│   │   ├── settings.py                # Global settings, paths & database config
│   │   ├── urls.py                    # Root URL router
│   │   ├── test_runner.py             # Custom backend/ test discoverer
│   │   └── wsgi.py / asgi.py          # WSGI & ASGI production gateways
│   │
│   ├── student/                       # Student Portal App
│   │   ├── views.py                   # Catalog, quiz, wizard, and status views
│   │   ├── urls.py                    # Student routes
│   │   └── tests.py                   # Student test suite
│   │
│   ├── admin/                         # Warden Admin Workspace App
│   │   ├── apps.py                    # AdminPortalConfig (label='admin_portal')
│   │   ├── views.py                   # Bedmap, draft review, runs, audit views
│   │   ├── urls.py                    # Admin routes
│   │   └── tests.py                   # Admin test suite
│   │
│   └── housing/                       # Shared Housing Domain
│       ├── models.py                  # Hostel, Room, Bed, Student, Application, Audit models
│       ├── admin.py                   # Django admin model registrations
│       ├── decorators.py              # Role guards (@student_required, @admin_required)
│       ├── auth_backend.py            # Optimized cached authentication backend
│       ├── views.py                   # Login, signup, authentication controllers
│       ├── management/commands/       # seed_data script
│       └── templatetags/              # Custom SVG icon and logo tags
│
└── frontend/                          # Presentation Layer
    ├── templates/                     # HTML Templates (Django Template Language)
    │   ├── base.html                  # Global shell, navigation, theme script & modal layer
    │   ├── housing/                   # Login, signup, 403 access denied screens
    │   ├── student/                   # Overview, hostels, roommate, application, status
    │   └── admin_panel/               # Admin overview, bedmap, draft review, runs
    └── static/                        # Static Assets
        ├── css/style.css              # Unified design system & responsive stylesheets
        ├── js/main.js                 # Theme engine, modals, drawer, and Socket.IO client
        ├── js/socket.io.min.js        # Socket.IO client library
        ├── favicon.svg                # Brand icon
        └── logo.svg                   # Brand mark
```

---

## Security & Governance

- **CSRF Protection:** All mutating endpoints require cryptographic CSRF verification (`{% csrf_token %}` and `X-CSRFToken` request headers).
- **Session Isolation:** Student and administrator sessions are isolated; role escalation attempts are logged and rejected with HTTP 403.
- **Prerequisite Locking:** Multi-tier verification ensures applications cannot be finalized without authenticated student verification and roommate profiling.
- **Immutable Audit Trail:** Critical operations (room reassignments, quota modifications, publishing runs) are recorded to the database audit ledger with actor and timestamp.

---

## License

This project is developed for university academic evaluation and hostel administration research. All rights reserved.
