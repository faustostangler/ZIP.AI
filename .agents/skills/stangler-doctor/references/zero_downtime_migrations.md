# Zero-Downtime Database Migrations — Unifying Schema Evolution with the ADR Lifecycle

This document defines the technical protocols and patterns for evolving the database schema of the Stangler ecosystem without system downtime. It unifies the database migration lifecycle with the ADR lifecycle, ensuring that all state changes are planned, isolated, and backwards-compatible.

---

## 1. The Core Philosophy: The Expand-Contract (Parallel Run) Pattern

Schema evolution must NEVER break active application nodes running the previous version of the code. This requires separating database changes into multiple, backward-compatible steps, executing a **Parallel Run** phase where both the old and new schema shapes are concurrently supported by the application.

```
┌────────────────────────────────────────────────────────┐
│ Phase 1: Expand                                        │
│ Add new columns, tables, or indexes. Old code remains  │
│ fully functional, unaware of new fields.               │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ Phase 2: Migrate (Parallel Writing & Backfill)         │
│ Deploy new code that writes to both old and new        │
│ structures. Run asynchronous background backfill jobs. │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ Phase 3: Contract                                      │
│ Deploy new code using ONLY the new structures. Drop    │
│ old columns, tables, or obsolete constraints.         │
└────────────────────────────────────────────────────────┘
```

---

## 2. ADR Lifecycle Integration for Database Schema Changes

Every database migration that alters existing state or schemas must be documented in a corresponding ADR. The ADR acts as the architectural contract for the state transition.

### Required ADR Sections for Migrations

1. **Schema Migration Plan**: Detail the specific SQL changes for Expand and Contract phases.
2. **Data Backfill Strategy**: If migrating existing data (e.g., column split, type change), define the batch size, throttling mechanism, and SRE monitoring signals.
3. **Rollback Protocol**: Define the rollback procedure for each phase. Note that once a "Contract" phase is run, rollback is extremely difficult, so the "Migrate" phase must be fully validated.
4. **Consistency Verification**: How the application proves that the parallel run phase is not losing or corrupting data.

---

## 3. Zero-Downtime Migration Patterns

Below are the safe recipes for common schema operations under PostgreSQL.

### Pattern A: Adding a Non-Nullable Column

#### ✗ The Dangerous Way (Single Step)
Adding a `NOT NULL` column with a default value blocks the table while PostgreSQL rewrites all rows (on older versions) or acquires an exclusive lock that blocks incoming transactions.

```sql
-- DANGER: Blocks table writes during execution and breaks running old code
ALTER TABLE users ADD COLUMN billing_address VARCHAR(255) NOT NULL DEFAULT 'Pending';
```

#### ✓ The Safe Way (Multi-Phase)

1. **Step 1 (ADR approved, Phase 1 - Expand)**:
   Add the column as nullable without a default value.
   ```sql
   ALTER TABLE users ADD COLUMN billing_address VARCHAR(255);
   ```

2. **Step 2 (Phase 2 - Migrate)**:
   Deploy code that writes to both the old fields (if any) and sets the new column values on new writes. Run a background backfill script to update existing rows in batches with throttled queries:
   ```python
   # Example backfill loop with batching to avoid locking tables
   limit = 1000
   offset = 0
   while True:
       result = db.execute(
           "UPDATE users SET billing_address = 'Pending' "
           "WHERE id IN (SELECT id FROM users WHERE billing_address IS NULL LIMIT :limit)",
           {"limit": limit}
       )
       if result.rowcount == 0:
           break
       time.sleep(0.1) # Throttle to allow replication lag to recover
   ```

3. **Step 3 (Phase 3 - Contract preparation)**:
   Add the `NOT NULL` constraint dynamically as `NOT VALID` (PostgreSQL specific), then validate it. This avoids locking the table for reads/writes during constraint checking.
   ```sql
   ALTER TABLE users ADD CONSTRAINT users_billing_address_not_null 
     CHECK (billing_address IS NOT NULL) NOT VALID;
   
   -- Validates existing rows asynchronously without blocking DML
   ALTER TABLE users VALIDATE CONSTRAINT users_billing_address_not_null;
   ```

4. **Step 4 (Phase 3 - Contract)**:
   Convert the check constraint to a standard `NOT NULL` column constraint if desired, and remove obsolete structures.

---

### Pattern B: Renaming a Column

#### ✗ The Dangerous Way
Renaming a column directly breaks running instances of the application that expect the old column name.

```sql
-- DANGER: Instantly breaks running production nodes
ALTER TABLE users RENAME COLUMN phone TO mobile_phone;
```

#### ✓ The Safe Way (Parallel Run)

1. **Step 1 (Expand)**:
   Add the new column `mobile_phone` as nullable.
   ```sql
   ALTER TABLE users ADD COLUMN mobile_phone VARCHAR(50);
   ```

2. **Step 2 (Migrate)**:
   Deploy application code that reads from `phone` but writes to BOTH `phone` and `mobile_phone`.
   Run a background worker to copy values from `phone` to `mobile_phone` for all historical rows.

3. **Step 3 (Transition)**:
   Deploy application code that reads from `mobile_phone` and writes to both.

4. **Step 4 (Contract)**:
   Drop the old `phone` column.
   ```sql
   ALTER TABLE users DROP COLUMN phone;
   ```

---

### Pattern C: Safe Index Creation

#### ✗ The Dangerous Way
Creating an index locks the table against writes by default.

```sql
-- DANGER: Blocks all inserts, updates, and deletes on users
CREATE INDEX idx_users_email ON users(email);
```

#### ✓ The Safe Way
Use `CONCURRENTLY` to build the index without blocking writes.

```sql
-- SAFE: Creates index in the background
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
```
*(Note: Concurrent index creation cannot run inside a transaction block. Alembic migrations must set `schema_editor.execute` outside transactional steps or use `with_op` settings appropriately).*

---

## 4. Database Verification and Safety Checklist

Before committing any migration file to the repository, the following checklist must be satisfied:

1. **No Table Locks**: Verify that no migration command acquires an `ACCESS EXCLUSIVE` lock on a high-throughput table.
2. **Lock Timeout**: Set a short lock timeout on all migration transactions to prevent queueing up blocked queries in production.
   ```sql
   SET lock_timeout = '2s';
   ```
3. **Idempotence**: All migrations must be idempotent or safely re-runnable in case of partial deployment failures.
4. **Anti-Corruption Integration**: Any structural change affecting bounded context boundaries must pass through the Anti-Corruption Layer (ACL) defined in [Legacy Strangling Patterns](file:///mnt/gamer_d/Fausto%20Stangler/Documentos/Python/ISB/.agents/skills/stangler-doctor/references/legacy_strangling_patterns.md).
