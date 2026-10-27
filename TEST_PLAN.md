# Test Plan and Acceptance Checklist

## Functional tests
| ID | Test | Expected result |
|---|---|---|
| F01 | Login with valid demo credentials | Dashboard loads; session created |
| F02 | Login with incorrect password | Generic error; failed login audit entry |
| F03 | Open module allowed to current role | Module loads |
| F04 | Open payment module as maintenance staff or tenant | HTTP 403 |
| F05 | Add property/unit/tenant/lease/payment/maintenance/utility record with valid data | Record saved and listed |
| F06 | Submit negative rent or payment | Database constraint rejects invalid value; user sees safe error |
| F07 | Add duplicate unit number under same property | Unique constraint prevents duplicate |
| F08 | Mark payment Paid | Status updates and paid date is set |
| F09 | Search a module | Matching rows shown |
| F10 | Call `/api/summary` while logged in | JSON aggregate returned |
| F11 | Call `/api/units` while logged in | JSON unit list returned |
| F12 | Open audit logs as non-admin | HTTP 403 |
| F13 | Maintenance staff views maintenance list | Only assigned requests are shown |
| F14 | Dashboard with overdue payment / expiring lease sample | Relevant counts shown |
| F15 | Logout | Session cleared and login page shown |

## Security tests before production
- Verify all state-changing requests require CSRF tokens and reject missing/invalid tokens.
- Attempt direct URL access to every restricted module and record; expect server-side denial.
- Test tenant A cannot access tenant B records, including IDs guessed manually.
- Test maintenance staff cannot view unassigned requests or change unauthorized assignments.
- Confirm payment reports are limited to approved accounting/oversight roles.
- Verify output escaping with HTML/script payloads; ensure they render as text.
- Test SQL-injection strings in all search and form fields.
- Test session cookie flags, session expiry/rotation, HTTPS, rate limiting, and account lockout.
- Test upload restrictions if document upload is later added.
- Verify audit log events for authentication and record changes.

## Backup/recovery test
- Create verified backup, simulate failure on a test copy, restore, run integrity check, compare record counts, and test core workflows.
- Capture evidence: screenshots, commands, timestamp, operator, result, and remediation notes.

## Known limitations
The current classroom prototype is not yet complete for every advanced requirement. It needs a full CRUD edit/delete interface with safe delete rules, stronger CSRF implementation on all actions, account administration and password reset, tenant object-level isolation for all data types, assignment UI for maintenance, automatic daily status jobs, contract/inspection/complaint workflows, and production HTTPS/secure-cookie configuration. Do not deploy with real tenant data until these gaps are resolved and independently tested.
