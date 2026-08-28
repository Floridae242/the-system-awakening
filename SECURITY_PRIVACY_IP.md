# Annex — Security, Privacy & IP Baseline

## Data Categories
Account, profile, quest/activity, raw evidence, derived facts, AI request/response, audit, analytics, art provenance.

For each category define: purpose, access roles, retention, deletion, export, AI use, logging policy.

## Evidence Upload Baseline
- authenticated uploader only
- extension allowlist
- validate actual file type
- server-generated storage names
- size limit
- private object storage
- no public-by-default evidence URLs
- consider malware/sandbox checks for production beta

## Privacy
- collect minimum necessary data
- user can delete account/activity
- avoid retaining raw evidence indefinitely when derived facts suffice
- redact sensitive content from logs

## IP / Art Provenance
Every production asset should record asset_id, creator/tool, creation date, prompt/version, references used, source/licence, review status and similarity/IP review status.
References inform abstract mood/grammar only; do not reproduce recognisable characters, logos, costumes, UI or franchise assets.
