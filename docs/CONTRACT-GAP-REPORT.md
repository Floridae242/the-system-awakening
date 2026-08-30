# AttlifeFUnz → Awakening contract review

Reviewed 30 Aug 2026 against `AttlifeFUnz/the-system-build-ready/`.

## Findings

| Area | Finding | Resolution |
| --- | --- | --- |
| Core contracts | PRD, MVP scope, game rules, design system, content seed, deployment and risk register are identical to the reference copies. | No change required. |
| Verification vocabulary | The reference snapshot uses the older `REJECT`/`NEEDS_BETTER_EVIDENCE` vocabulary, while the current user-flow/API/AI contracts use `FAIL`/`NEED_MORE_EVIDENCE` and `REVIEW`. | Kept the newer, internally consistent vocabulary and recorded the intentional contract evolution. |
| API document | Awakening adds first-party demo/BFF and internal-worker paths not present in the original API snapshot. | These are implementation boundaries; production verification remains worker-only. |
| Auditability | The reference ERD requires `audit_events` and mutation audit records; Awakening had the table absent and no domain-event writes. | Added `AuditEvent`, migration `f6a7b8c9d012`, indexes, and transactional records for quest acceptance, submission, verification, reward grant and chest opening. |
| Raw evidence | The reference requires private storage and configurable retention. | Existing validated private upload path remains; retention/object-store provider is a deployment hardening item, not silently changed in this review. |

## Verification

- API suite: 33 passed, 3 skipped.
- Added regression test proving the five core mutation events are persisted.
- Migration is append-only and follows the existing Alembic chain.
- No reference documents were modified.
