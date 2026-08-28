# 12 Risk Register

| ID | Risk | Probability | Impact | Trigger | Mitigation | Contingency | Owner | Status |
|---|---|---|---|---|---|---|---|---|
| R-01 | Scope creep | High | Critical | New core features added after Day 10 | MUST/SHOULD/WON'T freeze | Drop optional features | Product | Open |
| R-02 | AI provider outage/latency | Medium | High | Timeout/error spike | bounded retry, feature flag | DEMO_MODE fixture | AI/Backend | Open |
| R-03 | Invalid AI output | Medium | High | schema validation fails | strict JSON schema | fallback/no mutation | AI | Open |
| R-04 | Duplicate rewards | Medium | Critical | retries/network failures | unique DB constraints + transaction | audit/fix ledger | Backend | Open |
| R-05 | Chest reroll exploit | Medium | Critical | repeated open requests | persisted open result + idempotency | disable chest opening temporarily | Backend | Open |
| R-06 | Broken object authorization | Medium | Critical | cross-user access | ownership middleware/tests | feature shutdown + incident response | Backend/Security | Open |
| R-07 | Unsafe/untrusted uploads | Medium | High | malformed/oversized files | allowlist, size/type checks, private storage | disable upload, manual evidence | Backend | Open |
| R-08 | Art/IP similarity | Medium | High | review flags recognisable copied design | original art bible + provenance review | replace asset | Art/Product | Open |
| R-09 | DB migration failure | Low-Med | High | deployment migration error | migration tests/backup | rollback app/restore or forward fix | Backend | Open |
| R-10 | AI cost spike | Medium | Medium | calls/user rise unexpectedly | model routing, limits, cache | disable noncritical AI | AI/Platform | Open |
| R-11 | Performance issues from animation/art | Medium | Medium | mobile jank/slow load | compressed assets, lazy load, reduced motion | disable heavy FX | Frontend | Open |
| R-12 | Core E2E not stable by Day 12 | Medium | Critical | repeated test failures | prioritize only core loop | cut achievements/boss/polish | Tech Lead | Open |
| R-13 | Evidence privacy issue | Low-Med | Critical | public URL/log leak | private storage, log redaction | delete/rotate URLs, incident response | Security | Open |
| R-14 | Demo internet failure | Medium | High | venue connectivity issue | cached/static shell + demo fixture | local/demo fallback if prepared | Team | Open |

## Review Cadence
- Daily during 18-day build.
- Any Critical risk changing to High probability must be discussed before new feature work.
