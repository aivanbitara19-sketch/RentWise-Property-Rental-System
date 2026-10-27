# Information Security Plan

## 1. Scope and objectives
Protect tenant personally identifiable information, lease records, payment/utility data, user credentials, audit logs, and application/database availability. Use least privilege, accountability, backup/recovery, and documented incident response.

## 2. Asset inventory
| Asset | Classification | Owner/custodian | Security objective |
|---|---|---|---|
| Tenant/contact records | Confidential | Property Manager | Prevent unauthorized disclosure and alteration |
| Lease/contract records | Confidential / legally important | Leasing Officer + Owner | Integrity, controlled approvals, retention |
| Payment and utility records | Restricted financial | Accountant | Confidentiality, accuracy, traceability |
| User accounts/password hashes | Restricted | Administrator | Prevent account compromise |
| Web application/source | Internal | Administrator/developer | Integrity, patching, availability |
| SQLite database | Confidential | System administrator | Access restriction, integrity, recovery |
| Server/host and network | Internal | System administrator | Availability and secure configuration |
| Audit logs | Restricted | Administrator | Accountability and tamper resistance |
| Backup files | Confidential | System administrator | Recovery and confidentiality |
| Browser sessions/secrets | Restricted | Application administrator | Prevent session theft and forgery |

## 3. Risk register
Likelihood/impact are qualitative initial estimates and should be reviewed each term and after incidents.
| Threat | Vulnerability / cause | Likelihood | Impact | Risk | Treatment |
|---|---|---:|---:|---|---|
| Unauthorized account access | Weak/reused credentials | Medium | High | High | Mitigate: 12+ character passphrases, password hashing, failed-login monitoring/lockout in production, MFA for privileged accounts |
| Tenant data exposure | Incorrect role checks or broad query | Medium | High | High | Mitigate: deny-by-default RBAC, tenant ownership checks, authorization tests, minimal reports |
| SQL injection | Unsafe query construction | Low in current parameterized value queries | High | Medium | Mitigate: parameterized queries, allow-listed table/column names, input validation, code review |
| XSS | Unsafe rendering of user content | Medium | High | Medium/High | Mitigate: template autoescaping, avoid `safe`, validate input, deploy Content-Security-Policy |
| CSRF | Forged cross-site form submission | Medium | High | High | Mitigate: CSRF tokens on state-changing forms; production should use established CSRF middleware and origin checks |
| Session theft | Insecure transport or cookie configuration | Medium | High | High | Mitigate: HTTPS, Secure/HttpOnly/SameSite cookies, session rotation, timeout, revoke on password change |
| Data loss | Disk failure, accidental deletion, ransomware | Medium | High | High | Mitigate: daily incremental + weekly full backups, encrypted off-host copies, restore drills |
| Fraudulent payment entry | Unverified manual payment evidence | Medium | High | High | Mitigate: accounting review, reference reconciliation, dual approval for corrections, audit trail |
| Unauthorized lease alteration | Broad write access | Medium | High | High | Mitigate: restricted role, approval workflow, immutable audit, versioned backups |
| Server compromise | Unpatched dependencies or exposed debug service | Medium | High | High | Mitigate: patch schedule, no debug mode in production, firewall, least privilege, TLS |
| Insider misuse | Excessive privileges / no review | Medium | High | High | Mitigate: quarterly access review, separation of duties, log review, immediate deactivation on departure |
| Backup theft | Plaintext backups or public storage | Low/Medium | High | High | Mitigate: encryption, restricted access, off-site storage, retention/deletion schedule |

### Risk treatment choices
- **Mitigate:** default approach for credential, privacy, data loss, and server risks using the controls above.
- **Avoid:** do not store card numbers or unnecessary sensitive documents; do not expose debug mode publicly.
- **Transfer:** consider a reputable managed hosting provider/contractual service for infrastructure incidents; this does not remove the organization's accountability.
- **Accept:** only low residual risks documented by the owner, with rationale and review date.

## 4. Role-based access control matrix
Legend: Full = permitted; Own/Assigned = only own or assigned records; Limited = limited operational view; — = denied.
| Function | Admin | Owner | Manager | Tenant | Maintenance | Leasing | Accountant |
|---|---|---|---|---|---|---|---|
| Manage user accounts | Full | — | — | — | — | — | — |
| View/edit properties | Full | Full | Full | — | — | Limited | — |
| Manage units | Full | Full | Full | Own status only (future) | Limited | Full | — |
| View tenant details | Full | Full | Full | Own only | Minimum needed | Full | Billing identity only |
| Create/review leases | Full | Full | Full | Own only | — | Full | Read billing fields only |
| View payment reports | Restricted admin | Limited/owner oversight | — | Own only (future) | — | — | Full |
| Record payment | Full | Authorized | — | — | — | — | Full |
| Create maintenance request | Full | Full | Full | Own unit only | — | — | — |
| View/assign maintenance | Full | Full | Full | Own request | Assigned only | — | — |
| Audit logs | Full | — | — | — | — | — | — |
| Delete lease/payment records | Exceptional controlled admin with approval | Approval only | — | — | — | — | — |

The application currently implements role-aware module access and filters maintenance requests for maintenance staff and linked tenants. This matrix includes intended policy beyond the prototype; additional object-level tenant isolation and approval workflows must be completed before production.

## 5. Security policies
### Acceptable use
Use the system only for authorized rental-management tasks. Do not share accounts, scrape/export tenant data without approval, upload unlawful content, or bypass controls. Report suspected misuse immediately.

### Account management
Accounts require an approved request and unique named user. Administrator verifies role and business need. Deactivate accounts immediately when a worker leaves or role changes. Review privileged accounts quarterly. Never use shared administrator credentials.

### Password and authentication
Minimum 12 characters; prefer long unique passphrases; block common/compromised passwords; rate-limit failed logins and lock or challenge repeated failures; store only salted adaptive hashes; never send passwords in email or log them. Implement secure reset using time-limited single-use tokens and verified identity. Production privileged accounts should use MFA. Demo passwords must be changed.

### Access control and privacy
Default deny. Grant least privilege and separate accounting, leasing, maintenance, and administration duties. Tenants must not view other tenants' records. Maintenance personnel may see only assigned requests and minimum unit details. Payment reports are limited to accounting and explicitly authorized oversight roles. Review access quarterly.

### Data retention
Retain leases, accounting and tax records for the period required by applicable Philippine law and organizational policy; confirm exact periods with legal/accounting advisers. Retain tenant records only while needed for contract, operational, and legal purposes. Securely delete expired records after legal hold and approval checks. Keep audit logs according to a documented retention schedule.

### Audit logging
Record successful/failed login, logout, password changes/reset, account creation/deactivation, permission changes, record creation/modification, payment status changes, lease approval, export, backup/restore, and administrative actions. Do not log passwords, session tokens, or unnecessary personal data. Restrict log access and review alerts weekly.

### Change management
Every production change requires a ticket, impact/security review, approval by an authorized owner, testing in a non-production environment, a backup/rollback plan, controlled deployment, and updated documentation. Emergency changes must be retrospectively reviewed.

### Incident response
Follow **Detect → Report → Contain → Investigate → Recover → Document → Prevent recurrence**. Revoke compromised sessions/accounts; isolate affected host; preserve logs and forensic copies; notify the owner and appropriate stakeholders; assess legal notification duties; restore only from verified clean backups; document root cause and lessons learned.

### Backup and recovery
Daily incremental backup and weekly full backup; encrypt backups in transit and at rest; keep at least one access-restricted off-host copy; use a retention schedule approved by management; log backup outcomes; test restoration monthly and after major changes. Never rely on an untested backup.

### Disaster recovery
Prioritize database and authentication service, then web application and document storage. Proposed targets for a classroom prototype: **RTO 8 hours** (target time to restore service) and **RPO 24 hours** (maximum target data-loss window); management must approve targets based on business needs. Restore a verified backup to a clean environment, check record counts/integrity, test login/roles/core workflows, and record sign-off.
