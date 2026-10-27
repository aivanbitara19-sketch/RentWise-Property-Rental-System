# System Administration and Maintenance Plan

## 1. Proposed deployment specifications
These are planning recommendations, not measurements of a deployed server.

| Component | Classroom/demo | Production recommendation |
|---|---|---|
| OS | Windows 10/11, Ubuntu 22.04+ or equivalent | Supported Ubuntu Server LTS or managed Linux hosting |
| CPU | 2 cores | 2–4 vCPU to start, scale based on monitoring |
| RAM | 4 GB | 4–8 GB for app; database sized to usage |
| Storage | 5 GB free for code, database, logs | SSD sized for database, documents, logs and backups; keep backup separate |
| Web/app server | Flask development server on localhost only | Gunicorn/uWSGI behind Nginx or managed WSGI platform |
| Database | SQLite for one-host demonstration | Managed PostgreSQL/MySQL for concurrent multi-user production |
| Network | Local loopback for demo | HTTPS/TLS, firewall, restricted admin access, private database network |
| Backup | Local backup folder for lab | Encrypted off-host/object storage with restricted credentials |

## 2. Installation and deployment
1. Provision a supported OS and create a dedicated non-root service account.
2. Install supported Python and dependencies from `requirements.txt` in a virtual environment.
3. Configure a persistent random `SECRET_KEY` and database path using environment variables or a secret manager; do not commit secrets.
4. Initialize the database and validate sample data only in development. Remove sample accounts/data before production.
5. Run behind HTTPS reverse proxy and a production WSGI server; disable debug mode; set secure cookies; restrict inbound ports.
6. Apply least-privilege file permissions to application, database, logs, and backup locations.
7. Configure health checks, disk-space monitoring, dependency updates, and centralized error/security logs.
8. Test roles, core workflows, backup and restore before release.

## 3. User and permission management
- Only administrator may provision/deactivate accounts and change roles.
- Each user receives a unique account and the minimum permissions required.
- Review accounts and permissions quarterly and after transfers/termination.
- Remove access immediately on termination; revoke active sessions and rotate shared secrets if exposed.
- Database file and backup access is limited to the service account and authorized administrators. Production database accounts should have separate least-privilege credentials for application access and maintenance.

## 4. Service and maintenance schedule
| Frequency | Task | Responsible role |
|---|---|---|
| Daily | Check service health, errors, disk capacity, backup result and failed logins | System administrator |
| Daily | Incremental backup | System administrator / scheduled job |
| Weekly | Full backup; review overdue operational alerts and audit anomalies | System administrator + owner |
| Monthly | Restore test to isolated environment; apply tested security updates | System administrator |
| Quarterly | Access review, dependency review, disaster-recovery exercise | Administrator + owner |
| On change | Backup, test, approve, deploy, verify, document/rollback if needed | Change owner + administrator |
| On incident | Preserve evidence, contain, recover, record lessons learned | Incident lead |

## 5. Backup and restore demonstration
1. Use a test database or a copy of the classroom database.
2. Run `python scripts/backup.py` and record the backup file and integrity result.
3. Copy the database to a temporary test directory and simulate failure by renaming/deleting only the test copy.
4. Stop the application and run `python scripts/restore.py backups/<verified-file>.db` against the test path (set `PROPERTY_DB` to the test target).
5. Verify `PRAGMA integrity_check`, record counts, and login/dashboard/module functionality.
6. Document timestamp, operator, source backup, results, and any recovery issues.

## 6. Monitoring and updates
Monitor availability, response time, CPU/RAM, disk, database size, backup age, HTTP errors, repeated failed login attempts, and unexpected permission/data changes. Patch OS and Python dependencies on a regular schedule after staging tests. Keep an inventory of software versions and document rollback steps.
