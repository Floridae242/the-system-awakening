# 05 Database ERD & Persistence Contract

## 1. Database
PostgreSQL is authoritative for durable player/game state.

## 2. Core Tables
### users
- id uuid PK
- auth_provider_id text UNIQUE NOT NULL
- email text NULL
- created_at timestamptz NOT NULL
- updated_at timestamptz NOT NULL

### player_profiles
- id uuid PK
- user_id uuid UNIQUE FK users(id)
- display_name text NOT NULL
- level int NOT NULL DEFAULT 1 CHECK level >= 1
- current_xp bigint NOT NULL DEFAULT 0 CHECK current_xp >= 0
- str int NOT NULL DEFAULT 10
- agi int NOT NULL DEFAULT 10
- vit int NOT NULL DEFAULT 10
- int_stat int NOT NULL DEFAULT 10
- wil int NOT NULL DEFAULT 10
- streak_days int NOT NULL DEFAULT 0
- timezone text NOT NULL DEFAULT 'Asia/Bangkok'
- created_at, updated_at

### quest_definitions
- id text PK
- version int NOT NULL
- title text NOT NULL
- category text NOT NULL
- difficulty text NOT NULL
- objective jsonb NOT NULL
- verification_policy jsonb NOT NULL
- reward_profile text NOT NULL
- status text NOT NULL
- created_at, updated_at

### player_quests
- id uuid PK
- player_id uuid FK player_profiles(id)
- quest_definition_id text FK quest_definitions(id)
- quest_definition_version int NOT NULL
- status text NOT NULL
- accepted_at timestamptz NULL
- completed_at timestamptz NULL
- created_at, updated_at
- UNIQUE(player_id, quest_definition_id, created_at::date) implemented via appropriate generated key/logic if daily uniqueness is required

### quest_submissions
- id uuid PK
- player_quest_id uuid FK player_quests(id)
- player_id uuid FK player_profiles(id)
- idempotency_key text NOT NULL
- evidence_type text NOT NULL
- evidence_object_key text NULL
- manual_evidence jsonb NULL
- status text NOT NULL
- created_at, updated_at
- UNIQUE(player_id, idempotency_key)

### verification_results
- id uuid PK
- submission_id uuid UNIQUE FK quest_submissions(id)
- schema_version text NOT NULL
- provider text NOT NULL
- model text NULL
- prompt_version text NOT NULL
- recommended_disposition text NOT NULL
- confidence numeric NULL
- evidence_quality text NOT NULL
- extracted_facts jsonb NOT NULL
- condition_results jsonb NOT NULL
- risk_flags jsonb NOT NULL DEFAULT '[]'
- fallback_used boolean NOT NULL DEFAULT false
- latency_ms int NULL
- raw_response_redacted jsonb NULL
- created_at

### reward_grants
- id uuid PK
- player_id uuid FK player_profiles(id)
- submission_id uuid UNIQUE FK quest_submissions(id)
- rules_version text NOT NULL
- status text NOT NULL
- exp_granted int NOT NULL
- stat_changes jsonb NOT NULL
- created_at

### progression_ledger
- id uuid PK
- player_id uuid FK player_profiles(id)
- reward_grant_id uuid FK reward_grants(id)
- entry_type text NOT NULL
- stat_name text NULL
- amount int NOT NULL
- source_type text NOT NULL
- source_id uuid NOT NULL
- created_at
- UNIQUE(reward_grant_id, entry_type, stat_name)

### chests
- id uuid PK
- player_id uuid FK player_profiles(id)
- reward_grant_id uuid UNIQUE FK reward_grants(id)
- rarity text NOT NULL
- status text NOT NULL DEFAULT 'UNOPENED'
- rng_version text NOT NULL
- created_at, opened_at

### item_definitions
- id text PK
- version int NOT NULL
- name text NOT NULL
- rarity text NOT NULL
- item_type text NOT NULL
- power int NOT NULL DEFAULT 0
- metadata jsonb NOT NULL
- status text NOT NULL

### inventory_items
- id uuid PK
- player_id uuid FK player_profiles(id)
- item_definition_id text FK item_definitions(id)
- item_definition_version int NOT NULL
- source_chest_id uuid FK chests(id)
- created_at

### chest_open_results
- id uuid PK
- chest_id uuid UNIQUE FK chests(id)
- item_instance_id uuid UNIQUE FK inventory_items(id)
- rng_metadata jsonb NULL
- created_at

### audit_events
- id uuid PK
- event_type text NOT NULL
- event_version int NOT NULL DEFAULT 1
- player_id uuid NULL
- correlation_id text NULL
- causation_id text NULL
- payload jsonb NOT NULL
- created_at

## 3. Critical Invariants
- One verification result per submission.
- One reward grant per submission.
- One chest per reward grant.
- One chest open result per chest.
- One item instance per chest open result.
- Reward/chest state changes occur in a DB transaction.

## 4. Required Indexes
- player_quests(player_id, status)
- quest_submissions(player_id, created_at desc)
- audit_events(player_id, created_at desc)
- inventory_items(player_id, created_at desc)
- chests(player_id, status)

## 5. Retention / Privacy Baseline
- Raw evidence stored in private object storage, never public URLs.
- Evidence retention policy must be configurable; MVP default recommendation: short-lived where feasible.
- Logs must not contain raw secrets or unrestricted evidence contents.

## 6. Migration Policy
- All changes via migration files.
- No manual production schema edits.
- Migrations tested from empty database and from previous release snapshot.

## 7. Domain Events
quest.accepted
submission.created
verification.requested
verification.completed
reward.granted
player.level_up
chest.opened
item.granted
