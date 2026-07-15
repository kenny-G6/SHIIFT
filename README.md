# Shiift — On-Demand Healthcare Staffing Marketplace

Shiift is a two-sided marketplace web application connecting healthcare **facilities** with on-demand healthcare **workers** across Nigeria — conceptually similar to platforms like Clipboard Health, built for the Nigerian healthcare staffing market.

> ⚠️ **Status:** In active development. Not yet deployed — see [Running Locally](#running-locally) below to try it, or the [demo walkthrough video](#demo) for a full tour without needing to set anything up.

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

*(Add screenshots here — worker dashboard, facility shift posting, admin panel, etc. Even 3–4 images make the repo far easier for a reviewer to evaluate at a glance.)*

| Worker Portal | Facility Portal | Admin Panel |
|---|---|---|
| _screenshot_ | _screenshot_ | _screenshot_ |

---

## Demo

A full walkthrough video is available here: **[add your video link once recorded]**

The video covers the worker, facility, and admin flows end-to-end, since the app isn't deployed yet.

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
