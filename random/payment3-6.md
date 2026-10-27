We continue to **L3 Section 7, Topic 6 — Zero-downtime schema & ledger migrations**. The prior topics kept the system _correct_, _observable_, _resilient_, and _verified_. This topic confronts a harder temporal challenge: **changing the data model of a live money system without downtime and without corrupting a single cent.** Software evolves — new fields, new tables, restructured ledgers — but a money system can't go down to migrate (payments must keep flowing) and _every row is money_ (a migration bug doesn't lose a log line, it loses or duplicates real value). Worse, the ledger is **append-only and immutable** (L2.1) — you _can't rewrite history_ — so migrating it requires techniques that preserve the immutable record while evolving the schema around it. This is the data-evolution counterpart to Section 2's provider migration (Topic 5), now applied to the most correctness-critical data there is. Definitive treatment, labeled parts, building on the immutable ledger (L2.1), reconciliation (L2-recon), zero-downtime provider migration (Section 2 Topic 5), and the correctness-first/testing/observability foundations.

---

# Part 1 — First principles: why migrating a money system's data is uniquely hard

## 1.1 The three compounding constraints

Migrating _any_ database schema without downtime is hard. Migrating a _money system's_ data compounds it with three constraints that make it uniquely dangerous:

```text
THE THREE COMPOUNDING CONSTRAINTS (why money-data migration is uniquely hard):
  1. ZERO DOWNTIME — payments must keep flowing DURING the migration → you CAN'T take the system down to
     migrate (a money system down = lost transactions, broken SLAs, lost trust) → the migration happens on a
     LIVE, actively-processing system → the data is CHANGING while you migrate it.
  2. EVERY ROW IS MONEY — a migration bug doesn't lose a LOG LINE, it loses or duplicates REAL VALUE → a
     dropped row = lost money; a duplicated row = created money; a mis-transformed value = wrong money → the
     near-zero correctness budget (Topic 1) applies to EVERY row → zero tolerance for data error.
  3. THE LEDGER IS IMMUTABLE / APPEND-ONLY (L2.1) — you CAN'T REWRITE HISTORY → the financial record is
     permanent (for correctness, audit, compliance) → so you can't just "ALTER the ledger table and transform
     the rows" (mutating immutable records) → migrating the ledger requires preserving the immutable past while
     evolving the future (Part 4) → a FUNDAMENTALLY different migration problem than a mutable table.
  → these COMPOUND: migrate a LIVE (1) system where EVERY ROW IS MONEY (2) and the core data is IMMUTABLE (3)
     → no downtime, no data error (zero budget), no rewriting history → the hardest migration in software.
  → the GOVERNING PRINCIPLE (Topic 1): CORRECTNESS FIRST → the migration must NEVER corrupt the money, even at
     the cost of taking LONGER / being more CONSERVATIVE → a correctness breach during migration is an incident
     → migrate SLOWLY and SAFELY rather than fast and risky.
```

**Migrating a money system's data is uniquely hard because of _three compounding constraints_: (1) _zero downtime_ — payments must keep flowing _during_ the migration (a money system down means lost transactions, broken SLAs, lost trust), so the migration happens on a _live, actively-processing_ system where _the data is changing while you migrate it_; (2) _every row is money_ — a migration bug doesn't lose a log line, it loses or duplicates _real value_ (a dropped row = lost money, a duplicated row = created money, a mis-transformed value = wrong money), so the near-zero correctness budget (Topic 1) applies to _every row_ with _zero tolerance for data error_; and (3) _the ledger is immutable/append-only_ (L2.1) — you _can't rewrite history_ (the financial record is permanent for correctness/audit/compliance), so you _can't_ just "ALTER the ledger table and transform the rows" (mutating immutable records) — migrating the ledger requires _preserving the immutable past while evolving the future_ (Part 4), a fundamentally different problem than a mutable table. These _compound_: migrate a _live_ system where _every row is money_ and the core data is _immutable_ — no downtime, no data error, no rewriting history — the hardest migration in software. The governing principle (Topic 1) is _correctness first_: the migration must _never_ corrupt the money, even at the cost of taking longer / being more conservative — a correctness breach during migration is an incident — so you _migrate slowly and safely rather than fast and risky_. This triple constraint (live + money + immutable) is what makes money-data migration the hardest data-evolution problem, and correctness-first dictates the conservative, verified approach the rest of the topic develops.**

## 1.2 Why you must migrate anyway (the tension)

- **Software and requirements evolve.** New features need new fields; growth needs restructuring (sharding, the scaled ledger — L3 Section 1); new currencies, new rails, new regulations require schema changes. **You _must_ evolve the data model (features, scale, new requirements) over the system's multi-year life — the ledger is forever, and forever requires change — so migration is unavoidable; the question is _how_ to do it safely.**
- **You can't rebuild from scratch.** A money system is too critical, too large, and too _irreplaceable_ (the ledger is the source of truth) to rewrite — you _evolve in place_. **A money system can't be rebuilt from scratch (it's the irreplaceable source of truth); it must be _evolved in place_, which means migrating live data — the challenge this topic addresses.**

**The through-line: migrating a money system's data is uniquely hard (compounding zero-downtime + every-row-is-money + immutable-ledger constraints, demanding correctness-first conservatism), yet unavoidable (the system evolves over years and can't be rebuilt), so you must migrate _live, money-holding, immutable_ data _safely_ — the data-evolution counterpart to Section 2's provider migration, applied to the most correctness-critical data there is.**

---

# Part 2 — The expand-contract (parallel-change) pattern: the foundation

The core technique for zero-downtime schema change: **expand-contract** (also called _parallel-change_) — never change-in-place (which requires downtime or risks breaking live traffic); instead, _add the new_ alongside the old, migrate gradually, then _remove the old_ — so the system is always in a working state.

## 2.1 The pattern

```text
EXPAND-CONTRACT / PARALLEL-CHANGE (the zero-downtime schema-change foundation):
  the PROBLEM with change-in-place: rename a column / change a type / restructure → the OLD code expects the
     OLD schema, the NEW code expects the NEW → during the change, SOMETHING is broken (old code + new schema,
     or vice versa) → requires downtime (stop, change, restart) → UNACCEPTABLE for a live money system.
  EXPAND-CONTRACT: evolve in THREE phases, always keeping the system WORKING:
     1. EXPAND — ADD the new schema element (new column/table) ALONGSIDE the old → both exist → the system still
        works with the old (nothing broken) → a purely additive, safe change.
     2. MIGRATE / TRANSITION — DUAL-WRITE (write to BOTH old and new) + BACKFILL (copy existing old data to new)
        + gradually SHIFT READS from old to new → the system transitions while BOTH work → verified at each step
        (Part 3).
     3. CONTRACT — once everything uses the NEW and the old is unused + verified → REMOVE the old schema element
        → the migration is complete → a purely subtractive, safe change.
  → at EVERY phase, the system is in a WORKING state (expand: old works; transition: both work; contract: new
     works) → NO moment where it's broken → ZERO DOWNTIME.
  → this is the SAME gradual, reversible, dual-running pattern as Section 2's PROVIDER MIGRATION (Topic 5):
     expand (both available) → gradually shift (dual-run) → contract (old removed) → the parallel-change
     discipline, now for the DATA MODEL instead of the provider.
  → REVERSIBILITY: at each phase you can ROLL BACK (the old still exists until contract) → if the new has a
     problem, revert to the old → safe, reversible migration (never a point of no return until verified).
```

**Expand-contract (parallel-change) is the zero-downtime schema-change foundation, solving the problem that _change-in-place_ breaks something during the change (old code + new schema, or vice versa — requiring downtime, unacceptable for a live money system). Instead, you evolve in _three phases, always keeping the system working_: (1) _expand_ — _add_ the new schema element (new column/table) _alongside_ the old (both exist; the system still works with the old — a purely additive, safe change), (2) _migrate/transition_ — _dual-write_ (write to _both_ old and new) + _backfill_ (copy existing old data to new) + gradually _shift reads_ from old to new (the system transitions while both work, verified at each step — Part 3), and (3) _contract_ — once everything uses the new and the old is unused + verified, _remove_ the old (a purely subtractive, safe change). At _every_ phase the system is in a _working state_ (expand: old works; transition: both work; contract: new works) — _no moment where it's broken_ — zero downtime. This is the _same gradual, reversible, dual-running pattern as Section 2's provider migration_ (Topic 5): expand (both available) → gradually shift (dual-run) → contract (old removed) — the parallel-change discipline, now for the _data model_ instead of the _provider_. And it's _reversible_: at each phase you can _roll back_ (the old still exists until contract) — if the new has a problem, revert to the old — a safe, reversible migration (never a point of no return until verified). Expand-contract is the universal zero-downtime migration pattern — add-new, dual-run-and-shift, remove-old — keeping the system always-working and always-reversible, mirroring the provider-migration discipline from Section 2 applied to the data model.**

## 2.2 Why reversibility and always-working matter for money

```text
WHY ALWAYS-WORKING + REVERSIBLE MATTER FOR MONEY (the correctness-first application):
  ALWAYS-WORKING (no broken moment) → ZERO DOWNTIME → payments keep flowing → the availability requirement met
     WITHOUT sacrificing it during migration.
  REVERSIBLE (roll back at each phase) → if a phase reveals a problem (a dual-write discrepancy, a backfill
     error), you can REVERT before committing → you NEVER reach a point where the money is corrupted and you
     can't go back → correctness-first (Topic 1): don't proceed past a phase until it's VERIFIED correct.
  GRADUAL (shift reads/traffic incrementally) → a problem shows up at LOW scale (a small % on the new path)
     before full commitment → catch it early, roll back cheaply → the gated-rollout discipline (Section 2/5).
  → so expand-contract gives money migration the THREE things it needs: no downtime (always-working), no
     corruption (reversible + verified per phase), and early problem detection (gradual) → the correctness-
     first, conservative migration the triple constraint (Part 1) demands.
```

**Always-working + reversible matter for money as the correctness-first application: _always-working_ (no broken moment) → _zero downtime_ → payments keep flowing (the availability requirement met _without_ sacrificing it during migration); _reversible_ (roll back at each phase) → if a phase reveals a problem (a dual-write discrepancy, a backfill error), you can _revert before committing_ → you _never_ reach a point where the money is corrupted and you can't go back (correctness-first, Topic 1: don't proceed past a phase until it's _verified correct_); _gradual_ (shift reads/traffic incrementally) → a problem shows up at _low scale_ (a small % on the new path) before full commitment → catch it early, roll back cheaply (the gated-rollout discipline). So expand-contract gives money migration the _three things it needs_: no downtime (always-working), no corruption (reversible + verified per phase), and early problem detection (gradual) — the correctness-first, conservative migration the triple constraint demands. The reversibility and gradualness are _correctness controls_: they ensure that at no point is the money corrupted-and-unrecoverable, and that problems surface small and early — exactly what the near-zero correctness budget requires for a live money-data migration.**

---

# Part 3 — Dual-writes, backfills, and verification by reconciliation

The _transition_ phase — where the real migration happens — hinges on three mechanisms: _dual-writes_ (write to both old and new), _backfill_ (migrate existing data), and — the money-critical part — _verification by reconciliation_ (prove old and new agree before cutting over).

## 3.1 Dual-writes and backfill

```text
DUAL-WRITES + BACKFILL (migrating the data during the transition):
  DUAL-WRITE — during the transition, write EVERY new operation to BOTH the old AND the new schema → so the new
     schema stays CURRENT (gets all new data) while the old remains the authoritative source → both are kept in
     sync going forward.
  BACKFILL — the new schema is empty of EXISTING data → BACKFILL it: copy the historical data from old to new
     (transformed as needed) → a potentially HUGE, SLOW operation (billions of ledger rows) → done in BATCHES,
     in the BACKGROUND, WITHOUT blocking live traffic → + dual-writes ensure NEW data isn't missed during the
     backfill.
  → TOGETHER: dual-writes (new data → both) + backfill (old data → new) → the new schema accumulates BOTH the
     ongoing new data AND the historical data → it converges to a COMPLETE copy → ready to become authoritative.
  → the BACKFILL must be: IDEMPOTENT (re-runnable — a batch can be retried, L2.5), RESUMABLE (a huge backfill
     spanning days must resume after an interruption, L2.17/L3-Section-1), and NON-BLOCKING (doesn't slow/stop
     live traffic) → reusing the async/batch/idempotency machinery.
  → ORDERING hazard: a row being backfilled WHILE it's dual-written (a race) → the backfill must handle this
     (idempotent + "new data wins" / careful ordering) → don't let the backfill OVERWRITE newer dual-written
     data with older historical data → a subtle correctness hazard.
```

**Dual-writes and backfill migrate the data during the transition: _dual-write_ — during the transition, write _every new operation_ to _both_ the old _and_ the new schema (so the new stays _current_ — gets all new data — while the old remains authoritative — both kept in sync going forward); _backfill_ — the new schema is empty of _existing_ data, so _backfill_ it by copying historical data from old to new (transformed as needed), a potentially _huge, slow_ operation (billions of ledger rows) done in _batches, in the background, without blocking live traffic_ (and dual-writes ensure _new_ data isn't missed during the backfill). Together — dual-writes (new data → both) + backfill (old data → new) — the new schema accumulates _both_ the ongoing new data _and_ the historical data, converging to a _complete copy_ ready to become authoritative. The backfill must be _idempotent_ (re-runnable — a batch can be retried, L2.5), _resumable_ (a huge backfill spanning days must resume after an interruption, L2.17/L3-Section-1), and _non-blocking_ (doesn't slow/stop live traffic) — reusing the async/batch/idempotency machinery. A subtle _ordering hazard_: a row being backfilled _while_ it's dual-written (a race) — the backfill must handle this (idempotent + "new data wins" / careful ordering) so it doesn't _overwrite newer dual-written data with older historical data_ — a correctness hazard. Dual-writes + backfill are the transition mechanics (keep the new current + fill in the history), reusing the idempotency/resumability/async machinery, with the ordering race between backfill and dual-write being a subtle correctness hazard to handle carefully.**

## 3.2 Verification by reconciliation (the money-critical step)

```text
VERIFICATION BY RECONCILIATION (prove old and new AGREE before cutover — the money-critical step):
  before you SHIFT READS to the new (and before you CONTRACT the old), you must VERIFY that the new schema is
     CORRECT — that it has ALL the data, correctly transformed, matching the old → because EVERY ROW IS MONEY
     (Part 1): if the new is missing/wrong rows, cutting over LOSES/CORRUPTS money.
  RECONCILE old vs new (L2-recon, applied to the migration):
     - COMPLETENESS — every row in old is in new (no lost rows / lost money).
     - CORRECTNESS — every value in new matches the (transformed) old (no mis-transformed money).
     - CONSERVATION — the new schema's totals/invariants match the old (Σ conservation holds in new too) → the
        money is CONSERVED across the migration.
  → this is RECONCILIATION (L2-recon) applied to the MIGRATION: reconcile the old data source against the new,
     prove they AGREE (completeness + correctness + conservation) → ONLY cut over when they RECONCILE → "don't
     cut over to the new until you've PROVEN it matches the old".
  → CONTINUOUS reconciliation during dual-write: as both are written, CONTINUOUSLY reconcile them → any
     DIVERGENCE (a dual-write bug, a backfill error) is caught in REAL TIME (observability, Topic 2) → don't
     proceed until they're consistently in agreement.
  → the CUTOVER is GATED on reconciliation: shift reads to the new ONLY when it's PROVEN (reconciled) correct →
     the reconciliation is the CORRECTNESS GATE for the migration (like the testing correctness gate, Topic 4,
     but for the data migration) → "prove the money matches, THEN cut over".
  → this is the SAME reconciliation that proves correctness THROUGHOUT the course (L2-recon, Section 3's solvency,
     Section 2's multi-provider) → now proving the MIGRATION preserved the money → reconciliation is the
     universal money-correctness-proof, here applied to migration.
```

**Verification by reconciliation is the money-critical migration step — _prove old and new agree before cutover_: before you _shift reads_ to the new (and before you _contract_ the old), you must _verify the new schema is correct_ — that it has _all_ the data, correctly transformed, matching the old — because _every row is money_ (if the new is missing/wrong rows, cutting over _loses/corrupts_ money). You _reconcile old vs new_ (L2-recon applied to the migration): _completeness_ (every old row is in new — no lost rows/money), _correctness_ (every new value matches the transformed old — no mis-transformed money), and _conservation_ (the new schema's totals/invariants match the old — Σ conservation holds in new too — the money _conserved_ across the migration). This is _reconciliation applied to the migration_: reconcile old against new, prove they _agree_, and _only cut over when they reconcile_ ("don't cut over to the new until you've _proven_ it matches the old"). Done _continuously_ during dual-write (as both are written, continuously reconcile — any divergence from a dual-write bug or backfill error caught in _real time_ via observability, Topic 2 — don't proceed until consistently in agreement). The _cutover is gated on reconciliation_: shift reads to the new _only_ when it's proven (reconciled) correct — the reconciliation is the _correctness gate for the migration_ (like the testing correctness gate, Topic 4, but for the data migration) — "prove the money matches, _then_ cut over." This is the _same reconciliation that proves correctness throughout the course_ (L2-recon, Section 3's solvency, Section 2's multi-provider), now proving the _migration preserved the money_ — reconciliation is the universal money-correctness-proof, here applied to migration. This is the deep synthesis: _reconciliation — the course's universal money-correctness-proof — gates the migration cutover_, so you never shift to the new schema until you've _proven_ (via completeness + correctness + conservation reconciliation) that it holds exactly the same money as the old, continuously verified during dual-write.** This is the key money-migration insight — **reconciliation (the course's correctness-proof) is the cutover gate: prove old == new before cutting over, because every row is money.**

---

# Part 4 — Migrating the immutable ledger: evolving without rewriting history

The hardest case: the **append-only, immutable ledger** (L2.1). You _can't rewrite history_ — so the standard "transform the rows" migration is forbidden. This requires a different approach: _evolve the future, preserve the past_.

```text
MIGRATING THE IMMUTABLE LEDGER (evolve the future, PRESERVE the past — you can't rewrite history):
  the PROBLEM: the ledger is APPEND-ONLY / IMMUTABLE (L2.1) → you CANNOT mutate existing entries (rewrite
     history breaks immutability, auditability, and compliance-required retention) → so "ALTER the ledger table
     and transform the rows" is FORBIDDEN → how do you change the ledger's schema/structure?
  THE APPROACHES (evolve the FUTURE, preserve the PAST):
     NEW ENTRIES IN THE NEW FORMAT — start writing NEW ledger entries in the new schema/format going forward,
        while OLD entries stay in the old format (immutable, untouched) → the ledger has a MIXED history (old
        format + new format) → readers handle BOTH formats (versioned entries) → the past is PRESERVED, the
        future EVOLVES.
     ADDITIVE ONLY — add new FIELDS/tables ALONGSIDE (expand-contract, Part 2) WITHOUT changing existing entries
        → new fields are null/default for old entries → readers handle the absence → purely additive, never
        mutating.
     ADJUSTMENT ENTRIES (not mutation) — if a DATA FIX is needed (not a schema change), you don't MUTATE the bad
        entry → you APPEND a CORRECTING/reversing entry (L2.1's reversing-entry discipline) → the history shows
        the original AND the correction (the audit trail intact) → "correct by appending, never by mutating".
     A NEW LEDGER + MIGRATION — in extreme cases, build a NEW ledger (new structure), MIGRATE the historical
        balances/state into it (as opening entries), keep the OLD ledger as an immutable archive → a "ledger
        version 2" with the old preserved → heavy, but sometimes necessary.
  → the PRINCIPLE: NEVER mutate immutable history → evolve by APPENDING (new-format entries, new fields,
     correcting entries) or by a NEW ledger that PRESERVES the old → the immutable past stays intact; evolution
     happens in the APPEND-ONLY future.
  → VERSIONED ENTRIES — entries carry a schema VERSION → readers interpret each entry by its version → the
     ledger gracefully holds MULTIPLE formats over time → the evolution mechanism for an append-only store.
  → this is the DEEP challenge: the IMMUTABILITY that makes the ledger CORRECT/AUDITABLE (the course's
     foundation) also makes it HARD to migrate (can't rewrite) → the resolution: evolve FORWARD (append new
     formats/corrections), never BACKWARD (mutate history) → immutability PRESERVED, evolution ENABLED.
```

**Migrating the immutable ledger is the hardest case — _evolve the future, preserve the past_ (you _can't rewrite history_): the problem is that the ledger is _append-only/immutable_ (L2.1), so you _cannot_ mutate existing entries (rewriting history breaks immutability, auditability, and compliance-required retention) — so "ALTER the ledger table and transform the rows" is _forbidden_. The approaches _evolve the future while preserving the past_: _new entries in the new format_ (start writing _new_ ledger entries in the new schema going forward, while _old_ entries stay in the old format — immutable, untouched — the ledger has a _mixed_ history, old + new format, and readers handle _both_ via _versioned entries_ — the past preserved, the future evolves), _additive only_ (add new fields/tables _alongside_ via expand-contract _without_ changing existing entries — new fields null/default for old entries, readers handle the absence — purely additive, never mutating), _adjustment entries not mutation_ (if a _data fix_ is needed, you don't _mutate_ the bad entry — you _append_ a _correcting/reversing_ entry — L2.1's reversing-entry discipline — the history shows the original _and_ the correction, the audit trail intact — "correct by appending, never by mutating"), and _a new ledger + migration_ (in extreme cases, build a _new_ ledger with the historical balances migrated in as _opening entries_, keeping the _old_ ledger as an immutable archive — a "ledger version 2" with the old preserved — heavy but sometimes necessary). The principle: _never mutate immutable history — evolve by appending_ (new-format entries, new fields, correcting entries) _or by a new ledger that preserves the old_ — the immutable past stays intact; evolution happens in the append-only future, with _versioned entries_ (each entry carries a schema version, readers interpret by version) as the evolution mechanism for an append-only store. This is the deep challenge: the _immutability that makes the ledger correct/auditable_ (the course's foundation) also makes it _hard to migrate_ (can't rewrite) — and the resolution is to _evolve forward_ (append new formats/corrections), never _backward_ (mutate history) — immutability preserved, evolution enabled. The profound insight: the immutable ledger — the course's correctness/audit foundation — is migrated not by _transforming_ it (forbidden) but by _evolving it forward_ (versioned new-format entries, additive fields, correcting appends, or a preserving new-ledger), so the very immutability that protects the money also shapes _how_ you evolve it — forward, by appending, never by rewriting the past.** This is the topic's hardest and most distinctive point — **you migrate an immutable ledger by evolving forward (append new formats/corrections), never by rewriting history, because the past is permanent.**

---

# Part 5 — The complete migration process and safety discipline

Synthesizing into the end-to-end process and the safety discipline that correctness-first demands.

```text
THE COMPLETE MIGRATION PROCESS (correctness-first, gated, reversible):
  0. PLAN — design the migration (expand-contract phases, the transformation, the reconciliation checks) +
     TEST it (property/golden/differential tests, Topic 4, on the migration logic) + a ROLLBACK plan per phase.
  1. EXPAND — add the new schema (additive, safe) → the system still works on the old.
  2. DUAL-WRITE — write new operations to BOTH; CONTINUOUSLY RECONCILE old vs new (catch divergence real-time).
  3. BACKFILL — migrate historical data (batched, background, idempotent, resumable, non-blocking); RECONCILE
     completeness + correctness + conservation as it progresses.
  4. VERIFY — reconcile old vs new fully (completeness + correctness + conservation) → PROVE they agree →
     the CUTOVER GATE (don't proceed until reconciled).
  5. SHIFT READS GRADUALLY — move reads from old to new INCREMENTALLY (1% → 100%), monitoring correctness +
     reconciliation at each step; ROLL BACK on any discrepancy.
  6. CONTRACT — once fully on the new + verified + the old is unused → remove the old (for the IMMUTABLE ledger:
     keep the old as an archive, don't delete the history).
  7. VERIFY AGAIN — post-migration reconciliation: the system is fully on the new, conservation holds, no money
     lost/created → PROVE the migration preserved the money.
  → SAFETY DISCIPLINE (correctness-first, Topic 1): at EVERY phase — RECONCILE (prove correctness), be REVERSIBLE
     (roll back if wrong), GRADUAL (small-scale first), OBSERVABLE (Topic 2 — watch the invariants throughout),
     TESTED (Topic 4 — the migration logic property/golden-tested), and CHAOS-VERIFIED (Topic 5 — the migration
     survives a failure mid-migration) → the migration is as CONSERVATIVE and VERIFIED as the near-zero
     correctness budget demands.
  → MID-MIGRATION FAILURE — the migration itself spans time (days for a huge backfill) → a crash/failure
     DURING the migration must not corrupt (idempotent/resumable backfill, dual-write consistency) → the
     migration process is itself DURABLE/RESUMABLE (a mini state machine, L2.17) → "the migration survives its
     own failures".
  → this is the SAME discipline as Section 2's PROVIDER MIGRATION (Topic 5): gated, reversible, gradually-
     shifted, reconciliation-verified, surviving-its-own-failures → provider migration and data migration are
     the SAME zero-downtime-migration discipline (expand-contract + dual-run + reconcile + gradual-cutover),
     applied to the provider vs the data model.
```

**The complete migration process is correctness-first, gated, and reversible: (0) _plan_ (design the expand-contract phases + the transformation + the reconciliation checks, _test_ the migration logic — property/golden/differential, Topic 4 — and a rollback plan per phase), (1) _expand_ (add the new schema — additive, safe), (2) _dual-write_ (write to both; _continuously reconcile_ old vs new — catch divergence real-time), (3) _backfill_ (migrate historical data — batched, background, idempotent, resumable, non-blocking; reconcile completeness + correctness + conservation as it progresses), (4) _verify_ (reconcile old vs new fully — _prove they agree_ — the _cutover gate_), (5) _shift reads gradually_ (move reads from old to new _incrementally_ — 1% → 100% — monitoring correctness + reconciliation at each step; roll back on any discrepancy), (6) _contract_ (once fully on the new + verified + the old unused, remove the old — for the _immutable ledger_, keep the old as an _archive_, don't delete the history), and (7) _verify again_ (post-migration reconciliation — the system is fully on the new, conservation holds, no money lost/created — _prove the migration preserved the money_). The _safety discipline_ (correctness-first, Topic 1) at _every_ phase: _reconcile_ (prove correctness), be _reversible_ (roll back if wrong), _gradual_ (small-scale first), _observable_ (Topic 2 — watch the invariants throughout), _tested_ (Topic 4 — the migration logic property/golden-tested), and _chaos-verified_ (Topic 5 — the migration survives a failure mid-migration) — as conservative and verified as the near-zero correctness budget demands. A _mid-migration failure_ must not corrupt (the migration spans time — days for a huge backfill — so a crash during it must be handled: idempotent/resumable backfill, dual-write consistency — the migration process is itself _durable/resumable_, a mini state machine, L2.17 — "the migration survives its own failures"). This is the _same discipline as Section 2's provider migration_ (Topic 5): gated, reversible, gradually-shifted, reconciliation-verified, surviving-its-own-failures — _provider migration and data migration are the same zero-downtime-migration discipline_ (expand-contract + dual-run + reconcile + gradual-cutover), applied to the provider vs the data model. The complete process unifies the whole section's disciplines (reconcile, reverse, gradual rollout, observe, test, chaos-verify) into a conservative, verified, reversible, self-surviving data migration — the same discipline as provider migration, applied to the most correctness-critical data.**

---

# Part 6 — How it composes with everything

```text
┌─ ZERO-DOWNTIME SCHEMA & LEDGER MIGRATION (evolve live money data, no downtime, no corruption) ─┐
│  TRIPLE CONSTRAINT: zero downtime · every row is money · immutable ledger → correctness-first,     │
│     conservative, verified                                                                         │
│  EXPAND-CONTRACT: add-new → dual-write + backfill + shift-reads → remove-old (always-working,      │
│     reversible, gradual) — same as Section 2 provider migration (Topic 5)                          │
│  DUAL-WRITE + BACKFILL (idempotent/resumable/non-blocking) → the new schema converges to complete  │
│  VERIFY BY RECONCILIATION (completeness + correctness + conservation) → the CUTOVER GATE (prove    │
│     old == new before shifting) — reconciliation as the migration correctness-proof                │
│  IMMUTABLE LEDGER: evolve FORWARD (versioned new-format entries, additive fields, correcting       │
│     appends, or a preserving new-ledger) — NEVER rewrite history                                   │
│  SAFETY: gated · reversible · gradual · observable · tested · chaos-verified · survives-its-own-   │
│     failures (durable/resumable migration)                                                         │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

How it composes with everything:

- **Immutable ledger (L2.1):** the hardest migration case — evolve forward (append), never rewrite; correcting entries are the data-fix mechanism; reversing-entry discipline.
- **Reconciliation (L2-recon):** the _cutover gate_ — prove old == new (completeness + correctness + conservation) before shifting; continuous reconciliation during dual-write.
- **Provider migration (Section 2 Topic 5):** the _same_ zero-downtime-migration discipline (expand-contract + dual-run + reconcile + gradual-cutover), applied to data instead of the provider.
- **Correctness-first (Topic 1):** the governing principle — never corrupt, migrate conservatively, gate on correctness.
- **Observability (Topic 2):** watch the invariants + the reconciliation throughout the migration; detect divergence real-time.
- **Testing (Topic 4):** property/golden/differential test the migration logic (the transformation is correctness-critical code).
- **Chaos (Topic 5):** verify the migration survives a mid-migration failure.
- **Idempotency/resumability (L2.5, L2.17, L3 Section 1):** the backfill is idempotent/resumable/non-blocking; the migration survives its own failures.
- **Scaled ledger (L3 Section 1):** a common _reason_ to migrate (sharding, restructuring for scale).

**Zero-downtime schema & ledger migration evolves live money data without downtime or corruption, under the _triple constraint_ (zero downtime + every row is money + immutable ledger → correctness-first, conservative, verified): via _expand-contract_ (add-new → dual-write + backfill + shift-reads → remove-old — always-working, reversible, gradual — the _same_ pattern as Section 2's provider migration), with _dual-write + backfill_ (idempotent/resumable/non-blocking) converging the new schema to complete, _verification by reconciliation_ (completeness + correctness + conservation) as the _cutover gate_ (prove old == new before shifting — reconciliation as the migration's correctness-proof), the _immutable ledger_ migrated by _evolving forward_ (versioned new-format entries, additive fields, correcting appends, or a preserving new-ledger — never rewriting history), and a _safety discipline_ (gated, reversible, gradual, observable, tested, chaos-verified, surviving-its-own-failures). It composes as the data-model counterpart of provider migration (Section 2 Topic 5 — same discipline), governed by correctness-first (Topic 1), gated by reconciliation (L2-recon), watched by observability (Topic 2), verified by testing (Topic 4) and chaos (Topic 5), built on idempotency/resumability (L2.5/L2.17), and preserving the immutable ledger (L2.1) — the discipline of evolving the most correctness-critical data there is, safely, forever.**

---

# Part 7 — Failure modes, the mandatory questions, operations

Run the curriculum's questions against ledger/schema migration:

- **What if the migration corrupts data (loses/duplicates/mis-transforms a row)?** → Every row is money → reconciliation (completeness + correctness + conservation) catches it _before_ cutover (the gate); you don't cut over until old == new is proven. Correctness-first: never proceed past an unreconciled phase.
- **What if you need downtime to migrate?** → Unacceptable for a live money system → expand-contract (always-working, no broken moment) gives zero downtime.
- **What if you must change the immutable ledger?** → You can't rewrite history → evolve forward (versioned new-format entries, additive fields, correcting appends, or a preserving new-ledger); never mutate the past.
- **What if a data fix is needed in the ledger?** → Append a correcting/reversing entry (L2.1), never mutate the bad entry — the history shows both.
- **What if the migration fails mid-way (a crash during a days-long backfill)?** → The backfill is idempotent/resumable; dual-writes keep consistency; the migration survives its own failures (durable/resumable, a mini state machine).
- **What if the new schema has a problem after cutover?** → Roll back (the old still exists until contract — keep it until verified); reversibility per phase; gradual shift catches it early at low scale.
- **What's the source of truth that the migration preserved the money?** → Reconciliation (old == new: completeness + correctness + conservation) before, during, and after — the migration correctness-proof.
- **What if a backfill race overwrites newer data with older?** → The backfill must be idempotent + "new data wins"/careful ordering — handle the backfill-vs-dual-write race.
- **Operational signals (migration-specific):** reconciliation old-vs-new (completeness/correctness/conservation — the cutover gate — must agree); backfill progress + consistency (is it converging, idempotent, resumable?); dual-write divergence rate (caught real-time — should be 0); read-shift progress + per-step correctness (gradual cutover); rollback readiness (can you revert at the current phase?); post-migration conservation (the money preserved). **Old-vs-new reconciliation agreement (the cutover gate) and dual-write divergence (should be 0) are the headline signals — a safe migration proves old == new (completeness + correctness + conservation) continuously, cuts over only when reconciled, shifts gradually, stays reversible, and preserves conservation end-to-end.**

---

# Part 8 — Common mistakes, trade-offs, interview Qs, exercises, mastery

## 8.1 Mistakes (each a real migration failure)

1. **Change-in-place** (requiring downtime / breaking live traffic) → not using expand-contract → downtime or breakage on a live money system. 2. **Cutting over without reconciliation** (not proving old == new) → losing/corrupting money (missing/wrong rows go live). 3. **Mutating the immutable ledger** (rewriting history to migrate) → breaking immutability/auditability/retention. 4. **Mutating a bad entry to fix data** (not a correcting append) → destroying the audit trail. 5. **Non-idempotent/non-resumable backfill** → a backfill failure corrupts or can't resume (billions of rows). 6. **Blocking backfill** (slowing/stopping live traffic) → availability loss during migration. 7. **Not handling the backfill-vs-dual-write race** → overwriting newer data with older (corruption). 8. **Big-bang cutover** (not gradual) → a problem hits full scale before detection. 9. **Not reversible** (can't roll back) → stuck with a corrupted new schema. 10. **No continuous reconciliation during dual-write** → divergence undetected until cutover (too late). 11. **Deleting the old immutable ledger at contract** (not archiving) → losing the historical record. 12. **Not testing the migration logic** (the transformation is correctness-critical code) → a transformation bug corrupts data. 13. **Not handling mid-migration failure** (the migration doesn't survive its own crash) → corruption mid-migration. 14. **Migrating fast and risky** (not correctness-first/conservative) → a correctness breach for speed.

## 8.2 Trade-offs (reason, don't memorize)

- **Expand-contract vs change-in-place:** zero-downtime + always-working + more phases (expand-contract) vs simpler but requires downtime (change-in-place). → Expand-contract (zero downtime is non-negotiable for money).
- **Dual-write overhead vs simplicity:** keeps new current + double-write cost (dual-write) vs simpler but new goes stale. → Dual-write (keep new current during transition).
- **Reconcile-before-cutover vs cut-over-and-hope:** prove correctness + takes longer (reconcile) vs faster + risky (hope). → Reconcile (prove old == new — every row is money).
- **Gradual vs big-bang cutover:** catch problems small/early + slower (gradual) vs faster + high-risk (big-bang). → Gradual (gated rollout — catch early, roll back cheaply).
- **Evolve-forward vs new-ledger (immutable):** additive/versioned on the existing (evolve-forward, lighter) vs a new ledger preserving the old (heavier, cleaner). → Evolve-forward where possible; new-ledger for extreme restructures.
- **Conservative vs fast migration:** safe + slow (conservative) vs fast + risky (aggressive). → Conservative (correctness-first; a migration breach is an incident).

## 8.3 Interview questions you should answer cold

1. Why is migrating a money system's data uniquely hard (the three constraints)? 2. What's expand-contract / parallel-change, and why does it give zero downtime? 3. How is this the same discipline as Section 2's provider migration? 4. What are dual-writes and backfill, and what must the backfill be (idempotent/resumable/non-blocking)? 5. What's the backfill-vs-dual-write race, and how do you handle it? 6. Why is verification by reconciliation the cutover gate? 7. What three things does the reconciliation prove (completeness/correctness/conservation)? 8. Why can't you rewrite the immutable ledger, and how do you migrate it (evolve forward)? 9. How do you fix bad data in an immutable ledger (correcting appends)? 10. What are versioned entries, and why do they enable append-only evolution? 11. Walk the complete migration process (plan → expand → dual-write → backfill → verify → shift → contract → verify). 12. Why must the migration survive its own failures (durable/resumable)? 13. How does correctness-first govern the migration (conservative, gated)? 14. How does the migration compose with testing (verify the logic) and chaos (survive mid-migration failure)?

## 8.4 Hands-on exercises (for when we implement)

1. **Expand-contract migration:** migrate a table/ledger schema via expand (add new) → dual-write → backfill → verify → shift reads → contract (remove old); keep the system working throughout (zero downtime). 2. **Dual-write + continuous reconciliation:** dual-write to old + new; continuously reconcile them; inject a dual-write bug → the reconciliation catches the divergence real-time. 3. **Idempotent/resumable backfill:** backfill historical data in batches; make it idempotent (re-run a batch) and resumable (interrupt + resume); handle the backfill-vs-dual-write race (new data wins). 4. **Reconciliation cutover gate:** reconcile old vs new (completeness + correctness + conservation); only cut over when they agree; show a missing/wrong row blocks the cutover. 5. **Immutable-ledger evolution:** evolve the ledger forward (write new-format versioned entries, add additive fields) WITHOUT mutating old entries; readers handle both formats; show the old history intact. 6. **Correcting append:** fix bad data via a reversing/correcting entry (L2.1), not a mutation; show the history shows both. 7. **Gradual read-shift + rollback:** shift reads 1% → 100%; inject a problem at 10% → roll back; show reversibility. 8. **Mid-migration failure:** crash during the backfill → resume cleanly (idempotent/resumable); assert no corruption. 9. **Post-migration conservation:** after the full migration, assert conservation holds (no money lost/created across the migration).

## 8.5 Mastery checklist (before "multi-region / active-active money systems")

- [ ] I understand the **three compounding constraints** (zero downtime · every row is money · immutable ledger) that make money-data migration uniquely hard, demanding **correctness-first, conservative, verified** migration.
- [ ] I can apply **expand-contract / parallel-change** (add-new → dual-write + backfill + shift-reads → remove-old — **always-working, reversible, gradual**) and know it's the **same discipline as Section 2's provider migration** (Topic 5).
- [ ] I can design **dual-writes** (keep the new current) + **backfill** (**idempotent, resumable, non-blocking**, handling the **backfill-vs-dual-write race**) during the transition.
- [ ] I understand **verification by reconciliation** (completeness + correctness + **conservation**) as the **cutover gate** — prove **old == new before shifting** — reconciliation as the migration's correctness-proof (continuous during dual-write).
- [ ] I can migrate the **immutable ledger** by **evolving forward** (versioned new-format entries, additive fields, **correcting appends** not mutations, or a **preserving new-ledger**) — **never rewriting history** — and know **versioned entries** enable append-only evolution.
- [ ] I can run the **complete process** (plan+test → expand → dual-write → backfill → verify → gradual shift → contract → verify) with the **safety discipline** (gated, reversible, gradual, observable, tested, chaos-verified) and a migration that **survives its own failures** (durable/resumable).
- [ ] I understand the migration composes with **correctness-first** (Topic 1 — the governing principle), **reconciliation** (L2-recon — the cutover gate), **provider migration** (Section 2 Topic 5 — the same discipline), **observability** (Topic 2), **testing** (Topic 4 — verify the migration logic), **chaos** (Topic 5 — survive mid-migration failure), **idempotency/resumability** (L2.5/L2.17), and the **immutable ledger** (L2.1).
- [ ] I can name the operational signals (**old-vs-new reconciliation agreement** = the cutover gate; **dual-write divergence** = 0; backfill progress/consistency; read-shift progress; rollback readiness; post-migration conservation).

---

## One-paragraph synthesis

Zero-downtime schema and ledger migration confronts the challenge of **changing the data model of a live money system without downtime and without corrupting a single cent**, made uniquely hard by _three compounding constraints_: **zero downtime** (payments must keep flowing _during_ the migration, so you migrate a _live, actively-processing_ system whose data is changing as you move it), **every row is money** (a migration bug doesn't lose a log line but _loses or duplicates real value_ — a dropped row is lost money, a duplicated row is created money, a mis-transformed value is wrong money — so the near-zero correctness budget applies to _every row_), and **the immutable append-only ledger** (you _cannot rewrite history_, because the financial record is permanent for correctness, audit, and compliance, so the standard "ALTER the table and transform the rows" migration is _forbidden_) — which together make it the hardest migration in software and dictate, by correctness-first, a _conservative, verified, reversible_ approach. The foundation is **expand-contract (parallel-change)**: rather than change-in-place (which breaks something during the change and requires downtime), you evolve in three always-working phases — **expand** (add the new schema alongside the old, purely additive), **transition** (dual-write to both, backfill the history, gradually shift reads), and **contract** (remove the old once unused and verified) — so the system is _never_ in a broken state (zero downtime) and is _reversible at each phase_ (roll back until committed), which is _the same gradual, dual-running, reversible discipline as Section 2's provider migration_ applied to the data model. The transition hinges on **dual-writes** (write every new operation to both old and new, keeping the new current) and **backfill** (copy the historical data into the new schema — a huge operation done _batched, in the background, idempotently and resumably, without blocking live traffic_, carefully handling the backfill-vs-dual-write race so it never overwrites newer data with older), and — the money-critical step — **verification by reconciliation**: because every row is money, you must _prove the new schema is correct before cutting over_ by reconciling old against new for **completeness** (no lost rows/money), **correctness** (no mis-transformed values), and **conservation** (the money totals match — conservation holds in the new too), _continuously_ during dual-write (catching any divergence in real time via observability) and as a _cutover gate_ (shift reads only when old and new provably agree) — so that **reconciliation, the course's universal money-correctness-proof, gates the migration**, and you never cut over to data you haven't _proven_ holds exactly the same money. The hardest case, the **immutable ledger**, is migrated by _evolving the future while preserving the past_ — never mutating existing entries (which would break immutability/auditability/retention) but instead writing **new-format versioned entries going forward** (the ledger holds a mixed, version-tagged history that readers interpret per version), adding **additive fields** alongside, fixing bad data by **appending a correcting/reversing entry** (L2.1's discipline — the history shows both the original and the correction) rather than mutating, or in extreme cases building a **new ledger with the old preserved as an immutable archive** — so the very immutability that makes the ledger correct and auditable also shapes _how_ it evolves: **forward, by appending, never backward by rewriting**. The complete process — plan and _test_ the migration logic (property/golden/differential, Topic 4, since the transformation is correctness-critical code), expand, dual-write with continuous reconciliation, backfill idempotently/resumably, verify by full reconciliation (the cutover gate), shift reads _gradually_ (1%→100%, rolling back on any discrepancy), contract (archiving rather than deleting immutable history), and verify again (post-migration conservation) — is governed at every phase by the **correctness-first safety discipline** (reconcile to prove correctness, stay reversible, go gradual, observe the invariants throughout, test the logic, chaos-verify that the migration _survives its own mid-migration failures_ via idempotent/resumable mechanics that make the migration itself a durable state machine), as conservative and verified as the near-zero correctness budget demands. Composed into the whole, this is the **data-model counterpart of Section 2's provider migration** — the _same_ zero-downtime-migration discipline (expand-contract + dual-run + reconcile + gradual-cutover + survive-own-failures) applied to the data model rather than the provider — unifying the course's reconciliation (the cutover correctness-proof), reversing-entry discipline (immutable-ledger evolution), idempotency and resumability (the backfill and self-surviving migration), observability (real-time divergence detection), testing and chaos (verifying the migration logic and its resilience), and correctness-first governance — so that a money system can evolve its schema, restructure its ledger, and adapt over its multi-year, can-never-be-rebuilt life _while it keeps processing payments_, _without ever losing or duplicating a cent_, and _without ever rewriting the immutable history_ — proving, by reconciliation, at every step, that the money that went into the migration is exactly the money that comes out.

When you've reviewed, say **continue** and we'll cover the next topic — **multi-region / active-active money systems** — running money across geographic regions: active-passive vs active-active architectures, the defining consistency challenge (you _cannot_ double-spend across regions — a balance decremented in two regions at once creates money), partitioning money by region, cross-region consistency (single-writer-per-account across regions, the in-transit/reconciliation triad from L3 Section 1), the latency-vs-consistency trade-off (CAP for money — consistency over availability), and region failover without double-processing — applying "correctness first" to the hardest distributed-systems problem for money.
