# Dental Clinic API — README

This README explains how to set up and run the **Dental Clinic API** project on **Windows** and **Linux / macOS** for development and quick local testing.

> **Quick summary:** This is a Django REST Framework project with multiple apps (accounts, appointments, billing, medical, operations, payroll, pharmacy). It exposes OpenAPI docs (Swagger / Redoc) and a JSON schema. The project ships with `manage.py` and a `requirements.txt` for dependencies.

---

## Contents

* Project overview
* Prerequisites
* Setup (Linux / macOS)
* Setup (Windows - PowerShell)
* Database options (dev vs production)
* Running migrations & creating a superuser
* Running the dev server
* API docs & importing into Postman
* Static & media files (development)
* Useful management commands
* Troubleshooting & tips

---

## Project overview

* Multiple Django apps: `accounts`, `appointments`, `billing`, `medical`, `operations`, `payroll`, `pharmacy`.
* API base: `http://localhost:8000/api/` with interactive docs at `/api/docs/` and `/api/redoc/`.

---

## Prerequisites

* Python 3.10+ (or the interpreter used by the project)
* git
* pip
* For production or MySQL setup: MySQL/MariaDB server and `mysqlclient` installed (or use `psycopg2` for Postgres if preferred)

---

## Setup (Linux / macOS)

Open a terminal in the project root (where `manage.py` is):

```bash
# create & activate venv
python3 -m venv venv
source venv/bin/activate

# upgrade pip and install requirements
python -m pip install --upgrade pip
pip install -r requirements.txt

# set environment variables (example)
export DJANGO_SETTINGS_MODULE=core.settings
export SECRET_KEY='your-secret-key'
export DEBUG=True  # set False in production

# if using MySQL, configure DATABASES in settings and export DB credentials
```

Then run migrations and create a user:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput  # optional (for static files)
```

Start the dev server:

```bash
python manage.py runserver 0.0.0.0:8000
```

---

## Setup (Windows - PowerShell)

Open **PowerShell** in the project root:

```powershell
# create & activate venv
py -3 -m venv venv
venv\Scripts\Activate.ps1

# upgrade pip and install
python -m pip install --upgrade pip
pip install -r requirements.txt

# set env vars (temporary for current PS session)
$env:DJANGO_SETTINGS_MODULE = 'core.settings'
$env:SECRET_KEY = 'your-secret-key'
$env:DEBUG = 'True'  # 'False' in production

# then migrate and create superuser
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput

# run dev server
python manage.py runserver 0.0.0.0:8000
```

> Note: In cmd.exe use `venv\\Scripts\\activate.bat`. In PowerShell you might need to adjust the execution policy to allow the activate script: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.

---

## Database: quick-dev (SQLite) vs production (MySQL/MariaDB)

* For quick local development the project can use the included `db.sqlite3` (no extra config).
* For production or multi-developer environments use MySQL/MariaDB or Postgres and update `DATABASES` in `settings.py`. Ensure `mysqlclient` (or other DB adapter) is installed and the DB server is reachable.

---

## JWT & Settings

* The project is configured to use `djangorestframework-simplejwt` for JWT authentication. Example settings are in the repo and configure token lifetimes, algorithms, and auth classes.

---

## API documentation & Postman

* Open the interactive Swagger UI: `http://localhost:8000/api/docs/`.
* Schema (OpenAPI JSON): `http://localhost:8000/api/schema/`.

You can import the schema into Postman to auto-generate a collection:

1. In Postman click **Import** → **Link** and paste `http://localhost:8000/api/schema/` (or upload the downloaded `openapi.json`).
2. Postman creates a Collection with requests based on the OpenAPI spec.

---

## Useful management commands

* `python manage.py migrate` — Apply migrations
* `python manage.py createsuperuser` — Create admin user
* `python manage.py runserver` — Run dev server
* `python manage.py collectstatic` — Collect static files
* `python manage.py loaddata <fixture>` — Load fixtures

---

## Troubleshooting

* If `pip install -r requirements.txt` fails for `mysqlclient`, install system-level dependencies first (e.g., `sudo apt install default-libmysqlclient-dev` on Debian/Ubuntu). On Windows use prebuilt wheels or use MariaDB C connector.
* If static files 404 in production: ensure `collectstatic` ran and nginx/your server serves the `STATIC_ROOT` path.
* If media uploads fail: check `MEDIA_ROOT` and file permissions.

---

## Where to look in the code

* Root `manage.py` and `core/urls.py` contain the main routing and documentation routes (`/api/docs/`, `/api/schema/`, `/api/redoc/`).
* Apps live under the project root (`accounts/`, `appointments/`, `billing/`, ...).

---

## License & Contact

* Add license information here if needed.
* For questions: contact the maintainer.

---

Thanks for using this project — edit this README to add project-specific deploy notes.
