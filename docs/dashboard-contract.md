# Company dashboard contract

`GET /api/v1/dashboard` requires a Bearer token and the `empresa` role (or admin).
The owner is always the token subject; callers cannot select another company.
Response: `{ "success": true, "data": { "issued": 0, "pending_delivery": 0,
"sent": 0, "participants": 0, "emissions": [], "recent_activities": [] } }`.

Counts cover certificates with `issuer_id` equal to the subject and a non-null
`issued_at`. Pending delivery means student email status pending, sending,
failed or deferred. Sent means SMTP accepted (`sent`), not confirmed delivery.
Participants counts distinct normalized non-empty participant email addresses.
Emissions contains six calendar months, including the current month, in UTC,
as `{month: "YYYY-MM", emissions: number}`, including zero months.
Recent activities are the five latest issued certificates, descending by issue
date then ID, as `{id, name, student, issued_at}`. No invented outage notices.
Drafts exist only in browser storage and are excluded from company statistics.
No records returns zero counts and an empty activity list. Authentication errors
use 401/403; service failures are errors, never successful zero snapshots.
