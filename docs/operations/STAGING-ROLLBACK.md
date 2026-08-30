# Staging backup and rollback

Secrets are injected through the environment; never commit them to this runbook.

## Backup

```bash
docker compose -f docker-compose.prod.yaml exec -T postgres \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > awakening-$(date +%Y%m%d-%H%M%S).dump
```

Keep dumps in encrypted, access-controlled storage and record the migration/image
revision beside each dump.

## Rollback

1. Stop writes or place the deployment in maintenance mode.
2. Restore the last known-good image tag in `docker-compose.prod.yaml`.
3. Restore a compatible database dump only when the migration is not backward
   compatible: `pg_restore --clean --if-exists -U "$POSTGRES_USER" -d "$POSTGRES_DB" backup.dump`.
4. Run `alembic upgrade head`, then `docker compose ... up -d --wait`.
5. Verify health, auth, core loop, idempotency, and E2E before reopening traffic.

## Incident evidence

Record the commit SHA, image digest, migration revision, UTC timestamps, failed
checks, and operator. Preserve logs before teardown.
