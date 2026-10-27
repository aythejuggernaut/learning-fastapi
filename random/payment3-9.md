We continue to **L3 Section 7, Topic 9 — Capacity, load & performance at peak**. The prior topics kept money systems correct, observable, resilient, verified, evolvable, globally-distributed, and disaster-recoverable. This topic confronts a routine-but-dangerous reality: **load spikes.** Black Friday, a payday surge, a viral moment, a flash sale — payment volume can jump 10×, 100×, or unpredictably. Ordinary systems handle this with autoscaling and "degrade gracefully if overwhelmed." For money, there's a sharper constraint: **you must scale to peak _without ever breaking correctness_.** The near-zero correctness budget (Topic 1) doesn't relax under load — a double-charge under Black Friday pressure is _still_ an incident. And load is especially dangerous for money because _overload can corrupt_ (Topic 3) and because peak _concentrates_ on hot accounts (the merchant everyone's buying from). This topic is about scaling to peak while the invariants hold — synthesizing the scaling machinery (Section 1), correctness-protecting admission control (Topic 3), and correctness-under-load testing (Topic 4). Definitive treatment, labeled parts.

---

# Part 1 — First principles: why peak load is a correctness problem for money

## 1.1 The core reframe: scale without breaking correctness

```text
PEAK LOAD FOR MONEY (the correctness constraint, not just a performance one):
  ORDINARY systems at peak: handle the load (autoscale, add capacity) OR degrade (serve slower, shed load) →
     the goal is AVAILABILITY/PERFORMANCE (handle the traffic, or degrade gracefully) → a performance problem.
  MONEY systems at peak: handle the load WITHOUT EVER BREAKING CORRECTNESS → the near-zero correctness budget
     (Topic 1) DOESN'T RELAX under load → a double-charge / lost payment / broken invariant under peak pressure
     is STILL an incident → "scale to peak, but the INVARIANTS must hold throughout" → a CORRECTNESS problem,
     not just a performance one.
  → the DANGER (Topic 3): overload can CORRUPT (not just slow) → under peak, the risk is that the system, pushed
     beyond capacity, breaks correctness (a race under contention, a skipped idempotency check under resource
     exhaustion, a lost write under overload) → peak load is a CORRECTNESS RISK.
  → so the goal is: HANDLE the peak (scale up) OR DEGRADE SAFELY (Topic 3 — shed/queue, preserving correctness)
     → but NEVER break correctness under load → "performance at peak, SUBJECT TO correctness" → you'd rather
     REJECT/DELAY load (degrade availability) than process it INCORRECTLY (break correctness) under peak.
  → the CORRECTNESS-FIRST principle (Topic 1) at peak: scale/degrade to serve the peak, but the INVARIANTS are
     non-negotiable → capacity/performance engineering for money is "go fast AND stay correct", with correct
     winning when they conflict.
```

**The core reframe is that _peak load for money is a correctness problem, not just a performance one_: _ordinary_ systems at peak aim for _availability/performance_ (handle the load via autoscaling, or degrade gracefully), while _money_ systems must handle the load _without ever breaking correctness_ — the near-zero correctness budget (Topic 1) _doesn't relax_ under load (a double-charge / lost payment / broken invariant under peak pressure is _still_ an incident) — so "scale to peak, but the _invariants_ must hold throughout," a correctness problem. The danger (Topic 3): _overload can corrupt_ (not just slow) — under peak, the risk is that the system, pushed beyond capacity, _breaks correctness_ (a race under contention, a skipped idempotency check under resource exhaustion, a lost write under overload) — so peak load is a _correctness risk_. The goal is to _handle_ the peak (scale up) _or degrade safely_ (Topic 3 — shed/queue, preserving correctness) but _never break correctness under load_ — "performance at peak, _subject to_ correctness" — you'd rather _reject/delay_ load (degrade availability) than process it _incorrectly_ (break correctness) under peak. This is correctness-first (Topic 1) at peak: scale/degrade to serve the peak, but the invariants are _non-negotiable_ — capacity/performance engineering for money is "go fast _and_ stay correct," with correct winning when they conflict. The reframe governs the topic: peak capacity engineering for money isn't just "handle the traffic" — it's "handle the traffic _while the invariants hold_," because the near-zero correctness budget applies under load as much as in steady state, and overload can corrupt.**

## 1.2 Why peak is especially dangerous for money (the money-specific risks)

- **Overload can corrupt (Topic 3).** The naive peak response (accept everything, slow down) risks correctness failures — a correctness risk unique to not-just-slow-but-corrupt. **Peak-induced overload can _corrupt_ (not just slow), so peak is a correctness threat — you must protect correctness under load.**
- **Peak concentrates on hot accounts.** A sale concentrates on _one merchant's_ account (everyone buying from them); a payday concentrates on _payroll_. Peak _concentrates_ load on specific accounts/partitions — the hot-account problem (Section 1) at its worst. **Peak _concentrates_ on hot accounts (the merchant everyone's buying from), making the hot-account/hot-partition problem (Section 1) acute at exactly the moment of highest load.**
- **Peak is when incidents cascade.** High load + a failure = cascading collapse; peak is when the system is most stressed and most likely to fail. **Peak is when the system is most stressed and failures most likely to cascade — so resilience (Topic 3) and correctness are most tested at peak.**

**The through-line: peak load is a _correctness_ problem for money (scale without breaking the invariants — the near-zero budget doesn't relax, overload can corrupt), made especially dangerous by overload-corruption, hot-account concentration (Section 1 at its worst), and cascade-at-peak — so capacity/performance engineering for money is "scale to peak while the invariants hold," synthesizing the scaling machinery (Section 1), correctness-protecting admission control (Topic 3), and correctness-under-load verification (Topic 4).**

---

# Part 2 — Capacity planning for money flows

Before the peak, you _plan_ capacity — but money capacity planning has specifics (plan for the _correctness-critical_ path, the hot accounts, and the money-flow shape).

```text
CAPACITY PLANNING FOR MONEY FLOWS (plan to handle the peak, correctness intact):
  FORECAST the peak — predict the load (predictable: Black Friday, payday, a known sale; unpredictable: a viral
     moment, a flash spike) → size for the PEAK (plus headroom), not the average → "plan for the spike".
  PLAN THE CORRECTNESS-CRITICAL PATH — the money-movement path (the ledger write, the idempotency check, the
     balance update) must have capacity to process the peak CORRECTLY → don't just scale the stateless front-end;
     scale the CORRECTNESS-CRITICAL core (the ledger/balance writes) → the bottleneck for money is usually the
     STATEFUL, single-writer-per-account core (Section 1), not the stateless layers.
  PLAN FOR HOT ACCOUNTS — identify the accounts that will be HOT at peak (the sale merchant, payroll) → ensure
     they can handle the concentrated load (striping, Section 1 — Part 3) → the hot-account problem is the
     capacity bottleneck at peak.
  PLAN THE MONEY-FLOW SHAPE — the peak isn't uniform: a sale = many CHARGES to one merchant (hot inbound); a
     payday = many PAYOUTS (hot outbound); each stresses different parts → plan for the SHAPE of the peak money
     flow.
  HEADROOM + the ERROR BUDGET — size with headroom (don't run at 100%) → leave capacity for the unexpected +
     for correctness-preserving degradation if the peak exceeds the forecast.
  → the KEY: capacity planning for money targets the CORRECTNESS-CRITICAL, STATEFUL, HOT-ACCOUNT path (the
     single-writer-per-account ledger core) — because that's where the money correctness lives AND where the
     peak bottleneck is → "plan capacity where correctness and the bottleneck coincide".
```

**Capacity planning for money flows plans to handle the peak with correctness intact: _forecast the peak_ (predictable — Black Friday, payday, a known sale; unpredictable — a viral moment, a flash spike — size for the _peak_ plus headroom, not the average), _plan the correctness-critical path_ (the money-movement path — the ledger write, the idempotency check, the balance update — must have capacity to process the peak _correctly_; don't just scale the stateless front-end, scale the _correctness-critical core_ — the bottleneck for money is usually the _stateful, single-writer-per-account core_ (Section 1), not the stateless layers), _plan for hot accounts_ (identify the accounts hot at peak — the sale merchant, payroll — ensure they handle the concentrated load via striping, Section 1 — the hot-account problem is the capacity bottleneck at peak), _plan the money-flow shape_ (the peak isn't uniform — a sale = many _charges_ to one merchant, hot inbound; a payday = many _payouts_, hot outbound — each stresses different parts), and _headroom + the error budget_ (size with headroom — don't run at 100% — leaving capacity for the unexpected + for correctness-preserving degradation if the peak exceeds the forecast). The key: capacity planning for money targets the _correctness-critical, stateful, hot-account path_ (the single-writer-per-account ledger core) — because that's where the money correctness lives _and_ where the peak bottleneck is — "plan capacity where correctness and the bottleneck coincide." The money-specific capacity-planning insight: the bottleneck _is_ the correctness-critical path (the stateful, single-writer, hot-account ledger core), so you plan capacity precisely where correctness lives, sizing for the peak money-flow shape (charges-to-a-merchant vs payouts) and the hot accounts it concentrates on.**

---

# Part 3 — The hot-account problem at peak: Section 1's scaling, at its worst

The defining capacity challenge at peak: **hot accounts.** Peak _concentrates_ load on specific accounts (the sale merchant, payroll), and because of _single-writer-per-account_ (Section 1 — required for correctness), that account's writes _serialize_ — a throughput bottleneck at exactly the moment of highest load. This reuses Section 1's hot-account solutions.

```text
THE HOT-ACCOUNT PROBLEM AT PEAK (Section 1's scaling, at its worst):
  the PROBLEM: peak CONCENTRATES load on specific accounts (a flash sale → everyone pays ONE merchant; payday →
     ONE payroll account) → but SINGLE-WRITER-PER-ACCOUNT (Section 1, required for no-double-spend correctness)
     means that account's writes must SERIALIZE (one at a time) → a THROUGHPUT WALL on the hot account at the
     peak → the hot account can't keep up → the bottleneck.
  → the TENSION: CORRECTNESS requires single-writer-per-account (serialize writes to prevent lost-update/double-
     spend); PEAK THROUGHPUT requires parallelism on the hot account → single-writer SERIALIZES, limiting
     throughput exactly where the load concentrates → correctness and peak-throughput COLLIDE on the hot account.
  THE SOLUTIONS (Section 1, Part on hot accounts — now at peak):
     STRIPING — split the hot account's balance into N STRIPES (sub-balances) → writes distribute across the N
        stripes (parallelism) → sum-on-read for the total → the hot account handles N× the throughput WHILE
        preserving correctness (each stripe is single-writer; the sum is conserved) → the primary hot-account
        solution (Section 1).
     BATCHING — batch many operations on the hot account into fewer writes → amortize the serialization.
     DEFER OFF THE HOT PATH — move non-critical work off the hot account's critical path (async) → reduce the
        hot-path contention.
  → so at peak, the hot account (the bottleneck) is handled by STRIPING (Section 1) → parallelism WITHOUT
     breaking single-writer correctness (each stripe single-writer, conservation holds) → "stripe the hot
     account to handle the peak, correctness intact".
  → this is the DIRECT payoff of Section 1's scaling: the hot-account striping built for SCALE is EXACTLY what
     handles the PEAK concentration → the scaling machinery (Section 1) IS the peak-capacity machinery → "the
     ledger scaling you built handles the peak".
```

**The hot-account problem at peak is Section 1's scaling at its worst: peak _concentrates_ load on specific accounts (a flash sale → everyone pays _one_ merchant; payday → _one_ payroll account), but _single-writer-per-account_ (Section 1, required for no-double-spend correctness) means that account's writes must _serialize_ (one at a time) → a _throughput wall_ on the hot account at the peak (the hot account can't keep up — the bottleneck). The tension: _correctness_ requires single-writer-per-account (serialize writes to prevent lost-update/double-spend) while _peak throughput_ requires parallelism on the hot account — single-writer _serializes_, limiting throughput exactly where the load concentrates — so correctness and peak-throughput _collide_ on the hot account. The solutions (Section 1, now at peak): _striping_ (split the hot account's balance into N _stripes_ — sub-balances — so writes distribute across the N stripes for parallelism, with sum-on-read for the total → the hot account handles N× the throughput _while preserving correctness_ — each stripe is single-writer, the sum is conserved — the primary hot-account solution), _batching_ (batch many operations into fewer writes — amortize the serialization), and _defer off the hot path_ (move non-critical work off the hot account's critical path — reduce contention). So at peak, the hot account (the bottleneck) is handled by _striping_ (Section 1) — parallelism _without_ breaking single-writer correctness (each stripe single-writer, conservation holds) — "stripe the hot account to handle the peak, correctness intact." This is the _direct payoff of Section 1's scaling_: the hot-account striping built for _scale_ is _exactly_ what handles the _peak_ concentration — the scaling machinery (Section 1) _is_ the peak-capacity machinery — "the ledger scaling you built handles the peak." The synthesis: the hot-account problem is _the_ peak-capacity bottleneck (correctness's single-writer-per-account collides with peak-throughput's need for parallelism), and _striping_ (Section 1) resolves it — N-way parallelism that preserves single-writer correctness per stripe and conservation overall — so the ledger-scaling machinery built in Section 1 is precisely what handles the peak concentration on hot accounts.**

---

# Part 4 — Correctness-protecting rate limiting and admission control (extending Topic 3)

When load exceeds capacity (the peak exceeds the forecast, or an unpredictable spike), you need **rate limiting and admission control** — but, extending Topic 3, these must _protect correctness_: accept only what you can process _correctly_, reject/queue the excess, because accepting more than you can correctly handle risks overload-corruption.

```text
CORRECTNESS-PROTECTING RATE LIMITING + ADMISSION CONTROL AT PEAK (extending Topic 3):
  when the peak EXCEEDS capacity (forecast wrong, an unpredictable spike) → you CAN'T process it all CORRECTLY →
     the choice (Topic 3): accept it all and risk OVERLOAD-CORRUPTION, or ADMISSION-CONTROL (accept only what
     you can process CORRECTLY, reject/queue the excess) → for money, ADMISSION CONTROL (correctness-protecting).
  RATE LIMITING — bound the rate of accepted requests to the CORRECT-PROCESSING capacity → shed/reject the
     excess → the system stays within the capacity where it processes CORRECTLY (never overloaded into
     corruption).
  ADMISSION CONTROL — decide WHAT to admit: accept only as much as you can process correctly; PRIORITIZE the
     important (money-impact-weighted — a large settlement over a small read) + shed the low-priority → bound the
     in-flight work to the correct-processing capacity.
  QUEUE THE EXCESS (Topic 3) — a correctness-critical operation that exceeds capacity → QUEUE it (durably,
     L2.23-29) for processing when capacity frees up → don't LOSE it, don't process it WRONG → "defer, don't
     corrupt, don't lose" (Topic 3) → the peak's excess is absorbed by the durable queue (processed slightly
     later, correctly).
  → the KEY (Topic 3, at peak): accept only what you can process CORRECTLY → REJECT/QUEUE the rest (degrade
     AVAILABILITY) rather than accept it and process INCORRECTLY under overload (break CORRECTNESS) → admission
     control is the CORRECTNESS PROTECTION at peak → "under peak overload, shed/queue to preserve correctness".
  → GRACEFUL DEGRADATION at peak (Topic 3): shed load · queue · degrade non-essential features · fall back
     safely → preserve the CORRECTNESS-CRITICAL money movement, degrade the rest → "handle the peak's money
     correctly; degrade everything else".
  → this EXTENDS Topic 3's overload handling (backpressure + admission control as correctness protection) to the
     PEAK scenario → the overload-handling machinery (Topic 3) IS the peak-protection machinery → "the
     degradation you built protects correctness at peak".
```

**Correctness-protecting rate limiting and admission control at peak extend Topic 3: when the peak _exceeds capacity_ (forecast wrong, an unpredictable spike), you _can't_ process it all _correctly_, so the choice (Topic 3) is accept-it-all-and-risk-overload-corruption or _admission-control_ (accept only what you can process _correctly_, reject/queue the excess) — for money, _admission control_ (correctness-protecting). _Rate limiting_ (bound the rate of accepted requests to the correct-processing capacity — shed/reject the excess — the system stays within the capacity where it processes _correctly_, never overloaded into corruption), _admission control_ (decide _what_ to admit: accept only as much as you can process correctly, _prioritize_ the important — money-impact-weighted, a large settlement over a small read — + shed the low-priority — bound the in-flight work to the correct-processing capacity), and _queue the excess_ (Topic 3 — a correctness-critical operation that exceeds capacity → _queue_ it durably for processing when capacity frees up — don't _lose_ it, don't process it _wrong_ — "defer, don't corrupt, don't lose" — the peak's excess absorbed by the durable queue, processed slightly later, correctly). The key (Topic 3, at peak): _accept only what you can process correctly_ — _reject/queue_ the rest (degrade _availability_) rather than accept it and process _incorrectly_ under overload (break _correctness_) — admission control is the _correctness protection_ at peak ("under peak overload, shed/queue to preserve correctness"). _Graceful degradation_ at peak (Topic 3): shed load, queue, degrade non-essential features, fall back safely — _preserve the correctness-critical money movement, degrade the rest_ ("handle the peak's money correctly; degrade everything else"). This _extends_ Topic 3's overload handling (backpressure + admission control as correctness protection) to the _peak_ scenario — the overload-handling machinery (Topic 3) _is_ the peak-protection machinery ("the degradation you built protects correctness at peak"). The synthesis: at peak overload, rate limiting + admission control + queuing _protect correctness_ (accept only what you can process correctly, queue/shed the rest, degrade the non-essential) — exactly Topic 3's overload handling, so the graceful-degradation machinery built earlier is precisely what keeps the peak from corrupting the money.**

---

# Part 5 — Load testing: verifying correctness under load (extending Topic 4)

Before the peak, you _test_ — but, extending Topic 4, money load testing has a _correctness-under-load_ dimension: not just "can it handle the load?" (performance) but "does _correctness hold_ under the load?" (the invariants under stress).

```text
LOAD TESTING WITH THE CORRECTNESS-UNDER-LOAD DIMENSION (extending Topic 4):
  ORDINARY load testing: can the system HANDLE the load? (throughput, latency under load) → a PERFORMANCE test.
  MONEY load testing ADDS: does CORRECTNESS HOLD under the load? → run the system at PEAK load (and beyond) and
     VERIFY the INVARIANTS hold (conservation, no double-charge, no lost write, no race) under the stress → "test
     that the money stays RIGHT under load, not just that the system stays UP".
  → the DANGER load testing catches: a correctness bug that ONLY appears under LOAD (a race that happens under
     high concurrency, a lost update under contention, an idempotency check that fails under resource pressure) →
     these DON'T appear at low load → you must test AT PEAK (and beyond) to find them → the overload-corruption
     risk (Topic 3) verified.
  → COMBINE with property-based + simulation (Topic 4): generate load (high concurrency, peak volume) +
     check the INVARIANTS under it → "property-based testing UNDER LOAD" → the invariants asserted at peak
     concurrency → catches the load-induced correctness bugs.
  STRESS / SOAK / SPIKE tests:
     STRESS — push BEYOND capacity → verify the system DEGRADES CORRECTLY (sheds/queues, Part 4) WITHOUT breaking
        correctness (not corrupting under overload) → "verify overload degrades, doesn't corrupt".
     SPIKE — a sudden surge (unpredictable peak) → verify the system handles the spike (admission control,
        scaling) without correctness loss.
     SOAK — sustained high load over time → verify no DRIFT / resource leak / slow correctness degradation.
  → so money load testing verifies BOTH performance (handles the load) AND correctness (invariants hold under
     load + overload degrades-not-corrupts) → the correctness-under-load dimension is the money-specific addition.
  → this EXTENDS Topic 4's correctness testing to the LOAD dimension (property/simulation UNDER load) + verifies
     the Part 4 admission-control/degradation designs (overload → degrade-not-corrupt) → the testing machinery
     (Topic 4) verifies the peak-correctness.
```

**Load testing with the correctness-under-load dimension extends Topic 4: _ordinary_ load testing asks "can the system _handle_ the load?" (throughput, latency — a performance test), while _money_ load testing _adds_ "does _correctness hold_ under the load?" (run the system at _peak_ load and beyond and _verify the invariants hold_ — conservation, no double-charge, no lost write, no race — under the stress — "test that the money stays _right_ under load, not just that the system stays _up_"). The danger it catches: a correctness bug that _only appears under load_ (a race under high concurrency, a lost update under contention, an idempotency check that fails under resource pressure) — these _don't_ appear at low load, so you must test _at peak and beyond_ to find them (the overload-corruption risk, Topic 3, verified). _Combine with property-based + simulation_ (Topic 4): _generate load_ (high concurrency, peak volume) + _check the invariants_ under it — "property-based testing _under load_" — the invariants asserted at peak concurrency, catching the load-induced correctness bugs. The test types: _stress_ (push _beyond_ capacity → verify the system _degrades correctly_ — sheds/queues, Part 4 — _without breaking correctness_ — "verify overload degrades, doesn't corrupt"), _spike_ (a sudden surge — unpredictable peak → verify the system handles it via admission control/scaling without correctness loss), and _soak_ (sustained high load over time → verify no _drift_/resource leak/slow correctness degradation). So money load testing verifies _both_ performance (handles the load) _and_ correctness (invariants hold under load + overload degrades-not-corrupts) — the correctness-under-load dimension is the money-specific addition. This _extends_ Topic 4's correctness testing to the _load_ dimension (property/simulation _under_ load) + verifies the Part 4 admission-control/degradation designs (overload → degrade-not-corrupt) — the testing machinery (Topic 4) verifies the peak-correctness. The money-specific load-testing insight: test not just that the system _handles_ the load but that _correctness holds under_ it (the invariants asserted at peak concurrency — property-based testing under load) and that _overload degrades-not-corrupts_ (stress/spike/soak tests verifying the admission-control/degradation designs) — extending Topic 4's correctness verification to the load dimension.**

---

# Part 6 — The complete peak-capacity picture and how it composes

```text
┌─ CAPACITY, LOAD & PERFORMANCE AT PEAK (scale to peak, invariants HOLD) ────────────────────────┐
│  THE CONSTRAINT: scale/degrade to serve the peak WITHOUT breaking correctness (the near-zero budget │
│     doesn't relax; overload can CORRUPT) → correctness-first (Topic 1) at peak                      │
│  CAPACITY PLANNING: forecast the peak + plan the CORRECTNESS-CRITICAL, STATEFUL, HOT-ACCOUNT path   │
│     + the money-flow shape (charges vs payouts) + headroom                                         │
│  HOT ACCOUNTS (the bottleneck): STRIPING (Section 1) → parallelism WITHOUT breaking single-writer   │
│     correctness → the scaling machinery IS the peak machinery                                      │
│  ADMISSION CONTROL (Topic 3): accept only what you can process CORRECTLY ; rate-limit/shed/QUEUE    │
│     the excess (money-impact-weighted) ; degrade non-essential ; preserve the money core            │
│  LOAD TESTING (Topic 4): verify correctness UNDER load (invariants at peak concurrency) + overload  │
│     DEGRADES-not-corrupts (stress/spike/soak) → the testing machinery verifies peak-correctness     │
│  → HANDLE the peak (scale: stripe, autoscale) OR DEGRADE SAFELY (admission control, Topic 3) → NEVER │
│     break correctness under load                                                                   │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

How it composes with everything:

- **Scaled ledger / hot-account striping (Section 1):** the scaling machinery (striping, partitioning, snapshots) _is_ the peak-capacity machinery — handles the hot-account concentration.
- **Graceful degradation / admission control (Topic 3):** the overload-handling machinery (admission control, backpressure, queue, shed) protects correctness at peak — "degrade-not-corrupt."
- **Testing (Topic 4):** correctness-under-load testing (property/simulation under load, stress/spike/soak) verifies the invariants hold at peak and overload degrades-not-corrupts.
- **Correctness-first (Topic 1):** the near-zero budget doesn't relax under load; scale/degrade but never break correctness.
- **Observability (Topic 2):** watch the correctness invariants + the capacity signals (hot-account throughput, admission-reject rate, queue depth) at peak.
- **Chaos (Topic 5):** chaos-test the peak (inject a spike, verify degrade-not-corrupt).
- **Async/queues (L2.23-29):** the durable queue absorbs the peak's excess (defer, don't corrupt, don't lose).
- **Single-writer-per-account (Section 1):** the correctness constraint that creates the hot-account bottleneck (resolved by striping).

**Capacity, load & performance at peak scales to peak while the invariants hold: the constraint is scale/degrade to serve the peak _without_ breaking correctness (the near-zero budget doesn't relax; overload can corrupt — correctness-first at peak); _capacity planning_ targets the correctness-critical, stateful, hot-account path + the money-flow shape + headroom; _hot accounts_ (the bottleneck) are handled by _striping_ (Section 1 — parallelism without breaking single-writer correctness — the scaling machinery _is_ the peak machinery); _admission control_ (Topic 3) accepts only what you can process correctly, rate-limits/sheds/queues the excess (money-impact-weighted), degrades the non-essential, preserves the money core; and _load testing_ (Topic 4) verifies correctness _under_ load (invariants at peak concurrency) + overload _degrades-not-corrupts_ (stress/spike/soak). It composes as the synthesis of Section 1 (scaling/striping = the peak machinery), Topic 3 (admission control/degradation = correctness protection at peak), Topic 4 (correctness-under-load testing = peak verification), governed by correctness-first (Topic 1 — never break correctness under load), watched by observability (Topic 2), chaos-tested (Topic 5), and absorbed by durable queues (L2.23-29) — the discipline of handling the peak (scale or degrade safely) while the money stays exactly right.**

---

# Part 7 — Failure modes, the mandatory questions, operations

Run the curriculum's questions against peak capacity:

- **What if the peak exceeds capacity?** → Admission control (accept only what you can process correctly) + rate-limit/shed/queue the excess (degrade availability, preserve correctness) — don't accept more than you can correctly handle (overload corrupts).
- **What if a hot account can't keep up (the bottleneck)?** → Striping (Section 1 — N-way parallelism without breaking single-writer correctness); batching; defer off the hot path. The scaling machinery handles the peak concentration.
- **What if overload corrupts (not just slows)?** → The correctness risk at peak → admission control bounds the load to the correct-processing capacity; load-test (stress) verifies overload degrades-not-corrupts.
- **What if a correctness bug only appears under load (a race)?** → Load testing with the correctness-under-load dimension (property/simulation under load, high concurrency) catches it before production.
- **What if the peak is unpredictable (a spike)?** → Headroom + admission control + autoscaling + the durable queue (absorb the spike); spike-test verifies handling.
- **What's the source of truth that correctness held at peak?** → The invariant monitors (Topic 2) during the peak (conservation, no double-charge held under load) + post-peak reconciliation.
- **How do you handle the peak without breaking correctness?** → Scale (stripe the hot accounts, autoscale the stateless layers) OR degrade safely (admission control, shed/queue) — never accept more than you can process correctly.
- **Operational signals (peak-capacity-specific):** capacity utilization vs the peak forecast (headroom); hot-account throughput + striping effectiveness (is the bottleneck relieved?); admission-reject / rate-limit / shed rate (under overload — degrading availability to preserve correctness); queue depth / backlog (the peak's excess deferred); correctness-under-load (the invariants holding at peak — the critical check); latency under load; autoscaling responsiveness. **Correctness-under-load (the invariants holding at peak — did the money stay right under the spike?) + hot-account throughput (the bottleneck relieved by striping) are the headline signals — a peak-ready money system scales the hot-account path (striping), admission-controls the excess (degrade-not-corrupt), and keeps the invariants holding throughout the peak.**

---

# Part 8 — Common mistakes, trade-offs, interview Qs, exercises, mastery

## 8.1 Mistakes (each a real peak-capacity failure)

1. **Treating peak as only a performance problem** (not correctness) → overload corrupts under peak. 2. **Accepting more load than you can process correctly** (no admission control) → overload-corruption. 3. **Not striping hot accounts** → the hot-account bottleneck throttles the peak (and if you try to parallelize naively, you break single-writer correctness). 4. **Breaking single-writer-per-account to handle the peak** (naive parallelism) → lost updates / double-spend. 5. **Only scaling the stateless front-end** (not the correctness-critical stateful core) → the bottleneck (the ledger/balance writes) still throttles. 6. **No load testing under the correctness dimension** → a load-induced correctness bug (a race) ships. 7. **No stress test** (overload degrade-not-corrupt unverified) → overload corrupts in production. 8. **Not planning for the money-flow shape** (charges vs payouts) → the wrong part scaled. 9. **Running at 100% (no headroom)** → no capacity for the unexpected / degradation. 10. **Losing the peak's excess** (not queuing) → lost work (should defer, don't lose). 11. **Processing the excess incorrectly** (not rejecting/queuing) → overload-corruption. 12. **Not prioritizing by money impact under admission control** → a large settlement shed while small reads admitted. 13. **Not watching correctness during the peak** (only watching latency) → a correctness breach under load undetected. 14. **Not chaos-testing the peak** (the spike/degradation designs unverified) → they fail at the real peak.

## 8.2 Trade-offs (reason, don't memorize)

- **Scale vs degrade at peak:** add capacity (scale — handle it) vs shed/queue (degrade — if capacity insufficient). → Scale where you can (stripe, autoscale); degrade safely (admission control) when the peak exceeds capacity — never break correctness.
- **Accept-everything vs admission-control:** serve all + risk overload-corruption vs serve what you can correctly + reject excess. → Admission-control (accept only what you can process correctly).
- **Striping degree vs complexity:** more stripes + more hot-account throughput + more complexity (sum-on-read) vs fewer + simpler. → Stripe to the needed throughput for the hot accounts at peak.
- **Headroom vs cost:** more headroom + safer at peak + more cost vs less + cheaper + riskier. → Enough headroom for the forecast peak + the unexpected + degradation.
- **Queue vs reject the excess:** preserve the work + delay (queue) vs drop + immediate (reject). → Queue correctness-critical work (don't lose); reject when you can't queue.
- **Load-test realism vs cost:** realistic peak + beyond (thorough) + cost vs cheaper + gaps. → Test at and beyond peak (find the load-induced bugs); the near-zero budget demands it.

## 8.3 Interview questions you should answer cold

1. Why is peak load a correctness problem for money (not just performance)? 2. Why can overload corrupt (not just slow)? 3. How does peak concentrate on hot accounts, and why is that the bottleneck? 4. How does single-writer-per-account (correctness) collide with peak throughput? 5. How does striping (Section 1) resolve the hot-account bottleneck without breaking correctness? 6. What's capacity planning for money flows (the correctness-critical path)? 7. How do admission control + rate limiting protect correctness at peak? 8. Why accept only what you can process correctly (queue/shed the rest)? 9. What's the correctness-under-load dimension of load testing? 10. What are stress/spike/soak tests, and what do they verify for money? 11. How do you load-test the invariants (property/simulation under load)? 12. How is the scaling machinery (Section 1) the peak machinery? 13. How is the degradation machinery (Topic 3) the peak-protection machinery? 14. How does correctness-first govern peak capacity?

## 8.4 Hands-on exercises (for when we implement)

1. **Hot-account striping at peak:** simulate a flash sale (many concurrent charges to one merchant); show single-writer-per-account serializes (the bottleneck); stripe the hot account (Section 1); show N× throughput WITH conservation holding (no lost update). 2. **Admission control:** under a load spike exceeding capacity, admit only what you can process correctly (money-impact-prioritized); reject/queue the excess; show the admitted work processes correctly while naive accept-everything corrupts. 3. **Correctness under load:** run property-based invariant tests (conservation, no-double-charge) UNDER high concurrency / peak load; show a load-induced race is caught. 4. **Stress test (degrade-not-corrupt):** push beyond capacity; verify the system degrades (sheds/queues) WITHOUT breaking correctness (invariants hold); contrast with naive overload (corrupts). 5. **Spike test:** a sudden surge; verify admission control + the durable queue absorb it without correctness loss. 6. **Queue the excess:** the peak's excess correctness-critical work is queued (durably) and processed correctly when capacity frees up (defer, don't lose, don't corrupt). 7. **Capacity planning:** model the money-flow shape (charges-to-a-merchant vs payouts); identify the hot-account bottleneck; size the striping. 8. **Observe correctness at peak:** run the invariant monitors (Topic 2) during a simulated peak; assert the invariants held throughout (the money stayed right under load).

## 8.5 Mastery checklist (before "incident response & money-incident playbooks")

- [ ] I understand peak load is a **correctness problem** for money (scale/degrade to serve the peak **without breaking the invariants** — the near-zero budget doesn't relax, **overload can corrupt**) — correctness-first (Topic 1) at peak.
- [ ] I can do **capacity planning for money flows** (forecast the peak; plan the **correctness-critical, stateful, hot-account path**; the money-flow shape — charges vs payouts; headroom) — "plan capacity where correctness and the bottleneck coincide."
- [ ] I understand the **hot-account problem at peak** (peak concentrates on hot accounts; **single-writer-per-account correctness collides with peak throughput**) and that **striping** (Section 1) resolves it (N-way parallelism **without breaking single-writer correctness** — the scaling machinery IS the peak machinery).
- [ ] I can apply **correctness-protecting admission control + rate limiting** (extending Topic 3): accept only what you can process **correctly**; rate-limit/shed/**queue** the excess (money-impact-weighted); **degrade non-essential, preserve the money core** — "under peak overload, shed/queue to preserve correctness."
- [ ] I can do **load testing with the correctness-under-load dimension** (extending Topic 4): verify the **invariants hold under load** (property/simulation at peak concurrency) + overload **degrades-not-corrupts** (**stress/spike/soak** tests) — catching the **load-induced correctness bugs**.
- [ ] I understand the resolution: **handle the peak** (scale — stripe hot accounts, autoscale stateless layers) **OR degrade safely** (admission control, Topic 3) — **never break correctness under load**.
- [ ] I understand peak capacity composes with **scaled-ledger/striping** (Section 1 — the peak machinery), **graceful degradation/admission control** (Topic 3 — correctness protection), **testing** (Topic 4 — correctness-under-load), **correctness-first** (Topic 1), **observability** (Topic 2), **chaos** (Topic 5 — spike-test), and **async/queues** (L2.23-29 — absorb the excess).
- [ ] I can name the operational signals (**correctness-under-load** — the invariants holding at peak; **hot-account throughput**/striping effectiveness; admission-reject/shed rate; queue depth; capacity utilization vs forecast; latency under load) of a peak-ready money system.

---

## One-paragraph synthesis

Capacity, load & performance at peak confronts the routine-but-dangerous reality of load spikes (Black Friday, a payday surge, a viral moment, a flash sale — volume jumping 10×, 100×, or unpredictably) and reframes them, for money, from a _performance_ problem into a **correctness** problem: where ordinary systems at peak aim to _handle the load or degrade gracefully_ for availability, money systems must **scale to peak _without ever breaking correctness_**, because the **near-zero correctness budget (Topic 1) does not relax under load** — a double-charge, lost payment, or broken invariant under Black Friday pressure is _still_ an incident — and because, as Topic 3 established, **overload can _corrupt_, not just slow** (a race under contention, a skipped idempotency check under resource exhaustion, a lost write under pressure), making peak a genuine _correctness risk_. **Capacity planning** therefore targets the **correctness-critical, stateful, hot-account path** (the single-writer-per-account ledger core — where both the money correctness _and_ the peak bottleneck live, since scaling the stateless front-end is insufficient), sizing for the _peak money-flow shape_ (a sale is many charges to one merchant — hot inbound; a payday is many payouts — hot outbound) with headroom for the unexpected. The defining bottleneck is the **hot-account problem at peak** — peak _concentrates_ load on specific accounts (everyone paying the one sale merchant, the one payroll account), but the **single-writer-per-account invariant** (Section 1, required to prevent lost-update/double-spend) forces that account's writes to _serialize_, creating a throughput wall exactly where the load concentrates, so **correctness (single-writer) collides with peak-throughput (parallelism)** — and the resolution is **striping** (Section 1): split the hot account's balance into N stripes so writes distribute for N-way parallelism _while preserving correctness_ (each stripe single-writer, the sum conserved), which means **the ledger-scaling machinery built in Section 1 _is_ the peak-capacity machinery** ("the scaling you built handles the peak"). When the peak _exceeds_ capacity (a bad forecast or an unpredictable spike), **correctness-protecting rate limiting and admission control** (extending Topic 3) accept _only what can be processed correctly_ and **reject, shed, or durably queue the excess** (money-impact-prioritized — a large settlement over a small read), degrading _availability_ and non-essential features to **preserve the correctness-critical money movement**, because for money you would rather reject/delay load than accept it and process it _incorrectly_ under overload ("defer, don't corrupt, don't lose") — so **the graceful-degradation machinery of Topic 3 _is_ the peak-protection machinery**. And before the peak, **load testing** (extending Topic 4) adds the money-specific **correctness-under-load dimension**: not just "can the system handle the load?" but "do the _invariants hold_ under the load?" — running **property-based and simulation testing _under_ high concurrency and peak volume** to catch the correctness bugs (races, lost updates, idempotency failures) that _only appear under load_ and never at low concurrency, plus **stress tests** (push beyond capacity → verify the system _degrades-not-corrupts_), **spike tests** (a sudden surge → verify admission control absorbs it correctly), and **soak tests** (sustained load → verify no drift or slow correctness degradation), so **the testing machinery of Topic 4 verifies the peak-correctness**. The resolution is always the same: **handle the peak** (scale — stripe the hot accounts, autoscale the stateless layers) _or_ **degrade safely** (admission control, shed, queue) — but _never break correctness under load_. Composed into the whole, peak-capacity engineering is the synthesis of Section 1 (hot-account striping, partitioning, snapshots — the scaling machinery _is_ the peak machinery), Topic 3 (admission control, backpressure, queuing, degradation — the correctness protection at peak), and Topic 4 (correctness-under-load testing — the peak verification), governed by correctness-first (Topic 1 — the invariants are non-negotiable under load), watched by observability (Topic 2 — the invariant monitors confirming the money stayed right _during_ the peak), chaos-tested (Topic 5 — injecting spikes to verify degrade-not-corrupt), and absorbed by durable queues (L2.23-29 — the peak's excess deferred for correct later processing) — so that a money system can survive the predictable Black Friday and the unpredictable viral surge, scaling its hot-account path for the concentrated load, shedding or queuing what it cannot correctly process, and verifying through load testing that even at and beyond peak the invariants hold — handling the flood of money _while keeping every cent of it exactly right_, because peak performance, for money, is always subject to the non-negotiable constraint of correctness.

When you've reviewed, say **continue** and we'll cover the next topic — **incident response & money-incident playbooks** — the money-specific deep-dive on Section 6 Topic 9's incident lifecycle: detecting money _loss_ (not just a breach), containment that stops ongoing money damage, remediation via _correcting entries_ (the append-only reversing-entry discipline from L2.1, now as incident response), customer/merchant communications about money, and the _post-incident reconciliation_ that proves the books are right again — how you respond to a money incident (a double-charge wave, a stuck-payment pileup, a balance-corruption event) and restore financial correctness, provably.
