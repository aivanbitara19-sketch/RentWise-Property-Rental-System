# RentWise — Property Rental and Property Management System

A runnable Flask + SQLite web application created to match the uploaded project brief. It includes a responsive dashboard, role-aware navigation and server-side authorization, property/unit/tenant/lease/payment/maintenance/utility/notice records, reports, an API, audit logging, and backup/restore scripts.

## 1. Requirements
- Python 3.10 or newer
- pip
- A modern browser
- SQLite (included with standard Python)

## 2. Run locally

**Windows** (PowerShell):
```powershell
cd property_rental_system
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

**macOS/Linux:**
```bash
cd property_rental_system
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pip install -r requirements.txt
python app.py
```
Open `http://127.0.0.1:5000`.

The database is created on first launch and sample records are seeded. It is stored in `property_rental.db`. Set a persistent secret key before deployment with environment variable `SECRET_KEY`; set `PROPERTY_DB` to choose a database path. The built-in server is for local demonstrations only. Use a production WSGI server behind HTTPS for deployment.

## 3. Demo accounts

| Role | Username | Password |
|---|---|---|
| Administrator | `admin` | `AdminDemo!2026` |
| Property Owner | `owner` | `OwnerDemo!2026` |
| Property Manager | `manager` | `ManagerDemo!2026` |
| Accountant | `accountant` | `AccountDemo!2026` |
| Leasing Officer | `leasing` | `LeasingDemo!2026` |
| Maintenance Staff | `maintenance` | `MaintDemo!2026` |
| Tenant | `tenant` | `TenantDemo!2026` |

These are classroom demo credentials only. Replace them before any real deployment. Passwords are stored as Werkzeug password hashes, not plaintext.

## 4. Implemented modules
- Dashboard counts: property/unit counts, vacancies, occupancy, overdue payments, open maintenance and leases expiring within 30 days.
- Properties and units.
- Tenant records.
- Lease records and status changes.
- Payment and utility-bill records, with restricted payment access.
- Maintenance requests and status workflow.
- Notices.
- Reports and administrator audit log.
- JSON API: `GET /api/summary` and `GET /api/units` (requires login).

Forms insert records and status actions update records. Some advanced workflows in the brief—document upload/e-signature, full contract generation, inspections/complaints, email/SMS alerts, payment-gateway integration, password-reset workflow, and complete user administration UI—are documented as future enhancements and are not claimed as implemented.

## 5. Backup and restore
Create a consistent backup and verify database integrity:
```bash
python scripts/backup.py
```
Stop the app before restore, then run:
```bash
python scripts/restore.py backups/your_backup_filename.db
```
The restore script checks integrity and saves a pre-restore copy if the current database exists. Demonstrate the required backup → simulated failure/test copy → restore → verify workflow on a separate test database, never by deleting live data.

## 6. Project documentation
See `docs/PROJECT_DOCUMENTATION.md`, `docs/INFORMATION_SECURITY_PLAN.md`, `docs/SYSTEM_ADMINISTRATION_PLAN.md`, and `docs/TEST_PLAN.md`. The `schema.sql` file contains the relational schema for database review.
