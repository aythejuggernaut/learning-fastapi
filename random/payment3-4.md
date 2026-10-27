We continue to **L3 Section 7, Topic 4 — Testing money systems**. Topic 1 established that money systems have a _near-zero correctness error budget_ — a correctness breach (double-charge, lost money, broken invariant) is an _incident_, not a budgeted cost — which means every change must be _verified_ not to break correctness before it ships. This topic is that verification discipline. Ordinary testing checks "does the code do what I expect on the cases I thought of?" Money testing must do something stronger: **prove the _invariants_ hold across _all_ behaviors, including the concurrent, failure-laden, adversarial cases you didn't think of.** That requires techniques beyond example-based unit tests — **property-based testing** (generate cases that _try to break_ the invariants), **deterministic simulation** (reproduce complex concurrent/failure scenarios), **golden tests** (pin known-correct behavior), and **differential testing** (compare against the real provider). This is how you discharge the near-zero correctness budget. Definitive treatment, labeled parts, building on the correctness budget (Topic 1), the invariants (L2.3, L2.5, L2.17), and the whole correctness foundation.

---

# Part 1 — First principles: why money testing is different (and harder)

## 1.1 The core shift: from "does it work?" to "do the invariants always hold?"

The foundational reframe — ordinary testing verifies _expected behavior on chosen examples_; money testing must verify _invariants across all behaviors_:

```text
ORDINARY vs MONEY TESTING (the two questions):
  ORDINARY testing asks: "does the code do what I EXPECT, on the CASES I THOUGHT OF?" → example-based unit
     tests (given input X, assert output Y) → verifies the HAPPY PATH + the edge cases you IMAGINED.
  MONEY testing must ask: "do the INVARIANTS ALWAYS HOLD, across ALL behaviors — including the concurrent,
     failure-laden, adversarial cases I DIDN'T think of?" → because the near-zero correctness budget (Topic 1)
     means ANY sequence that breaks an invariant (conservation, no-double-charge) is an INCIDENT → you must
     verify the invariants hold UNIVERSALLY, not just on chosen examples.
  → THE PROBLEM with example-based tests for money: the DANGEROUS bugs are in the cases you DIDN'T think of —
     a specific concurrency interleaving, a crash at a specific point, an unusual sequence → example tests only
     check what you IMAGINED → they MISS the unimagined correctness-breaking case → and for money, the
     unimagined case is a double-charge / lost money.
  → so money testing needs techniques that EXPLORE the space of behaviors (not just chosen examples) and CHECK
     THE INVARIANTS across them → PROPERTY-BASED testing (generate many cases, check invariants),
     SIMULATION (explore concurrency/failure), DIFFERENTIAL (compare to the real thing) → VERIFY correctness
     UNIVERSALLY, not just on the happy path.
  → the SHIFT: from "assert specific outputs on specific inputs" (example) to "assert INVARIANTS hold over
     GENERATED/EXPLORED behaviors" (property/simulation) → test the PROPERTIES, not just the examples.
```

**The core shift is from "does the code do what I _expect_, on the _cases I thought of_?" (ordinary example-based testing — given input X, assert output Y, verifying the happy path + imagined edge cases) to "do the _invariants always hold_, across _all_ behaviors — including the concurrent, failure-laden, adversarial cases I _didn't_ think of?" (money testing). This matters because the near-zero correctness budget (Topic 1) means _any_ sequence that breaks an invariant (conservation, no-double-charge) is an _incident_ — so you must verify invariants _universally_, not just on chosen examples. The problem with example-based tests for money is that _the dangerous bugs are in the cases you didn't think of_ — a specific concurrency interleaving, a crash at a specific point, an unusual sequence — which example tests _miss_ (they only check what you imagined), and for money the unimagined case is a double-charge or lost money. So money testing needs techniques that _explore the space of behaviors_ (not just chosen examples) and _check the invariants_ across them — _property-based testing_ (generate many cases, check invariants), _simulation_ (explore concurrency/failure), _differential_ (compare to the real thing). The shift is from "assert specific outputs on specific inputs" (example) to "assert _invariants_ hold over _generated/explored_ behaviors" (property/simulation) — _test the properties, not just the examples_. This is the foundational reframe: for money, testing's job is to _try to break the invariants_ across the whole behavior space, because the unimagined invariant-breaking case is exactly the catastrophic money bug.**

## 1.2 Why this is harder for money

- **The behavior space is vast (concurrency, failures, sequences).** Money systems are concurrent (many transactions), failure-prone (networks, crashes), and stateful (long sequences) — the space of possible behaviors is enormous, and the bug is in a specific point in it. **The money behavior space is vast (concurrency × failures × sequences), so the correctness-breaking case is a needle in a haystack — example tests can't cover it; you need techniques that _search_ the space.**
- **The bugs are subtle and catastrophic.** A correctness bug (a race causing a double-charge, a crash leaving a broken invariant) is both _hard to find_ (a specific interleaving/timing) and _catastrophic_ (money loss). **Money correctness bugs are subtle (specific conditions) _and_ catastrophic (money loss) — the worst combination — demanding testing that actively hunts the subtle cases.**
- **The near-zero budget raises the bar.** Ordinary software tolerates some bugs (fix them later); money's near-zero correctness budget means a correctness bug reaching production is an incident. **The near-zero correctness budget (Topic 1) raises the testing bar: you must catch correctness bugs _before_ production (there's no budget to absorb them), demanding rigorous, invariant-focused, space-exploring testing.**

**The through-line: money testing verifies the _invariants hold across all behaviors_ (not just expected outputs on chosen examples), because the near-zero correctness budget makes any invariant-breaking sequence an incident, the dangerous bugs are in the unimagined (concurrent/failure/sequence) cases, and those bugs are subtle _and_ catastrophic — demanding techniques that _explore the behavior space and check the invariants_ (property-based, simulation, golden, differential) rather than example-based unit tests alone.**

---

# Part 2 — Property-based testing: generating cases that try to break the invariants

The primary technique: **property-based testing** — instead of asserting specific outputs, you assert _properties (invariants)_ that must hold for _all_ inputs, and the framework _generates many random inputs_ (and _shrinks_ failing ones to a minimal reproduction), actively trying to break the invariants.

## 2.1 What property-based testing is

```text
PROPERTY-BASED TESTING (assert INVARIANTS, generate cases that try to break them):
  instead of: "given input X, assert output Y" (example) → you write: "for ALL inputs, this PROPERTY
     (invariant) must hold" + the framework GENERATES many random inputs and CHECKS the property on each →
     actively SEARCHING for a case that BREAKS the invariant.
  SHRINKING — when a generated case FAILS, the framework SHRINKS it to the MINIMAL failing case (the smallest
     input that still breaks the property) → so you get a tiny, understandable reproduction (not a huge random
     case) → makes the found bug DEBUGGABLE.
  → THE PROPERTIES for money = the INVARIANTS (Topic 1 / the course):
     CONSERVATION — "for any sequence of operations, Σ signed entries == 0 per currency" (L2.3).
     NO DOUBLE-PROCESSING — "for any sequence (incl. retries/duplicates), each operation applies
        effectively-once" (L2.5).
     SUFFICIENT FUNDS — "no balance ever goes negative when it shouldn't / a payout never exceeds the balance"
        (L2.3).
     STATE VALIDITY — "no invalid state transition occurs; states only progress legally" (L2.17).
     BALANCE ACCURACY — "the materialized balance always equals the sum of entries" (L2.4).
  → the framework generates RANDOM SEQUENCES of operations (charges, refunds, captures, retries) and checks
     the invariant holds after each → if it finds a sequence that BREAKS an invariant → a correctness bug
     (shrunk to the minimal reproduction) → you've found the unimagined case.
  → this is EXACTLY what money testing needs: GENERATE the cases you didn't think of + CHECK the invariants →
     "try to break conservation / cause a double-charge, automatically, across thousands of generated sequences".
```

**Property-based testing is the primary money-testing technique: instead of "given input X, assert output Y" (example), you write "for _all_ inputs, this _property (invariant)_ must hold" and the framework _generates many random inputs_ and _checks the property on each_ — actively _searching for a case that breaks the invariant_ — with _shrinking_ (when a generated case fails, the framework shrinks it to the _minimal_ failing case — the smallest input that still breaks the property — giving a tiny, debuggable reproduction rather than a huge random case). For money, _the properties are the invariants_ (Topic 1 / the course): _conservation_ ("for any sequence of operations, Σ signed entries == 0 per currency"), _no double-processing_ ("for any sequence including retries/duplicates, each operation applies effectively-once"), _sufficient funds_ ("no balance goes negative when it shouldn't; a payout never exceeds the balance"), _state validity_ ("no invalid transition; states only progress legally"), and _balance accuracy_ ("the materialized balance always equals the sum of entries"). The framework _generates random sequences of operations_ (charges, refunds, captures, retries) and checks the invariant holds after each — if it finds a sequence that _breaks_ an invariant, that's a correctness bug (shrunk to the minimal reproduction) — _you've found the unimagined case_. This is _exactly_ what money testing needs: _generate the cases you didn't think of + check the invariants_ — "try to break conservation / cause a double-charge, automatically, across thousands of generated sequences." Property-based testing is the ideal money-testing technique because its structure (assert invariants, generate cases that try to break them) _matches_ the money-testing requirement (verify invariants across all behaviors) — and shrinking makes the found bugs debuggable.**

## 2.2 Why property-based testing fits money so well

```text
WHY PROPERTY-BASED TESTING FITS MONEY (the deep match):
  money has CLEAR, STRONG INVARIANTS (conservation, idempotency, sufficient funds, state validity — the course
     built them all) → PERFECT properties to assert (an invariant IS a property-based test's property).
  the DANGEROUS bugs are in UNIMAGINED SEQUENCES → property-based testing GENERATES sequences you didn't think
     of → it finds exactly the bugs example tests miss.
  the bugs are CATASTROPHIC → the near-zero budget demands finding them pre-production → property-based testing's
     thoroughness (thousands of generated cases) raises the confidence.
  SHRINKING → the found bug is a MINIMAL, debuggable reproduction → actionable.
  → so the course's INVARIANTS become property-based TESTS: every invariant the course ENFORCED (design) and
     OBSERVED (Topic 2, run-time) is now also TESTED (property-based, pre-production) → "enforce, observe, AND
     test" the invariants → three layers of correctness assurance.
  → STATEFUL property testing (model-based) — generate random sequences of STATEFUL operations (a model of the
     system), run them against the real system, check the invariants + that the real system matches a simple
     MODEL → catches stateful/sequence bugs (the FSM, the ledger over time) → the most powerful form for money.
```

**Property-based testing _fits money exceptionally well_ — a deep match: money has _clear, strong invariants_ (conservation, idempotency, sufficient funds, state validity — the course built them all), which are _perfect properties to assert_ (an invariant _is_ a property-based test's property); the _dangerous bugs are in unimagined sequences_, and property-based testing _generates sequences you didn't think of_ (finding exactly the bugs example tests miss); the bugs are _catastrophic_ and the near-zero budget demands finding them pre-production, which property-based testing's _thoroughness_ (thousands of generated cases) provides; and _shrinking_ gives a minimal, debuggable reproduction. So _the course's invariants become property-based tests_ — every invariant the course _enforced_ (design-time) and _observed_ (Topic 2, run-time) is now also _tested_ (property-based, pre-production) — "enforce, observe, _and_ test" the invariants: _three layers of correctness assurance_. The most powerful form is _stateful (model-based) property testing_ — generate random sequences of _stateful_ operations (a model of the system), run them against the real system, and check the invariants _plus_ that the real system matches a simple _model_ — catching stateful/sequence bugs (the FSM, the ledger over time), which are the hardest money bugs. This is the deepest payoff of having built the invariants: they're not just design properties and run-time observables; they're the _testable properties_ that property-based testing can hammer with thousands of generated sequences — and "enforce, observe, and test" is the full correctness-assurance stack.** This is a beautiful three-layer synthesis — **the invariants are enforced (in the code), observed (in production, Topic 2), and tested (pre-production, property-based) — triple-checked.**

---

# Part 3 — Deterministic simulation & replay: reproducing the hard scenarios

The second technique: **deterministic simulation** — running the system in a _controlled, reproducible_ environment where you can _inject_ concurrency interleavings, failures, and timing, and _replay_ them exactly — so the hard-to-reproduce bugs (races, crash-at-a-specific-point) become reproducible and testable.

## 3.1 What deterministic simulation is and why it's powerful

```text
DETERMINISTIC SIMULATION (controlled, reproducible exploration of concurrency/failure):
  the PROBLEM: the worst money bugs are in CONCURRENCY INTERLEAVINGS (a race) and FAILURE TIMINGS (a crash at
     a specific point) → these are NON-DETERMINISTIC in a normal environment (timing-dependent) → hard to
     reproduce, hard to test (a race that happens 1-in-a-million times).
  DETERMINISTIC SIMULATION: run the system in a SIMULATED environment where you CONTROL all the non-determinism
     — time, concurrency scheduling, I/O, failures → the execution is DETERMINISTIC (same seed → same run) →
     you can:
     - EXPLORE many interleavings/failure-timings (by varying the seed) → search the concurrency/failure space.
     - INJECT failures at EXACT points (crash right after the write, before the ack, mid-transaction) → test
        the failure-handling precisely.
     - REPRODUCE a bug EXACTLY (same seed → same execution) → a race that's 1-in-a-million in production is
        100% reproducible in simulation → DEBUGGABLE.
  → check the INVARIANTS after each simulated run (like property-based) → find the interleaving/failure-timing
     that BREAKS an invariant → the subtle concurrency/crash bugs example tests + even property-based tests on
     real timing can't reliably hit.
  → REPLAY — record a production (or test) execution and REPLAY it deterministically → reproduce a production
     bug exactly for debugging → "replay the exact sequence that caused the incident".
  → this is how you test the HARDEST money correctness properties: EFFECTIVELY-ONCE under crashes (L2.5 —
     inject a crash at every point in the operation, verify no double-processing), CONSERVATION under concurrent
     operations (L2.3 — explore interleavings, verify conservation), ATOMICITY under partial failure (L2.1).
```

**Deterministic simulation is the second technique — _controlled, reproducible exploration of concurrency and failure_. The problem it solves: the worst money bugs are in _concurrency interleavings_ (a race) and _failure timings_ (a crash at a specific point), which are _non-deterministic_ in a normal environment (timing-dependent, hard to reproduce — a race that happens 1-in-a-million times). _Deterministic simulation_ runs the system in a _simulated environment_ where you _control all the non-determinism_ (time, concurrency scheduling, I/O, failures), making the execution _deterministic_ (same seed → same run), so you can _explore many interleavings/failure-timings_ (by varying the seed — searching the concurrency/failure space), _inject failures at exact points_ (crash right after the write, before the ack, mid-transaction — testing failure-handling precisely), and _reproduce a bug exactly_ (same seed → same execution — a 1-in-a-million production race is 100% reproducible in simulation → debuggable). You _check the invariants after each simulated run_ (like property-based testing) to find the interleaving/failure-timing that _breaks_ an invariant — the subtle concurrency/crash bugs that example tests, and even property-based tests on real timing, can't reliably hit. _Replay_ complements it: record a production (or test) execution and _replay it deterministically_ to reproduce a production bug exactly for debugging ("replay the exact sequence that caused the incident"). This is how you test the _hardest_ money correctness properties: _effectively-once under crashes_ (L2.5 — inject a crash at _every_ point in the operation, verify no double-processing), _conservation under concurrent operations_ (L2.3 — explore interleavings, verify conservation), _atomicity under partial failure_ (L2.1). Deterministic simulation is the technique that makes the _non-deterministic_ (concurrency, crash-timing) bugs — the subtlest and most catastrophic money bugs — _reproducible and testable_, by controlling the non-determinism and injecting failures precisely.** This is powerful — **the hardest money bugs (races, crash-at-a-point) become 100% reproducible and systematically explorable under deterministic simulation.**

## 3.2 Combining simulation with property-based testing

```text
SIMULATION + PROPERTY-BASED (the powerful combination):
  PROPERTY-BASED generates random OPERATION SEQUENCES; DETERMINISTIC SIMULATION controls the CONCURRENCY/FAILURE
     execution → COMBINE them: generate random sequences (property) AND random interleavings/failure-timings
     (simulation) → explore BOTH the operation space AND the concurrency/failure space → check the invariants →
     the MOST THOROUGH correctness testing for money.
  → e.g. generate a random sequence of charges/refunds/retries (property) + run it under random concurrent
     interleavings with injected crashes at random points (simulation) + check conservation/no-double-charge
     hold → hammers the invariants across BOTH spaces → finds the deepest correctness bugs.
  → this is the state-of-the-art for testing correctness-critical systems (databases, consensus, payment
     ledgers): deterministic simulation + property-based invariant checking → "generate adversarial scenarios,
     run them deterministically, check the invariants, shrink the failures".
```

**Combining _simulation + property-based testing_ is the powerful state-of-the-art for money correctness: property-based testing generates random _operation sequences_ while deterministic simulation controls the _concurrency/failure execution_ — so _combined_, you generate random sequences (property) _and_ random interleavings/failure-timings (simulation), exploring _both_ the operation space _and_ the concurrency/failure space, checking the invariants throughout — the most thorough correctness testing for money. For example: generate a random sequence of charges/refunds/retries (property) + run it under random concurrent interleavings with injected crashes at random points (simulation) + check conservation/no-double-charge hold — hammering the invariants across _both_ spaces, finding the deepest correctness bugs. This is the state-of-the-art for testing correctness-critical systems (databases, consensus, payment ledgers): _deterministic simulation + property-based invariant checking_ — "generate adversarial scenarios, run them deterministically, check the invariants, shrink the failures." The combination is the apex of money correctness verification — it systematically explores the full behavior space (operations × concurrency × failures) and verifies the invariants hold everywhere, catching the subtle catastrophic bugs the near-zero budget can't tolerate.**

---

# Part 4 — Golden tests: pinning known-correct behavior

The third technique: **golden tests** (snapshot/characterization tests) — pin the _known-correct_ behavior/output so that any _change_ that alters it is caught. This protects against _regressions_ (a change unintentionally altering correct behavior).

```text
GOLDEN TESTS (pin known-correct behavior → catch regressions):
  record the KNOWN-CORRECT output/behavior of a scenario (the "golden" result) → on every change, re-run and
     COMPARE to the golden → any DIFFERENCE → a change altered the behavior → CATCH it (intended? → update the
     golden; unintended? → a regression bug).
  → for money: pin the exact LEDGER ENTRIES a known flow produces (a charge → these exact balanced entries),
     the exact FEE calculation, the exact STATE TRANSITIONS, the exact reconciliation output → any change that
     alters them is caught → protects the precise, correctness-critical behavior from accidental regression.
  → GOLDEN tests catch REGRESSIONS (a change breaking previously-correct behavior) — the complement to
     property-based (which catches NEW invariant violations) + simulation (concurrency/failure) → golden pins
     the SPECIFIC correct behavior; property asserts the GENERAL invariants.
  → especially important for money's PRECISE calculations (rounding, fees, FX conversion, interest) — where the
     exact value matters and a subtle change (a rounding tweak) could be a correctness regression → golden tests
     pin the exact values.
  → CAUTION: golden tests can become BRITTLE (every intended change requires updating goldens) → use them for
     STABLE, correctness-critical behavior (ledger entries, fee math), not for frequently-changing output.
```

**Golden tests (snapshot/characterization tests) are the third technique — _pin known-correct behavior to catch regressions_: you record the _known-correct_ output/behavior of a scenario (the "golden" result) and, on every change, re-run and _compare_ to the golden — any _difference_ means a change altered the behavior (intended? → update the golden; unintended? → a _regression bug_). For money, you pin the _exact ledger entries_ a known flow produces (a charge → these exact balanced entries), the _exact fee calculation_, the _exact state transitions_, the _exact reconciliation output_ — so any change that alters them is caught, protecting the precise, correctness-critical behavior from accidental regression. Golden tests catch _regressions_ (a change breaking previously-correct behavior) — the _complement_ to property-based testing (which catches _new_ invariant violations) and simulation (concurrency/failure): golden pins the _specific_ correct behavior, property asserts the _general_ invariants. They're especially important for money's _precise calculations_ (rounding, fees, FX conversion, interest — where the exact value matters and a subtle change like a rounding tweak could be a correctness regression) — golden tests pin the exact values. The caution: golden tests can become _brittle_ (every intended change requires updating goldens), so use them for _stable, correctness-critical_ behavior (ledger entries, fee math), not frequently-changing output. Golden tests complete the picture: property-based + simulation verify the _invariants_ (general correctness) across the behavior space, while golden tests pin the _specific_ correct behavior (precise calculations, exact entries) against regression — together covering both "the invariants always hold" and "this exact correct behavior didn't change."**

---

# Part 5 — Differential testing: comparing against the real provider

The fourth technique: **differential testing** — compare your system's behavior against a _reference_ (the real provider, or an independent implementation) to catch discrepancies, especially valuable for the _provider integration_ behavior (the gateway, Section 2) where the "correct" behavior is defined by the external provider.

```text
DIFFERENTIAL TESTING (compare against a reference — catch discrepancies):
  run the SAME scenario against YOUR system AND a REFERENCE (the real provider / an independent implementation /
     a simple model) → COMPARE the results → any DIFFERENCE → a discrepancy (your system vs the reference) →
     one of them is wrong (usually yours, if the reference is authoritative).
  → for money, the key use: COMPARE YOUR behavior to the REAL PROVIDER's (the gateway, Section 2):
     - does your normalization (provider status → your FSM state, Section 2) match what the provider ACTUALLY
        does? → test against the real provider (or its sandbox) → catch a mis-mapping.
     - does your fee/settlement calculation match the provider's? → compare → catch a discrepancy.
     - does your understanding of the provider's behavior (timing, finality, reversals) match reality? →
        differential test against the provider's sandbox → catch a wrong assumption.
  → this catches the GATEWAY correctness (Section 2): your system's MODEL of the provider vs the provider's
     ACTUAL behavior → a mismatch = a correctness bug (you'd process based on a wrong model) → differential
     testing against the real provider verifies your integration is CORRECT.
  → also: MODEL-BASED differential (property + differential) — compare the real system to a SIMPLE reference
     MODEL (an obviously-correct simple implementation of the ledger) → if they diverge, the real (complex)
     system has a bug the simple model reveals → "the complex optimized system must match the simple correct
     model".
  → and PROVIDER-CONTRACT testing — verify your integration against the provider's documented contract
     (their API behavior) → catch a drift (the provider changed; your model is stale — the Section 2 "unknown
     status" hazard).
```

**Differential testing is the fourth technique — _compare against a reference to catch discrepancies_: run the _same scenario_ against _your system_ and a _reference_ (the real provider, an independent implementation, or a simple model) and _compare_ the results — any _difference_ is a discrepancy where one is wrong (usually yours, if the reference is authoritative). For money, the key use is _comparing your behavior to the real provider's_ (the gateway, Section 2): does your _normalization_ (provider status → your FSM state) match what the provider _actually_ does? (test against the real provider/sandbox → catch a mis-mapping); does your _fee/settlement calculation_ match the provider's? (compare → catch a discrepancy); does your _understanding_ of the provider's behavior (timing, finality, reversals) match reality? (differential test against the sandbox → catch a wrong assumption). This catches _gateway correctness_ (Section 2): your system's _model_ of the provider vs the provider's _actual_ behavior — a mismatch is a correctness bug (you'd process based on a wrong model) — so differential testing against the real provider verifies your integration is _correct_. Two additional forms: _model-based differential_ (property + differential — compare the real system to a _simple reference model_, an obviously-correct simple ledger implementation; if they diverge, the complex system has a bug the simple model reveals — "the complex optimized system must match the simple correct model") and _provider-contract testing_ (verify your integration against the provider's documented contract — catch a _drift_ when the provider changes and your model goes stale — the Section 2 "unknown status" hazard). Differential testing verifies _correctness relative to an authority_ (the real provider or a simple model) — essential where "correct" is defined externally (provider integration) or where a complex optimized implementation should match a simple obviously-correct one.** This completes the testing toolkit — **differential testing catches the bugs where correctness is defined by an external reference (the provider) or a simpler model, which the other techniques can't (they test your invariants, not your match to reality).**

---

# Part 6 — The testing strategy: how the techniques combine, and testing in the pipeline

The techniques are _complementary_ — each catches a different class of bug — and together with the CI/CD pipeline (Section 6 Topic 4) they form the correctness-verification strategy that discharges the near-zero budget.

```text
THE MONEY-TESTING STRATEGY (complementary techniques + the pipeline):
  the TECHNIQUES, each catching a DIFFERENT class:
     EXAMPLE/UNIT tests — the happy path + known edge cases (fast, specific) → the baseline.
     PROPERTY-BASED — the INVARIANTS across GENERATED behaviors → catches unimagined invariant violations.
     DETERMINISTIC SIMULATION — CONCURRENCY/FAILURE interleavings → catches races, crash-at-a-point bugs.
     GOLDEN — REGRESSIONS of precise correct behavior → catches accidental changes to exact entries/calcs.
     DIFFERENTIAL — DISCREPANCY vs the real provider / a simple model → catches wrong integration/wrong model.
  → COMBINE: property + simulation (invariants across operation × concurrency/failure spaces) + golden (precise
     regressions) + differential (vs reality) + unit (happy path) → COMPREHENSIVE correctness coverage → each
     technique's blind spot covered by another.
  IN THE PIPELINE (Section 6 Topic 4's CI/CD + gates):
     - these tests are the CORRECTNESS GATE (Topic 1): a change can't ship if it breaks an invariant (property/
        simulation), regresses precise behavior (golden), or diverges from the provider (differential) → the
        near-zero correctness budget ENFORCED at the gate (you CANNOT merge a correctness-breaking change).
     - run FAST tests (unit, quick property) on every commit; DEEPER tests (extensive simulation, differential
        against the sandbox) on a schedule / pre-release → balance speed vs thoroughness.
  → this is how the near-zero CORRECTNESS BUDGET (Topic 1) is DISCHARGED: you VERIFY (comprehensively, invariant-
     focused, space-exploring) that no change breaks correctness BEFORE it ships → the testing is the mechanism
     that makes "move carefully on correctness-risk changes" (Topic 1) concrete.
  → and it feeds OBSERVABILITY (Topic 2): the invariants you TEST pre-production are the SAME invariants you
     OBSERVE in production → "enforce (design), test (pre-prod), observe (prod)" → the same invariants, three
     layers → comprehensive correctness assurance across the lifecycle.
```

**The money-testing strategy _combines complementary techniques_ (each catching a different bug class) with the CI/CD pipeline: _example/unit tests_ (the happy path + known edge cases — the fast baseline), _property-based_ (the invariants across generated behaviors — catches unimagined invariant violations), _deterministic simulation_ (concurrency/failure interleavings — catches races, crash-at-a-point bugs), _golden_ (regressions of precise correct behavior — catches accidental changes to exact entries/calcs), and _differential_ (discrepancy vs the real provider / a simple model — catches wrong integration/wrong model). _Combined_ — property + simulation (invariants across operation × concurrency/failure spaces) + golden (precise regressions) + differential (vs reality) + unit (happy path) — they give _comprehensive correctness coverage_, each technique's blind spot covered by another. _In the pipeline_ (Section 6 Topic 4's CI/CD + gates), these tests are the _correctness gate_ (Topic 1): a change _can't ship_ if it breaks an invariant (property/simulation), regresses precise behavior (golden), or diverges from the provider (differential) — _the near-zero correctness budget enforced at the gate_ (you _cannot_ merge a correctness-breaking change) — running fast tests (unit, quick property) on every commit and deeper tests (extensive simulation, differential against the sandbox) on a schedule/pre-release (balancing speed vs thoroughness). _This is how the near-zero correctness budget (Topic 1) is discharged_: you _verify comprehensively_ (invariant-focused, space-exploring) that no change breaks correctness _before it ships_ — the testing is the mechanism that makes "move carefully on correctness-risk changes" (Topic 1) concrete. And it _feeds observability_ (Topic 2): the invariants you _test_ pre-production are the _same_ invariants you _observe_ in production — "enforce (design), test (pre-prod), observe (prod)" — the same invariants, _three layers_, comprehensive correctness assurance across the lifecycle. The strategy is the full realization of the correctness-assurance stack: the invariants are _enforced_ in the design, _tested_ (comprehensively, before shipping, by complementary techniques gated in CI) to discharge the near-zero budget, and _observed_ in production — so correctness is verified at every stage of the lifecycle.**

---

# Part 7 — Failure modes, the mandatory questions, operations

Run the curriculum's questions against money testing:

- **What if a bug is in a case you didn't think of?** → Example tests miss it → property-based testing _generates_ the unimagined cases and checks the invariants; simulation explores concurrency/failure; the dangerous bug is found before production.
- **What if the bug is a race / crash-at-a-point (non-deterministic)?** → Hard to reproduce normally → deterministic simulation makes it 100% reproducible (control the non-determinism, inject failures precisely) and explorable.
- **What if a change regresses precise behavior (a rounding tweak)?** → Golden tests pin the exact values/entries and catch the change (intended → update; unintended → a regression bug).
- **What if your model of the provider is wrong?** → Differential testing against the real provider/sandbox catches the discrepancy (a mis-mapping, a wrong assumption).
- **What if a correctness-breaking change tries to ship?** → The correctness gate (property/simulation/golden/differential in CI) blocks it — the near-zero budget enforced; you can't merge a correctness-breaking change.
- **What's the source of truth for "is this change correct?"** → The invariants holding across the test suite (property + simulation) + no regression (golden) + matching the provider (differential) — comprehensive verification.
- **How do you reproduce a production correctness incident?** → Replay (deterministic) the exact execution; or reconstruct the sequence and run it in simulation.
- **Operational signals (testing-specific):** invariant-test coverage (are all the invariants property-tested?); simulation coverage (concurrency/failure scenarios explored); the correctness-gate pass/fail (changes blocked for correctness); escaped-correctness-bug rate (correctness bugs that reached production — should be ~0; any is a testing gap); differential-discrepancy findings (provider-model drift); golden-test stability. **Invariant-test coverage + the escaped-correctness-bug rate (correctness bugs reaching production ≈ 0) are the headline signals — well-tested money systems property-test all invariants, simulate concurrency/failure, gate changes on correctness, and let ~0 correctness bugs escape to production.**

---

# Part 8 — Common mistakes, trade-offs, interview Qs, exercises, mastery

## 8.1 Mistakes (each a real money-testing failure)

1. **Only example-based testing** (not property/simulation) → the unimagined correctness-breaking case ships. 2. **Not testing the invariants** (testing outputs, not conservation/idempotency) → invariant violations undetected. 3. **Not testing concurrency** (no simulation) → races (double-charges) reach production. 4. **Not testing crash/failure** (no failure injection) → crash-at-a-point bugs (broken invariants) ship. 5. **No golden tests for precise calculations** → a rounding/fee regression ships silently. 6. **Not differential-testing the provider** → a wrong provider-model (mis-mapping) causes correctness bugs. 7. **No correctness gate in CI** → a correctness-breaking change merges (the near-zero budget not enforced). 8. **Relying on production to find correctness bugs** → the near-zero budget violated (bugs reach prod). 9. **Testing only the happy path** → the edge/failure cases (where money bugs live) untested. 10. **Brittle golden tests** (over-using them) → constant updates, test fatigue. 11. **Not shrinking property failures** → huge un-debuggable reproductions. 12. **Not reproducing production incidents** (no replay/simulation) → can't debug or verify the fix. 13. **Not covering all invariants with property tests** → an untested invariant breaks. 14. **Treating money testing like ordinary testing** (not raising the bar for the near-zero budget) → insufficient rigor.

## 8.2 Trade-offs (reason, don't memorize)

- **Example vs property/simulation:** fast/specific but limited (example) vs thorough/space-exploring but slower (property/simulation). → Both — example for the baseline/happy path, property/simulation for the invariants across behaviors.
- **Test thoroughness vs speed:** more coverage + slower (deep simulation) vs faster + less (quick tests). → Fast tests on every commit, deep tests on a schedule/pre-release (balance in the pipeline).
- **Golden coverage vs brittleness:** pin precise behavior + maintenance (golden) vs flexible + less regression protection. → Golden for stable correctness-critical behavior (entries, fee math); not for volatile output.
- **Differential against real vs sandbox vs model:** authoritative but slow/costly (real) vs fast but maybe-divergent (sandbox) vs fast/simple (model). → Model for logic, sandbox for integration, real sparingly.
- **Gate strictness vs velocity:** block all correctness risk + slower (strict) vs faster + more risk (lax). → Strict on correctness (near-zero budget — Topic 1); tune the gate for correctness, not velocity.
- **Simulation determinism vs realism:** reproducible/controlled (deterministic sim) vs realistic but non-reproducible (real environment). → Deterministic sim for correctness testing (reproducibility); real environment for other concerns.

## 8.3 Interview questions you should answer cold

1. How does money testing differ from ordinary testing (the two questions)? 2. Why do example-based tests miss the dangerous money bugs? 3. What's property-based testing, and why does it fit money so well? 4. What's shrinking, and why does it matter? 5. What are the money properties/invariants to property-test? 6. What's deterministic simulation, and what bugs does it catch that property-based alone can't? 7. How do simulation + property-based combine? 8. What are golden tests, and what do they catch (vs property-based)? 9. What are differential tests, and why are they key for provider integration? 10. What's model-based differential testing? 11. How do the techniques combine into a comprehensive strategy? 12. How does testing enforce the near-zero correctness budget (the correctness gate)? 13. How does "enforce, test, observe" form three layers of correctness assurance? 14. How do you reproduce a production correctness incident (replay/simulation)?

## 8.4 Hands-on exercises (for when we implement)

1. **Property-based invariant tests:** write property tests asserting conservation (Σ signed == 0), no-double-charge (effectively-once under retries/duplicates), sufficient-funds (no improper negative), and state-validity (no invalid transition) over _generated random sequences_ of operations against the ledger/payments packages; show it finds an injected bug (and shrinks it). 2. **Stateful/model-based property test:** generate random stateful operation sequences, run against the real system + a simple model, assert they match + the invariants hold. 3. **Deterministic simulation:** run operations under controlled concurrency scheduling + injected crashes at each point; verify effectively-once (no double-charge) under every crash point and conservation under every interleaving; reproduce a found bug exactly (same seed). 4. **Combine property + simulation:** generate random sequences + random interleavings/failure-timings; check the invariants across both spaces. 5. **Golden tests:** pin the exact ledger entries / fee calculation / state transitions of known flows; show a change altering them is caught. 6. **Differential test:** compare your provider-normalization (status → FSM state) against a mock "real provider"; catch a mis-mapping; compare the complex ledger to a simple reference model. 7. **Correctness gate:** a CI gate that runs the property/simulation/golden/differential tests and blocks a correctness-breaking change. 8. **Replay:** record an execution and replay it deterministically to reproduce a bug.

## 8.5 Mastery checklist (before "chaos engineering / fault injection for payments")

- [ ] I understand money testing's shift from "**does it work on chosen examples?**" to "**do the invariants hold across ALL behaviors** (concurrent/failure/sequence — including the unimagined)?" — because the near-zero correctness budget (Topic 1) makes any invariant-breaking sequence an incident.
- [ ] I can apply **property-based testing** (assert the **invariants** as properties; generate many cases that **try to break** them; **shrink** failures to minimal reproductions) and know **why it fits money** (clear invariants, unimagined-sequence bugs, catastrophic bugs, debuggable shrinks) — including **stateful/model-based** property testing.
- [ ] I can use **deterministic simulation** (control non-determinism — time/scheduling/I-O/failures; **explore interleavings**, **inject failures at exact points**, **reproduce bugs exactly**) to catch the **race / crash-at-a-point** bugs, and **combine it with property-based** (operation × concurrency/failure spaces) — the state-of-the-art.
- [ ] I can use **golden tests** (pin **precise correct behavior** — exact entries, fee math, transitions — to catch **regressions**, the complement to property's general invariants) and know their **brittleness** caution (stable behavior only).
- [ ] I can use **differential testing** (compare against the **real provider**/sandbox — catch provider-model discrepancies/mis-mappings — and against a **simple reference model** — the complex system must match the simple correct one), key for **gateway/integration** correctness (Section 2).
- [ ] I understand the **complementary strategy** (unit + property + simulation + golden + differential, each covering another's blind spot) and that it's **gated in CI** as the **correctness gate** that **enforces the near-zero budget** (can't ship a correctness-breaking change) — discharging Topic 1's "move carefully on correctness-risk changes."
- [ ] I understand testing forms the **three-layer correctness-assurance stack** with the course's work: the invariants are **enforced** (design), **tested** (pre-production, these techniques), and **observed** (production, Topic 2) — the same invariants, three layers.
- [ ] I can name the operational signals (**invariant-test coverage**, simulation coverage, correctness-gate pass/fail, **escaped-correctness-bug rate ≈ 0**, differential discrepancies) of a well-tested money system.

---

## One-paragraph synthesis

Testing money systems is the correctness-verification discipline that discharges the near-zero correctness error budget of Topic 1, and it rests on a fundamental shift: where **ordinary testing asks "does the code do what I _expect_, on the _cases I thought of_?"** (example-based unit tests verifying the happy path and imagined edge cases), **money testing must ask "do the _invariants always hold_, across _all_ behaviors — including the concurrent, failure-laden, adversarial cases I _didn't_ think of?"** — because the near-zero budget makes _any_ sequence that breaks an invariant (conservation, no-double-charge) an _incident_, and the dangerous money bugs live precisely in the _unimagined_ cases (a specific concurrency interleaving, a crash at a specific point, an unusual sequence) that example tests, by construction, miss — bugs that are both _subtle_ (specific conditions) and _catastrophic_ (money loss). So money testing uses techniques that _explore the behavior space and check the invariants_ rather than asserting outputs on chosen inputs. The primary technique is **property-based testing** — instead of "given X, assert Y," you assert that a _property (invariant)_ holds "for _all_ inputs" and the framework _generates thousands of random cases actively trying to break it_, _shrinking_ any failure to a minimal debuggable reproduction — which fits money _exceptionally_ well because the course's **invariants are perfect properties** (conservation = "Σ signed entries == 0 for any sequence," effectively-once = "each operation applies once despite retries/duplicates," sufficient-funds, state-validity, balance-accuracy), and its _stateful/model-based_ form (generate random stateful sequences, run against the real system and a simple model, check invariants + that they match) catches the hardest sequence/FSM bugs — so the invariants the course _enforced_ (design) and _observed_ (production, Topic 2) are now also _tested_ (pre-production), giving a three-layer "enforce, test, observe" correctness-assurance stack. The second technique, **deterministic simulation**, makes the subtlest and most catastrophic bugs — _races_ and _crash-at-a-specific-point_ failures, which are non-deterministic and nearly impossible to reproduce normally — _100% reproducible and systematically explorable_ by _controlling all the non-determinism_ (time, concurrency scheduling, I/O, failures) so that the same seed yields the same run, letting you _explore many interleavings/failure-timings_, _inject crashes at exact points_ (right after the write, before the ack, mid-transaction, to verify effectively-once under every crash point and conservation under every interleaving), and _reproduce a 1-in-a-million production race deterministically for debugging_ — and _combined with property-based testing_ (random operation sequences × random interleavings/failure-timings, checking the invariants throughout) it is the state-of-the-art for correctness-critical systems. The third technique, **golden tests**, _pins the precise known-correct behavior_ (the exact ledger entries a flow produces, the exact fee/FX/rounding calculation, the exact state transitions) so that any change _altering_ it is caught as a potential _regression_ — the complement to property-based testing (golden pins the _specific_ correct behavior; property asserts the _general_ invariants), especially vital for money's precise calculations where a subtle rounding tweak is a correctness regression. The fourth, **differential testing**, _compares your behavior against a reference_ — the _real provider_ (or its sandbox, or its documented contract) to verify that your _model_ of the provider (status→FSM-state normalization, fee/settlement calculation, timing/finality/reversal assumptions — the gateway, Section 2) matches the provider's _actual_ behavior (a mismatch is a correctness bug, since you'd process on a wrong model), and a _simple reference model_ (the complex optimized ledger must match an obviously-correct simple implementation) — catching the bugs where "correct" is defined externally or where complexity hides errors a simple model reveals. These techniques are _complementary_ — unit (happy path) + property (invariants across generated behaviors) + simulation (concurrency/failure) + golden (precise regressions) + differential (vs reality) — each covering another's blind spot for _comprehensive_ coverage, and they are _gated in the CI/CD pipeline_ (Section 6 Topic 4) as the **correctness gate** that _enforces the near-zero budget_: a change _cannot ship_ if it breaks an invariant (property/simulation), regresses precise behavior (golden), or diverges from the provider (differential), with fast tests on every commit and deep simulation/differential runs pre-release — which is precisely how Topic 1's "move carefully on correctness-risk changes" becomes concrete, and how the discipline feeds back to observability (the same invariants tested pre-production are observed in production) so that correctness is enforced in the design, verified comprehensively before shipping, and watched continuously in production — the full-lifecycle assurance that a money system, whose near-zero correctness budget tolerates no breaches, is _proven_ correct against the vast space of concurrent, failure-laden, adversarial behaviors where a single unimagined invariant violation would otherwise become a catastrophic, compounding, unrecoverable money bug.

When you've reviewed, say **continue** and we'll cover the next topic — **chaos engineering / fault injection for payments** — the _resilience_-verification counterpart to this topic's _correctness_ verification: deliberately injecting failures into production-like (or production) systems to verify the graceful-degradation, failover, and recovery designs (Topics 3, and the upcoming DR/multi-region) actually work; game days; and — critically for money — the blast-radius and safety discipline for chaos-testing _without losing real money_ (how you inject faults into a money system safely, verify correctness held under the injected failure, and build confidence that the system fails as designed).
