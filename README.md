# Shiift — On-Demand Healthcare Staffing Marketplace

Shiift is a two-sided marketplace web application connecting healthcare **facilities** with on-demand healthcare **workers** across Nigeria — conceptually similar to platforms like Clipboard Health.

> ⚠️ **Status:** In active development. Not yet deployed — see [Running Locally](#running-locally) below to try it, or the [demo walkthrough video](#demo) for a full tour without needing to set up locally.

---

## Overview

Healthcare facilities in Nigeria often face last-minute staffing gaps, while qualified healthcare workers lack a reliable way to pick up flexible shifts. Shiift solves this by giving:

- **Facilities** a way to post open shifts and book verified workers
- **Workers** a way to browse, accept, and manage shifts around their schedule
- **Admins** oversight across users, bookings, payments, and platform activity

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask (app factory + blueprints) |
| Database | MySQL, SQLAlchemy ORM, Flask-Migrate |
| Forms & Auth | Flask-WTF, CSRF protection, session-based auth |
| Templating | Jinja2 |
| Frontend | Bootstrap 5, jQuery, custom design system |

---

## Key Features

- **Three distinct portals** — Worker, Facility, and Admin — each with role-based access and dedicated views
- **Shift booking system** — post, browse, accept, and track shifts end-to-end
- **Relational data model** covering Facilities, Workers, Shifts, Bookings, Payments, Reviews, and Worker Locations (10+ tables)
- **Consistent design system** — custom color palette (Deep Teal / Mint Green), typography (Baloo 2 / Poppins), and reusable UI components across 20+ page templates
- **Version-controlled schema** via Flask-Migrate, so the database evolves safely alongside the codebase

---

## Architecture

Shiift follows a Flask **application factory + blueprint** structure to keep the codebase modular as it grows:

```
shiift/
├── app/
│   ├── __init__.py          # App factory
│   ├── models.py            # SQLAlchemy models
│   ├── auth/                # Auth blueprint
│   ├── worker/               # Worker portal blueprint
│   ├── facility/             # Facility portal blueprint
│   ├── admin/                 # Admin portal blueprint
│   ├── templates/
│   └── static/
├── migrations/               # Flask-Migrate version history
├── config.py
└── run.py
```

---

## Screenshots

### Worker Portal — Browse & Book Shifts
![Worker Portal](./screenshots/01-worker-dashboard.png)
Workers can browse available shifts in their area, view their booking history, track payouts, and manage their schedule.

### Facility Portal — Post & Manage Shifts
![Facility Portal](./screenshots/02-facility-dashboard.png)
Facilities get an overview of open and filled shifts, post new shifts, and manage applicants and bookings.

### Admin Panel — Central Operations
![Admin Dashboard](./screenshots/03-admin-dashboard.png)
Admins oversee pending verifications, manage the escrow ledger, track worker payouts, and monitor platform activity.

### Admin Login — Role-Based Access
![Admin Login](./screenshots/04-admin-login.png)
Secure login page for admin control panel with role-based access and monitoring.

---

## Demo

A full walkthrough video will be available here soon: **[add your video link once recorded]**

The video will cover the worker, facility, and admin flows end-to-end, since the app isn't deployed yet.

---

## Running Locally

```bash
# Clone the repo
git clone https://github.com/kenny-G6/SHIIFT.git
cd SHIIFT

# Set up a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env          # then fill in your MySQL credentials

# Set up the database
flask db upgrade

# Run the app
flask run
```

Visit `http://127.0.0.1:5000` in your browser.

---

## Roadmap

- [ ] Deploy to production (Render/Railway)
- [ ] Payment gateway integration
- [ ] SMS/WhatsApp shift notifications
- [ ] Mobile-responsive PWA support

---

## Author

**Kehinde Awe** — Full-stack developer, Ibadan, Nigeria
GitHub: [@kenny-G6](https://github.com/kenny-G6)
