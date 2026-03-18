# Maghettoni

A property management system built for Tanzanian landlords. Manage properties, units, tenants, payments, and maintenance requests from a single dashboard — with Swahili-first UI and Nairobi timezone support.

---

## Features

- **Dashboard** — revenue trends, occupancy rates, overdue payments, emergency maintenance alerts
- **Properties** — create and manage multiple properties with images, types, and unit counts
- **Units** — track individual units per property: rent, bedrooms, bathrooms, occupancy status
- **Tenants** — full tenant lifecycle (active/pending/inactive), emergency contacts, move-in/out dates
- **Payments** — record payments with method (Cash, Mobile Money, Bank Transfer, etc.), status tracking, and reference numbers
- **Maintenance** — priority-based request tracking (low/medium/high/emergency) with cost estimates
- **Search** — cross-entity search across properties, tenants, payments, and maintenance
- **Notifications** — per-user alert system
- **Authentication** — email/password registration with activation, Google OAuth2, password reset
- **Lead Generation** — phone OTP verification, assessment form, newsletter subscriptions

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5.2 |
| Database | SQLite (dev) |
| Auth | Django auth + Google OAuth2 (`social-auth-app-django`) |
| Frontend | Tailwind CSS (CDN), Chart.js, HTMX, Font Awesome |
| Forms | django-widget-tweaks |
| Static files | WhiteNoise |
| Images | Pillow |
| CORS | django-cors-headers |
| Email | Gmail SMTP |

---

## Project Structure

```
maghettoni/
├── maghettoni/          # Project config, settings, URL root, OAuth pipeline
├── yuzzaz/              # User auth — custom user model, registration, profiles
├── dashboardd/          # Core app — properties, units, tenants, payments, maintenance
├── tathmini/            # Lead gen — OTP verification, assessment forms, newsletter
├── static/              # JS and CSS
│   └── js/
│       ├── dashboardd.js    # Revenue chart, Swahili greetings, animated counters
│       ├── base.js          # Toast notifications
│       └── head-yuzzaz.js   # Auth page utilities
├── media/               # User-uploaded files (property images, tenant photos)
└── db.sqlite3
```

---

## Setup

### 1. Clone and create virtual environment

```bash
git clone <repo-url>
cd maghettoni
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install django pillow django-widget-tweaks django-cors-headers whitenoise \
            social-auth-app-django
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
GOOGLE_CLIENT_ID=your-google-oauth-client-id
GOOGLE_CLIENT_SECRET=your-google-oauth-client-secret
```

### 4. Run migrations

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5. Collect static files (production)

```bash
python manage.py collectstatic
```

### 6. Start the server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000`

---

## URL Overview

| Prefix | Description |
|--------|-------------|
| `/` | Landing page |
| `/home/` | Auth routes (register, login, profile, password reset) |
| `/dashboard/` | Main app — CRUD for all property entities |
| `/dashboard/api/` | JSON endpoints for dynamic form interactions |
| `/tathmini/` | OTP API, assessment submission, newsletter |
| `/admin/` | Django admin panel |
| `/oauth/` | Google OAuth2 |

---

## Environment Notes

- **Timezone:** `Africa/Nairobi`
- **Currency:** TZS (Tanzanian Shilling) formatting in charts
- **Language:** Swahili-first labels, status names, and property types
- `DEBUG = True` and `CORS_ALLOW_ALL_ORIGINS = True` — restrict both before deploying to production
- `ALLOWED_HOSTS` includes `maghettoni.com` and `www.maghettoni.com`

---

## Admin

All models are registered with Django admin. Access at `/admin/` after creating a superuser.

Models available in admin: `CustomUser`, `Property`, `Unit`, `Tenant`, `Payment`, `MaintenanceRequest`, `Notification`, `PhoneVerification`, `AssessmentSubmission`, `Subscriber`
