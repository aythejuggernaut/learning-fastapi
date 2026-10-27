We continue to **L3 Section 7, Topic 3 — Graceful degradation & failure modes**. Topics 1-2 established _what_ reliability means for money (correctness first) and _how to see it_ (observe the invariants). This topic is about what happens **under stress and failure**: how a money system _degrades gracefully_ rather than collapsing, and — the defining principle — how it **preserves correctness even at the cost of availability**, the inverse of most software. When ordinary systems are overloaded or partially failing, the instinct is "stay up at all costs." For money, that instinct is _wrong_: a system that stays up by processing _wrong_ is worse than one that sheds load or stops. This topic generalizes the fail-open/fail-closed decision (which recurred in idempotency, fraud, and payouts) into a principled framework, catalogs the failure modes, and shows how to degrade _correctly_. Definitive treatment, labeled parts, building on correctness-first (Topic 1), observability (Topic 2), and the fail-open/closed decisions throughout (L2.5, Section 5, Section 3).

---

# Part 1 — First principles: graceful degradation and the money inversion

## 1.1 What graceful degradation is, and the defining money principle

**Graceful degradation** = the design discipline of ensuring a system, when it _cannot fully operate_ (overload, partial failure, a dependency down), **degrades in a controlled, acceptable way — maintaining its most important functions and failing in a _chosen_, safe manner — rather than collapsing catastrophically or behaving unpredictably.** The alternative is _brittle_ failure: a small problem cascades into total, chaotic collapse.

For money, graceful degradation has a _defining inversion_ from ordinary systems:

```text
THE MONEY INVERSION (graceful degradation's defining principle for money):
  ORDINARY systems degrade to PRESERVE AVAILABILITY → "stay UP, even if degraded" → serve stale data, drop
     non-essential features, do WHATEVER keeps the system responding → availability is the thing to preserve.
  MONEY systems degrade to PRESERVE CORRECTNESS → "stay CORRECT, even if unavailable" → when you can't
     process CORRECTLY, you STOP (or queue) rather than process WRONG → CORRECTNESS is the thing to preserve,
     AVAILABILITY is what you sacrifice.
  → THE INVERSION: ordinary degradation sacrifices CORRECTNESS/completeness to preserve AVAILABILITY (serve
     something, even if stale/partial); MONEY degradation sacrifices AVAILABILITY to preserve CORRECTNESS
     (process nothing rather than process wrong) → the DIRECT consequence of "correctness first" (Topic 1:
     a wrong answer is worse than no answer).
  → so under stress/failure, a money system's graceful degradation means: SHED LOAD, QUEUE, SLOW DOWN, or
     STOP — but NEVER PROCESS INCORRECTLY → degrade AVAILABILITY to protect CORRECTNESS.
  → the KEY design question for every degradation: "does this degradation preserve CORRECTNESS?" → if a
     degradation would risk a double-charge / lost money / broken invariant, it's the WRONG degradation (even
     if it keeps the system "up") → correctness is the non-negotiable floor.
```

**Graceful degradation is the discipline of ensuring a system, when it _can't fully operate_ (overload, partial failure, a dependency down), _degrades in a controlled, chosen, safe way_ — maintaining its most important functions — rather than collapsing catastrophically. For money, it has a _defining inversion_ from ordinary systems: _ordinary_ systems degrade to _preserve availability_ ("stay up, even if degraded" — serve stale data, drop features, do whatever keeps responding), while _money_ systems degrade to _preserve correctness_ ("stay correct, even if unavailable" — when you can't process _correctly_, you _stop or queue_ rather than process _wrong_). The inversion: ordinary degradation _sacrifices correctness/completeness to preserve availability_ (serve something, even if stale/partial), while money degradation _sacrifices availability to preserve correctness_ (process nothing rather than process wrong) — the direct consequence of "correctness first" (Topic 1: a wrong answer is worse than no answer). So under stress/failure, a money system's graceful degradation means _shed load, queue, slow down, or stop — but never process incorrectly_ — degrading _availability_ to protect _correctness_. The key design question for every degradation is: _"does this degradation preserve correctness?"_ — if a degradation would risk a double-charge, lost money, or a broken invariant, it's the _wrong_ degradation (even if it keeps the system "up"); correctness is the non-negotiable floor. This inversion is the governing principle of the topic: money systems fail toward _correctness_ (stop/queue) rather than toward _availability_ (process anyway), the operational realization of Topic 1.**

## 1.2 Why "fail well" matters (the "why")

- **Failure is inevitable; _how_ you fail is a choice.** Dependencies go down, load spikes, bugs happen (the "assume breach"/"assume failure" posture, Section 6 Topic 9). You can't prevent all failure, but you _design_ how the system behaves when it fails. **Failure is inevitable, but _how_ the system fails is a design choice — graceful degradation is choosing to fail _safely_ (correctly, controllably) rather than catastrophically — the difference between a contained incident and a disaster.**
- **Brittle failure is catastrophic and correctness-breaking.** An un-designed failure cascades (one dependency down → the whole system collapses) and can _corrupt_ (a partial failure mid-transaction → a broken invariant). **Brittle (un-designed) failure both _cascades_ (small problem → total collapse) and _corrupts_ (partial failure → broken invariants) — graceful degradation prevents both (contains the failure _and_ preserves correctness).**

**The through-line: graceful degradation is designing _how_ a money system fails (failure is inevitable; the manner is a choice), with the defining money inversion — _preserve correctness even at the cost of availability_ (stop/queue rather than process wrong, the inverse of ordinary systems) — because for money a wrong answer is worse than no answer, and brittle failure both cascades and corrupts. The governing question for every degradation: does it preserve correctness?**

---

# Part 2 — The fail-open vs fail-closed framework (generalized)

The central decision in degradation — recurring throughout the course — is **fail-open vs fail-closed**: when a component fails, do you _proceed_ (fail-open, favor availability) or _stop_ (fail-closed, favor correctness/safety)? This topic _generalizes_ the decisions made in idempotency, fraud, and payouts into a principled framework.

## 2.1 The framework

```text
FAIL-OPEN vs FAIL-CLOSED (the central degradation decision — generalized):
  when a component/check FAILS or is UNAVAILABLE, you must decide: PROCEED or STOP?
     FAIL-OPEN — PROCEED without the failed component → favors AVAILABILITY (keep processing) → RISK: you
        proceed WITHOUT the check/component, possibly INCORRECTLY.
     FAIL-CLOSED — STOP (reject/block/queue) → favors CORRECTNESS/SAFETY (don't proceed without it) → RISK:
        you're UNAVAILABLE (you stopped).
  → the DECISION depends on the FAILURE COST (which recurred throughout): "what's worse — proceeding WITHOUT
     this component (fail-open risk) or STOPPING (fail-closed risk)?":
     - if proceeding-without risks a CORRECTNESS BREACH (money wrong) → FAIL-CLOSED (don't process wrong).
     - if proceeding-without is SAFE (correctness preserved) and stopping loses AVAILABILITY → FAIL-OPEN
       (keep serving good customers).
  → the COURSE'S EXAMPLES, now unified under this framework:
     IDEMPOTENCY (L2.5) — FAIL-CLOSED: if you can't verify idempotency, STOP (a double-charge — correctness
        breach — is worse than a declined payment) → correctness-protecting fail-closed.
     FRAUD DECISIONING (Section 5) — FAIL-OPEN (usually): if the fraud system is down, APPROVE (blocking ALL
        payments is worse than some fraud) → availability-protecting fail-open (BUT fail-CLOSED for final-rail
        payouts, where an irreversible fraudulent payout is worse).
     PAYOUTS / FINAL RAILS (Section 2/3) — FAIL-CLOSED: don't send an irreversible payout you can't verify
        (money wrong is worse than a delayed payout).
  → so the RULE: FAIL-CLOSED when proceeding risks CORRECTNESS (money wrong); FAIL-OPEN when proceeding is
     SAFE and stopping only costs AVAILABILITY → the failure cost (correctness-at-risk vs availability-at-risk)
     determines the direction.
```

**The central degradation decision — recurring throughout the course — is _fail-open vs fail-closed_: when a component/check _fails_ or is _unavailable_, do you _proceed_ (fail-open, favoring availability — keep processing, but _risk proceeding without the check, possibly incorrectly_) or _stop_ (fail-closed, favoring correctness/safety — don't proceed without it, but _risk being unavailable_)? The decision depends on the _failure cost_ (which recurred throughout): "what's worse — proceeding _without_ this component (fail-open risk) or _stopping_ (fail-closed risk)?" — if proceeding-without risks a _correctness breach_ (money wrong) → _fail-closed_ (don't process wrong); if proceeding-without is _safe_ (correctness preserved) and stopping loses availability → _fail-open_ (keep serving good customers). The course's examples unify under this framework: _idempotency_ (L2.5) fails _closed_ (if you can't verify idempotency, stop — a double-charge is worse than a declined payment); _fraud decisioning_ (Section 5) fails _open_ usually (if the fraud system is down, approve — blocking all payments is worse than some fraud — _but_ fails _closed_ for final-rail payouts where irreversible fraud is worse); _payouts/final rails_ (Section 2/3) fail _closed_ (don't send an irreversible payout you can't verify). The rule: _fail-closed when proceeding risks correctness (money wrong); fail-open when proceeding is safe and stopping only costs availability_ — the failure cost (correctness-at-risk vs availability-at-risk) determines the direction. This framework generalizes the scattered fail-open/closed decisions into one principled rule: the direction follows from _whether correctness or merely availability is at risk_ — fail toward correctness, fall open only when correctness is safe.** This is the key synthesis — **every fail-open/closed decision the course made is one application of a single rule: protect correctness (fail-closed) when it's at risk; protect availability (fail-open) only when correctness isn't.**

## 2.2 The nuance: fail-closed doesn't mean "lose the work" — queue it

```text
FAIL-CLOSED ≠ LOSE THE WORK (queue it — the key nuance):
  fail-CLOSED means "don't process INCORRECTLY NOW" → but that doesn't mean "drop the request / lose the work".
  → often the BEST fail-closed is to QUEUE / DEFER the work: don't process it wrong now, but HOLD it (durably)
     and process it CORRECTLY when the component recovers → you preserve BOTH correctness (don't process wrong)
     AND eventually the work (process it later, correctly).
  → e.g. the fraud system is down + it's a correctness-critical payout → don't send it wrong (fail-closed), but
     QUEUE it for when fraud is back → the payout isn't LOST, just DELAYED → correctness preserved, availability
     degraded (delayed), work not lost.
  → so the degradation spectrum isn't just PROCEED vs DROP → it's: PROCESS-NOW (fail-open) · QUEUE-FOR-LATER
     (fail-closed-but-don't-lose) · REJECT (fail-closed-and-drop, when you can't even queue) → QUEUING is the
     degradation that preserves correctness WITHOUT losing the work (the async/durable-queue machinery,
     L2.23-29, as a degradation tool).
  → this reuses the ASYNC foundations: a correctness-critical operation that can't complete NOW is QUEUED
     (durably) and processed when it can → "defer, don't corrupt, don't lose".
```

**A key nuance: _fail-closed doesn't mean "lose the work" — queue it_. Fail-closed means "don't process _incorrectly now_", but often the _best_ fail-closed response is to _queue/defer_ the work — don't process it wrong now, but _hold it durably_ and process it _correctly_ when the component recovers — preserving _both_ correctness (don't process wrong) _and_ the work (process it later). For example, if the fraud system is down and it's a correctness-critical payout, don't send it wrong (fail-closed), but _queue_ it for when fraud is back — the payout isn't _lost_, just _delayed_; correctness preserved, availability degraded (delayed), work not lost. So the degradation spectrum isn't just _proceed vs drop_ — it's _process-now_ (fail-open) · _queue-for-later_ (fail-closed-but-don't-lose) · _reject_ (fail-closed-and-drop, when you can't even queue) — where _queuing is the degradation that preserves correctness without losing the work_ (reusing the async/durable-queue machinery, L2.23-29, as a degradation tool). This reuses the async foundations: a correctness-critical operation that can't complete _now_ is _queued durably_ and processed when it can — "defer, don't corrupt, don't lose." This enriches the fail-closed option: the best money degradation is often _defer_ (queue correctly for later) rather than _reject_ (drop) — leveraging the durable queue to turn "can't process now" into "process correctly later," which is why async/durable queuing is a _degradation strategy_, not just a scaling one.**

---

# Part 3 — Degradation strategies: how to shed, queue, and degrade correctly

Beyond the fail-open/closed direction, there are concrete _strategies_ for degrading under stress — each must _preserve correctness_.

```text
DEGRADATION STRATEGIES (concrete ways to degrade — each must preserve CORRECTNESS):
  SHED LOAD — reject some requests (under overload) to keep the rest processing CORRECTLY → better to process
     SOME correctly than ALL incorrectly (overload-induced corruption) → shed the LEAST important / excess load
     → preserve correctness for what you DO process.
  QUEUE / DEFER — hold correctness-critical work (durably) for later correct processing (Part 2.2) → absorb a
     spike or a dependency outage without processing wrong or losing work.
  DEGRADE FEATURES (prioritize) — turn off NON-essential features to preserve the ESSENTIAL ones → keep CORE
     money movement working; drop nice-to-haves (analytics, non-critical reads, recommendations) → prioritize
     the correctness-critical core.
  FALLBACK (safely) — fall back to a degraded-but-CORRECT mode (e.g. a rules-only fraud safety net when the ML
     is down — Section 5; a cached INFORMATIONAL balance when the authoritative read is slow — BUT never a
     cached balance for a DECISION, L3 Section 1) → fall back ONLY to modes that preserve correctness.
  CIRCUIT BREAKERS (Section 2) — stop calling a failing dependency (fail fast) to avoid cascading / piling up
     indeterminate operations → the failover/circuit-breaker machinery as a degradation tool.
  RATE LIMITING / ADMISSION CONTROL — bound the load you accept to what you can process CORRECTLY → don't
     accept more than you can handle (which would cause overload-corruption).
  → EVERY strategy is CORRECTNESS-GATED: shed/queue/degrade/fallback ONLY in ways that preserve correctness →
     "degrade AVAILABILITY/FEATURES/COMPLETENESS, never CORRECTNESS".
  → the FORBIDDEN degradations (correctness-breaking): serving a stale balance for a DECISION (L3 Section 1),
     skipping idempotency under load (L2.5), processing without a required check that protects correctness,
     "best-effort" writes that might lose/duplicate money → these trade correctness for availability → WRONG
     for money.
```

**Degradation strategies are concrete ways to degrade under stress, _each gated on preserving correctness_: _shed load_ (reject some requests under overload to keep the rest processing _correctly_ — better to process _some_ correctly than _all_ incorrectly, shedding the least-important/excess load), _queue/defer_ (hold correctness-critical work durably for later correct processing — Part 2.2), _degrade features_ (turn off non-essential features to preserve the essential — keep core money movement working, drop nice-to-haves like analytics/recommendations — prioritizing the correctness-critical core), _fallback safely_ (fall back to a degraded-but-_correct_ mode — a rules-only fraud safety net when the ML is down (Section 5), a cached _informational_ balance when the authoritative read is slow — _but never a cached balance for a decision_ (L3 Section 1) — falling back only to modes that _preserve correctness_), _circuit breakers_ (Section 2 — stop calling a failing dependency to avoid cascading/piling-up indeterminate operations), and _rate limiting/admission control_ (bound the load you accept to what you can process _correctly_ — don't accept more than you can handle, which would cause overload-corruption). _Every strategy is correctness-gated_ — shed/queue/degrade/fallback _only_ in ways that preserve correctness: "degrade availability/features/completeness, _never_ correctness." And there are _forbidden degradations_ (correctness-breaking, wrong for money): serving a stale balance for a _decision_ (L3 Section 1), skipping idempotency under load (L2.5), processing without a required correctness-protecting check, "best-effort" writes that might lose/duplicate money — these trade correctness for availability, which is wrong for money. The unifying principle: _degrade the dispensable (availability, features, completeness, freshness-of-informational-reads), never the invariants (correctness)_ — and know the forbidden degradations that look tempting under load but break correctness.**

---

# Part 4 — Overload, backpressure, and admission control

A specific, critical failure mode: **overload** (more load than you can handle). For money, overload is especially dangerous because the naive response (accept everything, slow down) can cause _correctness_ failures — so you need _backpressure_ and _admission control_ to protect correctness under load.

```text
OVERLOAD + BACKPRESSURE + ADMISSION CONTROL (protecting correctness under load):
  OVERLOAD — more load than the system can process correctly → the NAIVE response (accept everything, process
     slower) → queues grow unbounded, timeouts cascade, resources exhaust, and — DANGEROUSLY — correctness can
     break (a half-completed transaction under resource exhaustion, a race under contention, an idempotency
     check that times out and gets skipped) → overload can CORRUPT, not just slow.
  BACKPRESSURE — PUSH BACK on the source of load when you can't keep up → signal "slow down" upstream (reject,
     delay, or block new work) rather than accept more than you can handle → prevents the unbounded-queue /
     resource-exhaustion collapse → the system STAYS within its correct-processing capacity.
  ADMISSION CONTROL — DECIDE WHAT TO ADMIT at the entrance → accept only as much as you can process CORRECTLY;
     reject/queue the excess → bound the in-flight work to the correct-processing capacity → "don't bite off
     more than you can correctly chew".
  → the KEY for money: accept only what you can process CORRECTLY → better to REJECT excess load (degrade
     availability) than to accept it and process INCORRECTLY under overload (corrupt) → admission control is
     CORRECTNESS-PROTECTING (bound the load to the safe capacity).
  → PRIORITIZE under admission control: admit the HIGH-VALUE / important work first (a $1M settlement over a
     $1 read); shed the low-priority → money-impact-weighted admission (like the alerting, Topic 2).
  → this connects to RATE LIMITING (Section 5 controls — velocity, and here load) + the ASYNC queue (L2.23-29,
     as a buffer) + the CIRCUIT BREAKER (Section 2) → the load-protection machinery, now as CORRECTNESS
     protection under overload.
```

**Overload (more load than you can handle) is especially dangerous for money because the _naive_ response (accept everything, process slower) causes queues to grow unbounded, timeouts to cascade, resources to exhaust, and — _dangerously_ — _correctness_ to break (a half-completed transaction under resource exhaustion, a race under contention, an idempotency check that times out and gets skipped) — so _overload can corrupt, not just slow_. The defenses: _backpressure_ (push back on the source of load when you can't keep up — signal "slow down" upstream, reject/delay/block new work rather than accept more than you can handle — preventing the unbounded-queue/resource-exhaustion collapse, keeping the system within its correct-processing capacity) and _admission control_ (decide what to admit at the entrance — accept only as much as you can process _correctly_, reject/queue the excess — bounding in-flight work to the correct-processing capacity: "don't bite off more than you can correctly chew"). The key for money: _accept only what you can process correctly_ — better to _reject_ excess load (degrade availability) than accept it and process _incorrectly_ under overload (corrupt) — so admission control is _correctness-protecting_ (bound the load to the safe capacity). You _prioritize_ under admission control (admit the high-value/important work first — a $1M settlement over a $1 read; shed the low-priority — money-impact-weighted, like the alerting in Topic 2). This connects to rate limiting (Section 5 controls), the async queue (as a buffer), and the circuit breaker (Section 2) — the load-protection machinery, now as _correctness protection under overload_. The critical money-specific insight: _overload can corrupt_ (not just slow), so backpressure and admission control aren't just performance tools — they're _correctness protections_ that keep the system within the capacity where it can process _correctly_, rejecting excess rather than corrupting.** This is a sharp money-specific point — **for money, admission control is a correctness control: you reject load you can't correctly process, because processing incorrectly under overload is worse than rejecting.**

---

# Part 5 — The failure-mode taxonomy and designing for it

To degrade gracefully, you must _know the failure modes_ and _design the degradation for each_. A taxonomy of payment failure modes and their correctness-preserving degradation.

```text
THE FAILURE-MODE TAXONOMY (and the correctness-preserving degradation for each):
  DEPENDENCY DOWN (a provider, the fraud system, a database replica) → FAIL-OPEN or FAIL-CLOSED per the failure
     cost (Part 2) → circuit-break the failing dependency; fall back (safely) or queue.
  OVERLOAD (too much load) → backpressure + admission control (Part 4) → shed/reject the excess, process the
     admitted correctly.
  PARTIAL FAILURE (a transaction fails MID-WAY) → the ATOMICITY/idempotency machinery (L2.1/L2.5): either the
     transaction COMPLETES or ROLLS BACK CLEANLY (no half-done state) → a partial failure must NOT leave a
     broken invariant (atomic transactions ensure this) → the correctness foundation handles this failure mode.
  INDETERMINATE OUTCOME (a timeout — did it happen? L2.5) → don't assume; VERIFY (status check) or mark
     NEEDS_VERIFICATION + reconcile → don't process wrong on uncertainty (fail toward verification).
  SLOW DEPENDENCY (not down, but slow) → TIMEOUT + fall back / degrade (don't let a slow dependency block
     everything — the latency-budget/timeout discipline, Section 5 Topic 2) → bound the wait.
  DATA CORRUPTION (a replica out of sync, a bad write) → detect (observability, Topic 2 — balance drift,
     conservation break) → fail-closed on the corrupted data (don't serve/use it) → use the authoritative
     source / reconcile.
  CASCADING FAILURE (one failure triggers others) → circuit breakers + bulkheads (isolate components so one's
     failure doesn't spread) + backpressure → CONTAIN the failure (don't let it cascade into total collapse).
  NETWORK PARTITION (components can't reach each other — preview, Topic 7) → CAP: choose CONSISTENCY over
     AVAILABILITY for money (don't process on both sides of a partition and double-spend) → fail-closed on the
     partition (preserve correctness).
  → for EACH failure mode, the degradation is designed to PRESERVE CORRECTNESS (fail-closed when correctness is
     at risk; fall back/queue safely otherwise) → "design the failure behavior for each mode, correctness-first".
  → BULKHEADS (isolation) + CIRCUIT BREAKERS (fail-fast) + TIMEOUTS (bound waits) + BACKPRESSURE (bound load) +
     the ATOMICITY/IDEMPOTENCY foundation (clean partial-failure) = the DESIGN TOOLKIT for graceful degradation
     → each failure mode handled by the right tool, all preserving correctness.
```

**To degrade gracefully you must _know the failure modes_ and design correctness-preserving degradation for each: _dependency down_ (a provider, the fraud system, a replica) → fail-open or fail-closed per the failure cost (circuit-break the failing dependency; fall back safely or queue), _overload_ → backpressure + admission control (shed/reject excess, process admitted correctly), _partial failure_ (a transaction fails mid-way) → the atomicity/idempotency machinery (L2.1/L2.5: the transaction either _completes_ or _rolls back cleanly_ — no half-done state leaving a broken invariant — the correctness foundation handles this), _indeterminate outcome_ (a timeout — did it happen? L2.5) → don't assume; verify or mark NEEDS_VERIFICATION + reconcile (fail toward verification), _slow dependency_ → timeout + fall back/degrade (don't let a slow dependency block everything — the latency-budget discipline), _data corruption_ (a replica out of sync, a bad write) → detect (observability, Topic 2 — balance drift, conservation break) + fail-closed on the corrupted data (don't serve/use it; use the authoritative source/reconcile), _cascading failure_ → circuit breakers + bulkheads (isolate components so one's failure doesn't spread) + backpressure (contain, don't cascade), and _network partition_ (preview, Topic 7) → CAP: choose consistency over availability for money (don't process on both sides and double-spend — fail-closed on the partition). For _each_ failure mode, the degradation is designed to _preserve correctness_ (fail-closed when correctness is at risk; fall back/queue safely otherwise). The _design toolkit_ is _bulkheads_ (isolation) + _circuit breakers_ (fail-fast) + _timeouts_ (bound waits) + _backpressure_ (bound load) + the _atomicity/idempotency foundation_ (clean partial-failure) — each failure mode handled by the right tool, all preserving correctness. The synthesis: graceful degradation is _knowing your failure modes and designing each one's behavior to preserve correctness_ — using a toolkit (bulkheads, circuit breakers, timeouts, backpressure, atomic transactions) where the correctness foundations the course built (atomicity, idempotency, reconciliation) handle the hardest failure modes (partial failure, indeterminate outcome, corruption) by design.**

---

# Part 6 — The complete graceful-degradation picture and how it composes

```text
┌─ GRACEFUL DEGRADATION (fail WELL — preserve CORRECTNESS even at the cost of AVAILABILITY) ─────┐
│  THE INVERSION (Topic 1): degrade AVAILABILITY to preserve CORRECTNESS (stop/queue, never corrupt) │
│  FAIL-OPEN vs FAIL-CLOSED (generalized): fail-CLOSED when correctness at risk (idempotency, payouts)│
│     ; fail-OPEN when safe + stopping only costs availability (fraud decisioning) — by FAILURE COST  │
│  FAIL-CLOSED ≠ LOSE: QUEUE/DEFER (durable, L2.23-29) → correctness preserved, work not lost         │
│  STRATEGIES (correctness-gated): shed load · queue · degrade features · fallback-safely ·           │
│     circuit-break · rate-limit → degrade the dispensable, NEVER the invariants                      │
│  OVERLOAD: backpressure + admission control → accept only what you can process CORRECTLY (overload   │
│     can CORRUPT) → correctness-protecting load control                                             │
│  FAILURE-MODE TAXONOMY: dependency-down · overload · partial-failure · indeterminate · slow ·       │
│     corruption · cascading · partition → each handled correctness-first (toolkit: bulkheads,        │
│     breakers, timeouts, backpressure, atomicity/idempotency)                                        │
│  → fail WELL (controlled, correctness-preserving) not catastrophically (cascading, corrupting)      │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

How it composes with everything:

- **Correctness-first (Topic 1):** graceful degradation is the _operational realization_ of "correctness first" — degrade availability to preserve correctness (the inversion).
- **Observability (Topic 2):** observability _detects_ the failure/overload/corruption that _triggers_ degradation; it watches whether degradation preserved correctness.
- **Idempotency (L2.5):** fail-closed on idempotency; the indeterminate-outcome handling; the clean-retry foundation.
- **Atomicity (L2.1):** clean partial-failure (complete or roll back — no broken invariant).
- **Async/queues (L2.23-29):** queuing as a degradation tool (defer, don't lose).
- **Circuit breakers / failover (Section 2):** the dependency-down degradation; cascading-failure containment.
- **Fraud (Section 5) / payouts (Section 2/3):** the fail-open/closed examples unified under the framework.
- **Multi-region/partition (Topic 7) / DR (Topic 8):** the partition and catastrophic-failure modes, handled correctness-first.

**Graceful degradation is failing _well_ — preserving correctness even at the cost of availability (the money inversion, Topic 1): the _fail-open/closed framework_ (fail-closed when correctness is at risk — idempotency, payouts; fail-open when safe and stopping only costs availability — fraud decisioning; by failure cost) with _fail-closed ≠ lose_ (queue/defer durably — correctness preserved, work not lost), the _correctness-gated strategies_ (shed, queue, degrade-features, fallback-safely, circuit-break, rate-limit — degrade the dispensable, never the invariants), _overload handling_ (backpressure + admission control — accept only what you can process correctly, since overload can _corrupt_), and the _failure-mode taxonomy_ (dependency-down, overload, partial-failure, indeterminate, slow, corruption, cascading, partition — each handled correctness-first with the toolkit of bulkheads, breakers, timeouts, backpressure, and the atomicity/idempotency foundation). It composes as the operational realization of correctness-first (Topic 1), triggered and verified by observability (Topic 2), built on idempotency (L2.5), atomicity (L2.1), and queues (L2.23-29), using the circuit-breaker/failover machinery (Section 2), unifying the fraud/payout fail-open/closed examples, and previewing the partition/DR handling (Topics 7-8) — the discipline of failing controllably and correctly rather than catastrophically.**

---

# Part 7 — Failure modes, the mandatory questions, operations

Run the curriculum's questions against graceful degradation:

- **What if the system is overloaded?** → Backpressure + admission control (accept only what you can process correctly — overload can corrupt); shed/queue the excess, prioritize by money impact. Don't accept more than you can correctly handle.
- **What if a dependency is down?** → Fail-open or fail-closed per the failure cost (correctness-at-risk → closed; safe → open); circuit-break it; fall back safely or queue.
- **What if a component you can't verify is needed (fail-open vs closed)?** → Fail-closed if proceeding risks correctness (don't process wrong); fail-open if safe and stopping only costs availability — by the failure cost.
- **What if a transaction fails mid-way?** → Atomicity (L2.1): complete or roll back cleanly — no half-done state / broken invariant. The correctness foundation handles partial failure.
- **What if degrading would risk correctness?** → Then it's the _wrong_ degradation (even if it keeps the system up) — degrade the dispensable, never the invariants; correctness is the non-negotiable floor.
- **What if you fail-closed — is the work lost?** → No — queue/defer it (durably) and process it correctly when the component recovers; fail-closed ≠ lose.
- **What's the source of truth that degradation preserved correctness?** → Observability (Topic 2) — the invariants still hold (conservation, no double-charge) during/after degradation; verify correctness was preserved.
- **What if a failure cascades?** → Bulkheads (isolate) + circuit breakers (fail-fast) + backpressure (bound load) → contain it; don't let one failure collapse everything.
- **Operational signals (degradation-specific):** degradation events (how often is the system degrading, and how?); correctness-during-degradation (did the invariants hold while degraded? — the critical check); load-shed/admission-reject rate (under overload); queue-depth/backpressure signals (is work being deferred? piling up?); fail-open/closed events (and the correctness outcome); circuit-breaker states; recovery time (how fast does it return to full operation?). **Correctness-during-degradation (the invariants held while degraded) is the headline signal — a well-degrading money system shows that even under stress/failure, correctness was preserved (availability degraded, invariants intact).**

---

# Part 8 — Common mistakes, trade-offs, interview Qs, exercises, mastery

## 8.1 Mistakes (each a real degradation failure)

1. **Degrading to preserve availability at the cost of correctness** (the ordinary-system instinct) → up-but-wrong (the money inversion violated). 2. **Fail-open when correctness is at risk** (proceeding without a correctness-protecting check) → a correctness breach. 3. **Fail-closed-and-drop when you could queue** → losing work unnecessarily (fail-closed ≠ lose). 4. **No admission control / backpressure under overload** → overload corrupts (unbounded queues, resource exhaustion, skipped checks). 5. **Accepting more load than you can process correctly** → overload-induced correctness failures. 6. **Serving a stale balance for a decision** (a forbidden degradation) → a wrong money decision. 7. **Skipping idempotency under load** → double-charges. 8. **"Best-effort" writes under stress** (might lose/duplicate money) → correctness breach. 9. **No circuit breakers** → cascading failure (one dependency down → total collapse). 10. **No bulkheads** (components not isolated) → one failure spreads. 11. **No timeouts on slow dependencies** → a slow dependency blocks everything. 12. **Brittle failure** (no designed degradation) → catastrophic + possibly corrupting collapse. 13. **Not handling partial failure** (no atomicity) → half-done transactions / broken invariants. 14. **Not verifying correctness was preserved during degradation** → a silent correctness breach while degraded.

## 8.2 Trade-offs (reason, don't memorize)

- **Fail-open vs fail-closed:** availability (open) vs correctness/safety (closed). → By the failure cost: fail-closed when correctness at risk; fail-open when safe + stopping only costs availability.
- **Queue vs reject (fail-closed):** preserve the work + delay (queue) vs drop + immediate (reject). → Queue when you can (don't lose correctness-critical work); reject when you can't even queue.
- **Shed load vs slow down:** reject excess + process the rest correctly (shed) vs accept all + risk overload-corruption (slow). → Shed/admission-control (don't accept more than you can correctly process).
- **Degrade features vs full service:** preserve the core + drop nice-to-haves (degrade) vs all-or-nothing. → Degrade features (prioritize the correctness-critical core).
- **Backpressure vs accept-everything:** bounded + push-back (backpressure) vs unbounded + collapse (accept). → Backpressure (stay within correct-processing capacity).
- **Correctness vs availability under failure:** stop/queue (correctness) vs process anyway (availability). → Correctness first (the money inversion) — degrade availability, preserve correctness.

## 8.3 Interview questions you should answer cold

1. What's graceful degradation, and what's the money inversion (vs ordinary systems)? 2. Why does money degrade to preserve correctness, not availability? 3. What's the fail-open vs fail-closed framework, and what determines the direction? 4. How do the course's examples (idempotency, fraud, payouts) fit the framework? 5. Why is fail-closed ≠ losing the work (queuing)? 6. What are the degradation strategies, and how is each correctness-gated? 7. What are the forbidden (correctness-breaking) degradations? 8. Why is overload especially dangerous for money (it can corrupt)? 9. What are backpressure and admission control, and why are they correctness-protecting? 10. Walk the failure-mode taxonomy and the degradation for each. 11. How do atomicity/idempotency handle partial failure and indeterminate outcomes? 12. What are bulkheads and circuit breakers (cascading-failure containment)? 13. How does observability trigger and verify degradation? 14. Why is correctness the non-negotiable floor for every degradation?

## 8.4 Hands-on exercises (for when we implement)

1. **Fail-open vs fail-closed:** implement a decision point where a check is unavailable; show fail-closed (stop — correctness-critical, e.g. a payout) vs fail-open (proceed — safe, e.g. fraud down) by the failure cost. 2. **Queue as fail-closed:** a correctness-critical operation that can't complete now → queue it durably → process it correctly when the dependency recovers (correctness preserved, work not lost). 3. **Admission control under overload:** bound in-flight work to a capacity; under overload, reject/queue the excess (prioritized by money impact); show the admitted work processes correctly while naive accept-everything would corrupt. 4. **Shed load:** under overload, shed low-priority requests to keep high-value ones processing correctly. 5. **Circuit breaker + fallback:** a failing dependency → circuit-break (fail-fast) + fall back safely (a correct degraded mode, e.g. rules-only fraud); show cascading is prevented. 6. **Partial-failure atomicity:** a transaction fails mid-way → it rolls back cleanly (no broken invariant) — the atomicity foundation. 7. **Forbidden-degradation detection:** show that serving a stale balance for a decision / skipping idempotency under load breaks correctness → flag these as forbidden. 8. **Correctness-during-degradation check:** run the invariant monitors (Topic 2) during a degradation; assert the invariants held (correctness preserved while availability degraded).

## 8.5 Mastery checklist (before "testing money systems")

- [ ] I understand **graceful degradation** (fail in a controlled, chosen, safe way, not catastrophically) and the defining **money inversion**: degrade **availability to preserve correctness** (stop/queue, never corrupt) — the inverse of ordinary systems, the operational realization of **correctness-first** (Topic 1).
- [ ] I can apply the **fail-open vs fail-closed framework** (fail-closed when proceeding risks **correctness**; fail-open when safe and stopping only costs **availability** — by the **failure cost**), unifying the course's examples (idempotency fail-closed, fraud fail-open, payouts fail-closed).
- [ ] I know **fail-closed ≠ lose the work** — **queue/defer** (durably, L2.23-29) preserves correctness _and_ the work (defer, don't corrupt, don't lose).
- [ ] I can apply the **correctness-gated degradation strategies** (shed load, queue, degrade features, fallback-safely, circuit-break, rate-limit — degrade the **dispensable**, never the **invariants**) and know the **forbidden degradations** (stale balance for a decision, skipping idempotency, best-effort writes).
- [ ] I understand **overload** is especially dangerous for money (**it can corrupt**, not just slow), and that **backpressure + admission control** (accept only what you can process **correctly**, money-impact-prioritized) are **correctness-protecting** load controls.
- [ ] I can handle the **failure-mode taxonomy** (dependency-down, overload, **partial-failure** via atomicity, **indeterminate** via verify, slow via timeout, corruption via detect+fail-closed, cascading via **bulkheads/circuit-breakers**, partition via consistency-over-availability) — each **correctness-first**, with the toolkit (bulkheads, breakers, timeouts, backpressure, atomicity/idempotency).
- [ ] I understand graceful degradation composes with **correctness-first** (Topic 1, the realization), **observability** (Topic 2, triggers + verifies), **idempotency/atomicity/queues** (the foundations), **circuit-breakers/failover** (Section 2), and the **fraud/payout** fail-open/closed examples, previewing **partition/DR** (Topics 7-8).
- [ ] I can name the operational signals (**correctness-during-degradation** as the headline — invariants held while degraded; degradation events; load-shed/admission-reject; queue depth/backpressure; fail-open/closed outcomes; recovery time).

---

## One-paragraph synthesis

Graceful degradation is the discipline of ensuring a money system, when it _cannot fully operate_ (overload, partial failure, a dependency down), **fails in a controlled, chosen, safe way — preserving its most important functions** rather than collapsing catastrophically, and its defining principle is the **money inversion**: where _ordinary_ systems degrade to _preserve availability_ ("stay up, even if degraded" — serve stale data, drop features, do whatever keeps responding), _money_ systems degrade to _preserve correctness_ ("stay correct, even if unavailable" — when you can't process _correctly_, you _stop or queue_ rather than process _wrong_), sacrificing availability to protect correctness because, per Topic 1, a wrong answer is worse than no answer — so the governing question for _every_ degradation is "does this preserve correctness?", and any degradation that would risk a double-charge, lost money, or a broken invariant is the _wrong_ degradation even if it keeps the system "up." The central decision is **fail-open vs fail-closed** — when a component fails, do you _proceed_ (fail-open, favoring availability but risking proceeding incorrectly) or _stop_ (fail-closed, favoring correctness but risking unavailability)? — determined by the **failure cost**: _fail-closed when proceeding risks correctness_ (a double-charge is worse than a declined payment — idempotency, Section 2/3 final-rail payouts) and _fail-open when proceeding is safe and stopping only costs availability_ (blocking all payments is worse than some fraud — fraud decisioning), which unifies the scattered decisions of the course into one rule: _fail toward correctness, fall open only when correctness is safe_; crucially, **fail-closed does not mean losing the work** — the best fail-closed response is often to **queue/defer** durably (the async machinery as a degradation tool) so the work is processed _correctly later_ ("defer, don't corrupt, don't lose"). The concrete **degradation strategies** — shed load, queue, degrade non-essential features (prioritizing the correctness-critical core), fall back _safely_ (to degraded-but-_correct_ modes like a rules-only fraud net or a cached _informational_ balance, but _never_ a cached balance for a _decision_), circuit-break, and rate-limit — are _each gated on preserving correctness_ ("degrade availability, features, completeness, and freshness-of-informational-reads, _never_ the invariants"), with _forbidden_ degradations (stale balance for a decision, skipping idempotency under load, best-effort writes) that tempt under stress but break correctness. **Overload** is especially dangerous for money because the naive "accept everything and slow down" can _corrupt_ (not just slow) — unbounded queues, resource exhaustion, a timed-out-and-skipped idempotency check, a race under contention — so **backpressure** (push back on the load source) and **admission control** (accept only as much as you can process _correctly_, money-impact-prioritized, rejecting/queuing the excess) are _correctness protections_, not just performance tools: better to reject excess (degrade availability) than accept it and process incorrectly (corrupt). And graceful degradation requires _knowing the failure modes and designing each one's correctness-preserving behavior_ — **dependency-down** (fail-open/closed by cost; circuit-break; fall back/queue), **overload** (backpressure/admission control), **partial failure** (the atomicity foundation: complete or roll back cleanly, never a half-done broken invariant), **indeterminate outcome** (don't assume; verify or mark NEEDS_VERIFICATION + reconcile), **slow dependency** (timeout + degrade), **data corruption** (detect via observability + fail-closed on the bad data), **cascading failure** (bulkheads to isolate + circuit breakers to fail fast + backpressure to bound load), and **network partition** (CAP: consistency over availability — don't process on both sides and double-spend) — each handled correctness-first with a toolkit (bulkheads, circuit breakers, timeouts, backpressure, atomicity/idempotency) where the correctness foundations the course built handle the hardest modes by design. Composed into the system, graceful degradation is the _operational realization_ of correctness-first (Topic 1), triggered and verified by observability (Topic 2 — which detects the overload/corruption that triggers degradation and confirms the invariants held while degraded), built on idempotency, atomicity, and durable queues, using the circuit-breaker/failover machinery of Section 2, and previewing the partition/DR handling of Topics 7-8 — so that when a money system is pushed beyond its limits or partially fails, it **fails _well_**: it sheds, queues, degrades, or stops in a controlled, correctness-preserving way, degrading availability to protect the invariants, never corrupting the money, never losing the work it can defer, and never trading the non-negotiable correctness floor for the tempting but wrong goal of staying "up" at all costs.

When you've reviewed, say **continue** and we'll cover the next topic — **testing money systems** — the correctness-verification discipline: property-based testing of the invariants (conservation, idempotency, monotonic state progression — automatically generating cases that try to break them), deterministic simulation and replay (reproducing complex concurrent/failure scenarios), golden tests (pinning known-correct behavior), and differential testing against providers (comparing your behavior to the real provider's) — how you _prove_ a money system is correct and that no change breaks an invariant, the verification that the near-zero correctness budget (Topic 1) demands.
