We begin **L3 Section 7 — Reliability, operability & evolution of money systems**, first topic: **Reliability for money systems: SLOs, error budgets & correctness vs availability**. This section is the operational and temporal capstone of L3 — how money systems stay reliable, operable, and evolvable for years. And it opens with a reframe that governs everything: **reliability for a money system is not the same as reliability for ordinary software.** Ordinary reliability is about _uptime_ (is it up? is it fast?). Money reliability is about _correctness_ (is the money _right_?) — and the two are _different dimensions_, with a crucial asymmetry: **a money system that is _up but wrong_ is worse than one that is _down_.** Getting this distinction right reshapes how you set reliability targets (SLOs), how you budget for failure (error budgets), and how you decide what to trade off under pressure. Definitive treatment, labeled parts, building on the conservation invariant (L2.3), idempotency (L2.5), reconciliation (L2-recon), and the whole correctness foundation the course built.

---

# Part 1 — First principles: what "reliability" means for a money system

## 1.1 The core distinction: correctness is a separate (and higher) reliability dimension

The foundational reframe — the thing that makes money-system reliability different in kind:

```text
CORRECTNESS vs AVAILABILITY (the two reliability dimensions, and their asymmetry):
  AVAILABILITY — is the system UP and RESPONDING? (and fast enough?) → the classic reliability dimension
     → measured by uptime, latency, error rate → "can users use it?"
  CORRECTNESS — is the system producing the RIGHT ANSWER? for money: is the MONEY RIGHT? (conservation holds,
     no double-charge, balances accurate, no money lost/created) → a DISTINCT dimension → "is it right?"
  → these are DIFFERENT: a system can be 100% AVAILABLE and WRONG (up, fast, but double-charging / losing
     money / corrupting balances) → AVAILABLE ≠ CORRECT.
  → THE ASYMMETRY (the key insight): for MONEY, a WRONG answer is WORSE than NO answer:
     - a payment that DOESN'T happen (unavailable) → the customer retries, is annoyed → RECOVERABLE.
     - a payment that happens WRONG (double-charged, money lost, wrong balance) → real financial harm, a
       correctness breach, lost trust, possibly unrecoverable, a compliance/legal issue → WORSE.
  → so for money systems, CORRECTNESS is the HIGHER reliability dimension → you'd rather be DOWN (unavailable
     but correct) than UP-AND-WRONG (available but incorrect) → "fail CLOSED on correctness."
  → this INVERTS the ordinary-software instinct (maximize availability) → for money, CORRECTNESS comes FIRST,
     availability second → the defining reliability principle of money systems.
```

**The foundational distinction is that *correctness* and *availability* are *two different reliability dimensions*: availability is "is the system up and responding (and fast)?" while correctness is "is it producing the *right answer* — for money, *is the money right*?" (conservation holds, no double-charge, accurate balances, no money lost/created). These are different — a system can be 100% *available* and *wrong* (up, fast, but double-charging or corrupting balances), so *available ≠ correct*. The key insight is the *asymmetry*: for money, *a wrong answer is worse than no answer* — a payment that *doesn't happen* (unavailable) is recoverable (the customer retries, annoyed), but a payment that happens *wrong* (double-charged, money lost, wrong balance) is real financial harm, a correctness breach, lost trust, possibly unrecoverable, and a compliance issue. So for money systems, *correctness is the higher reliability dimension* — you'd rather be *down (unavailable but correct)* than *up-and-wrong (available but incorrect)* — which *inverts the ordinary-software instinct* (maximize availability): **for money, correctness comes first, availability second.** This is the defining reliability principle of money systems, and it reshapes everything downstream (SLOs, error budgets, degradation, failover) — because the usual "keep it up at all costs" is _wrong_ for money; the right instinct is "keep it _correct_ at all costs, available where possible."** This is the pivotal reframe of the entire section — **money systems optimize a different objective than most software: correctness over availability.**

## 1.2 Why this asymmetry holds (the "why")

- **Money errors are often irreversible or costly to reverse.** A double-charge requires a refund (cost, effort, trust damage); money lost may be unrecoverable; a wrong balance that propagates corrupts downstream decisions. **Unlike a wrong search result (refresh and it's fine), a money error has _lasting consequences_ — it moved (or failed to move) real value — so it's far costlier than a transient unavailability.**
- **Money errors compound and spread.** A corrupted balance feeds wrong decisions (a wrong payout, a wrong credit limit, a wrong reconciliation); a double-charge that isn't caught becomes a chargeback (Section 5). **Money errors _propagate_ through the system (the ledger feeds everything), so a correctness breach isn't contained — it spreads — making it far worse than a localized outage.**
- **Money correctness is a trust and compliance foundation.** Customers trust you with their money; regulators require accurate books (safeguarding, Section 3; audit, Section 6). A correctness breach violates both. **Money correctness is the foundation of trust and compliance — breaching it is existential in a way an outage isn't.**

**The through-line: money-system reliability is defined by _correctness_ (is the money right?), a distinct and _higher_ dimension than _availability_ (is it up?), because for money a _wrong_ answer is worse than _no_ answer — money errors are irreversible/costly, they propagate, and they breach trust/compliance — so money systems invert the ordinary instinct: _correctness first, availability second_. This reframe governs the whole section.**

---

# Part 2 — SLOs, SLIs, and error budgets (the reliability framework)

To _manage_ reliability, you need a framework to _measure and target_ it. The SRE framework — SLIs, SLOs, error budgets — is the standard, and we adapt it to money's correctness dimension.

## 2.1 The framework (SLI, SLO, error budget)

```text
THE RELIABILITY FRAMEWORK (SLI → SLO → error budget):
  SLI (Service Level Indicator) — a MEASURED metric of reliability: e.g. "% of payments that succeed", "p99
     latency", "% of transactions that reconcile correctly" → WHAT you measure.
  SLO (Service Level Objective) — a TARGET for an SLI: e.g. "99.95% of payments succeed", "100% of
     transactions reconcile" → the GOAL you commit to → defines "reliable enough".
  ERROR BUDGET — the ALLOWED amount of unreliability = (1 − SLO): e.g. a 99.95% availability SLO → a 0.05%
     error budget (you're ALLOWED to fail 0.05% of the time) → the "budget" of failure you can SPEND before
     you've violated the SLO.
  → the ERROR BUDGET is the KEY concept: it QUANTIFIES acceptable unreliability → and it GOVERNS the pace of
     change (Part 4): if you have budget left, you can ship risky changes; if you've spent it (too many
     failures), you FREEZE changes and focus on reliability → the error budget BALANCES velocity vs reliability.
  → (SLA = Service Level AGREEMENT — a CONTRACTUAL promise to customers, with penalties → the external,
     contractual version of an SLO.)
```

**The reliability framework is _SLI → SLO → error budget_: an _SLI (Service Level Indicator)_ is a measured reliability metric ("% of payments that succeed", "% that reconcile correctly" — _what_ you measure), an _SLO (Service Level Objective)_ is a _target_ for an SLI ("99.95% of payments succeed", "100% reconcile" — the _goal_, defining "reliable enough"), and an _error budget_ is the _allowed_ unreliability = (1 − SLO) (a 99.95% SLO → a 0.05% error budget — you're _allowed_ to fail 0.05% of the time). The error budget is the key concept: it _quantifies acceptable unreliability_ and _governs the pace of change_ (Part 4 — budget left → ship risky changes; budget spent → freeze and focus on reliability — balancing velocity vs reliability). (An _SLA — Service Level Agreement_ — is the _contractual_ version of an SLO, with penalties.) The framework turns reliability from a vague aspiration into a _measured, targeted, budgeted_ quantity — and the error budget is the mechanism that balances the competing pressures of shipping features (velocity) and staying reliable.**

## 2.2 The crucial adaptation: separate SLOs for correctness and availability

```text
SEPARATE SLOs FOR CORRECTNESS vs AVAILABILITY (the money adaptation):
  ordinary systems: SLOs on AVAILABILITY (uptime) + latency → the classic SLIs.
  MONEY systems: you need SLOs on BOTH dimensions, with CORRECTNESS held to a HIGHER standard:
     AVAILABILITY SLOs — "99.95% of payments succeed", "p99 latency < 500ms" → like ordinary systems (an
        error budget you CAN spend — some unavailability is acceptable).
     CORRECTNESS SLOs — "100% of transactions reconcile", "0 double-charges", "conservation holds always",
        "0 money lost/created" → held to a MUCH higher (often ZERO-error) standard → the error budget for
        CORRECTNESS is NEAR ZERO (you can't "spend" a budget of double-charges — any is a breach).
  → the ASYMMETRY (Part 1) in the SLOs: AVAILABILITY has a real error budget (some failure acceptable);
     CORRECTNESS has a NEAR-ZERO budget (correctness breaches are NOT acceptable — a double-charge isn't
     "within budget", it's an incident).
  → so a money system has a RELAXED availability SLO (some downtime OK) + a STRICT correctness SLO (near-zero
     correctness errors) → reflecting "correctness first, availability second" (Part 1) in the targets.
  → the CORRECTNESS SLIs are the INVARIANTS the course built: conservation (L2.3), effectively-once/no-double-
     charge (L2.5), balance accuracy, reconciliation completeness (L2-recon) → you MEASURE these as correctness
     SLIs → the invariants become MONITORED reliability targets (Topic 2).
```

**The crucial money adaptation is *separate SLOs for correctness and availability, with correctness held to a much higher standard*: ordinary systems have SLOs on availability + latency, but money systems need *both* dimensions — *availability SLOs* ("99.95% of payments succeed", "p99 < 500ms" — like ordinary systems, with a real error budget you *can* spend, since some unavailability is acceptable) *and* *correctness SLOs* ("100% reconcile", "0 double-charges", "conservation holds always", "0 money lost/created" — held to a *much higher, often zero-error* standard, so the correctness error budget is *near zero* — you can't "spend" a budget of double-charges; any is a breach). The asymmetry (Part 1) shows up *in the SLOs*: availability has a *real error budget* (some failure acceptable) while correctness has a *near-zero budget* (a double-charge isn't "within budget" — it's an *incident*). So a money system has a *relaxed availability SLO* (some downtime OK) + a *strict correctness SLO* (near-zero correctness errors), reflecting "correctness first, availability second" in the targets. Crucially, *the correctness SLIs are the invariants the course built* — conservation (L2.3), effectively-once/no-double-charge (L2.5), balance accuracy, reconciliation completeness (L2-recon) — which you now *measure* as correctness SLIs, so the invariants become *monitored reliability targets* (bridging to Topic 2's observability). This is the key engineering move: **the course's correctness invariants become the correctness SLIs/SLOs — the things you measure and hold to a near-zero error budget — making reliability for money a matter of continuously verifying the invariants.\*\*

---

# Part 3 — Defining correctness SLOs: what "the money is right" means, measurably

To hold correctness to a near-zero error budget, you must _define_ correctness _measurably_ — turn "the money is right" into concrete, monitorable SLIs. This operationalizes the invariants.

```text
CORRECTNESS SLIs (making "the money is right" MEASURABLE — the invariants as metrics):
  CONSERVATION (L2.3) — "Σ signed ledger entries == 0 per currency, always" → measure: the conservation
     residual (should be 0) → a nonzero residual = money created/destroyed = a correctness breach.
  NO DOUBLE-PROCESSING (L2.5) — "every operation applied effectively-once" → measure: the duplicate/double-
     charge rate (should be 0) → any double-charge = a breach.
  BALANCE ACCURACY (L2.4) — "materialized balances match the entries" → measure: balance drift (materialized
     vs recomputed; should be 0) → drift = a correctness problem.
  RECONCILIATION COMPLETENESS (L2-recon) — "internal ledger reconciles to external (bank/processor)" →
     measure: the reconciliation gap / unmatched-and-unexplained amount (should be 0) + reconciliation
     timeliness → a gap = money unaccounted-for.
  SOLVENCY (Section 3) — "held == owed (the platform conservation invariant)" → measure: the solvency residual
     (should be 0) → a shortfall = insolvency.
  SETTLEMENT CORRECTNESS — "money settled matches what was captured" → measure: settlement discrepancies.
  STATE-MACHINE VALIDITY (L2.17) — "no invalid state transitions" → measure: invalid-transition attempts.
  → EACH correctness invariant → a measurable SLI (usually "the residual/gap/rate is 0") → held to a near-zero
     error budget → CONTINUOUSLY MONITORED (Topic 2) → the moment a correctness SLI goes nonzero, it's an
     INCIDENT (Topic 10), not "within budget".
  → this is the OPERATIONALIZATION of the course's invariants: every invariant the course built as a
     CORRECTNESS property is now a MEASURED, TARGETED, MONITORED reliability SLI → correctness becomes
     OBSERVABLE and ENFORCED as a reliability target.
```

**Defining correctness SLOs means making "the money is right" _measurable_ — turning the course's invariants into concrete monitorable SLIs: _conservation_ (L2.3 → the conservation residual should be 0; nonzero = money created/destroyed), _no double-processing_ (L2.5 → the duplicate/double-charge rate should be 0), _balance accuracy_ (L2.4 → balance drift, materialized vs recomputed, should be 0), _reconciliation completeness_ (L2-recon → the unmatched-and-unexplained gap should be 0, plus timeliness), _solvency_ (Section 3 → held == owed, the solvency residual should be 0), _settlement correctness_, and _state-machine validity_ (L2.17 → no invalid transitions). Each invariant becomes a measurable SLI (usually "the residual/gap/rate is 0"), held to a _near-zero error budget_ and _continuously monitored_ — so the _moment a correctness SLI goes nonzero, it's an incident_ (Topic 10), not "within budget." This is the _operationalization of the course's invariants_: every invariant built as a _correctness property_ is now a _measured, targeted, monitored reliability SLI_ — correctness becomes _observable and enforced_ as a reliability target. This is the deep payoff of having built all those invariants: they're not just design properties; they're the _correctness SLIs_ that define and enforce money-system reliability — and Topic 2 (observability) is about _watching them continuously_.** This is the unifying thread — **the entire course's correctness work becomes the measurable reliability targets of a money system.**

---

# Part 4 — The error budget as the governor of change (velocity vs reliability)

The error budget isn't just a measurement — it's a _decision tool_ that governs _how fast you change the system_, balancing the competing pressures of shipping (velocity) and staying reliable. And for money, this interacts with the correctness/availability asymmetry.

## 4.1 How the error budget governs change

```text
THE ERROR BUDGET GOVERNS THE PACE OF CHANGE (velocity vs reliability):
  the tension: CHANGE (new features, migrations, deploys) is the #1 source of incidents (most outages are
     caused by changes) → but you MUST change (ship features, evolve — the whole section) → how FAST?
  the ERROR-BUDGET POLICY: use the error budget to DECIDE:
     - BUDGET REMAINING (you're meeting the SLO comfortably) → you can AFFORD risk → ship changes faster,
       take calculated risks (the budget absorbs the occasional failure).
     - BUDGET SPENT/EXHAUSTED (too many failures, SLO at risk) → FREEZE risky changes, focus on reliability
       (stop spending the budget) until you recover.
  → this BALANCES velocity (ship features) vs reliability (stay up) OBJECTIVELY (by the budget, not by argument)
     → the error budget is the SHARED, DATA-DRIVEN arbiter between "ship faster" (product) and "stay reliable"
       (ops) → it aligns incentives (both want to stay within budget).
  → it makes reliability a FEATURE with a BUDGET, not an absolute → "100% reliable" is neither achievable nor
     the goal; MEETING THE SLO (spending the budget wisely) is → reliability is ENGINEERED to a target, not
     maximized.
```

**The error budget _governs the pace of change_ — balancing velocity vs reliability: the tension is that _change_ (features, migrations, deploys) is the #1 source of incidents (most outages are change-caused) but you _must_ change (the whole section is about evolution), so _how fast?_ The _error-budget policy_ decides: _budget remaining_ (meeting the SLO comfortably) → you can _afford risk_ → ship faster, take calculated risks (the budget absorbs occasional failure); _budget spent/exhausted_ (too many failures, SLO at risk) → _freeze_ risky changes and focus on reliability until you recover. This balances velocity vs reliability _objectively_ (by the budget, not by argument) — the error budget is the _shared, data-driven arbiter_ between "ship faster" (product) and "stay reliable" (ops), aligning incentives (both want to stay within budget). It makes reliability a _feature with a budget_, not an absolute — "100% reliable" is neither achievable nor the goal; _meeting the SLO_ (spending the budget wisely) is — reliability is _engineered to a target, not maximized_. The error budget is the governance mechanism that turns the velocity-vs-reliability conflict into a data-driven policy — and it connects to the gated-rollout discipline (Section 2 migration, Section 5 fraud policy): you _spend_ error budget deliberately on changes, rolled out gradually, rolling back if the budget drains too fast.**

## 4.2 The money twist: the correctness budget doesn't flex

```text
THE MONEY TWIST — THE CORRECTNESS BUDGET DOESN'T FLEX (the asymmetry in the policy):
  for AVAILABILITY, the error budget flexes (Part 4.1): budget left → ship; budget spent → freeze → a normal
     velocity/reliability balance.
  for CORRECTNESS, the budget is NEAR-ZERO and DOESN'T flex the same way: you can't "spend" a budget of money
     errors → a correctness breach is an INCIDENT, not a budgeted cost → so you CAN'T trade correctness for
     velocity (you can't ship a change that risks double-charging because "we have budget").
  → so the error-budget POLICY for money is ASYMMETRIC:
     - AVAILABILITY budget → governs velocity normally (ship faster when you have availability budget).
     - CORRECTNESS budget → near-zero, non-negotiable → ANY correctness-risking change gets EXTREME scrutiny
       (testing — Topic 4, gradual rollout, reconciliation verification) → you NEVER knowingly spend
       correctness budget for velocity.
  → this means CHANGES to a money system are gated MORE on CORRECTNESS risk than availability risk → a change
     that might cause a brief outage (availability) is less scary than one that might corrupt the ledger
     (correctness) → the gating/testing/rollout rigor is proportional to the CORRECTNESS risk.
  → "move fast" is OK for availability-risk changes (you have budget); "move carefully" for correctness-risk
     changes (near-zero budget) → the pace of change is correctness-risk-weighted.
```

**The money twist is that _the correctness budget doesn't flex_ — the asymmetry shows up in the error-budget _policy_: for _availability_, the budget flexes normally (budget left → ship; budget spent → freeze — a normal velocity/reliability balance), but for _correctness_, the budget is _near-zero and non-negotiable_ (you can't "spend" a budget of money errors — a correctness breach is an _incident_, not a budgeted cost — so you _can't trade correctness for velocity_; you can't ship a change that risks double-charging because "we have budget"). So the error-budget policy for money is _asymmetric_: the _availability budget_ governs velocity normally (ship faster when you have availability budget), while the _correctness budget_ (near-zero, non-negotiable) means _any correctness-risking change gets extreme scrutiny_ (property testing — Topic 4, gradual rollout, reconciliation verification) — you _never knowingly spend correctness budget for velocity_. This means _changes to a money system are gated more on correctness risk than availability risk_ — a change that might cause a brief outage is less scary than one that might corrupt the ledger — so the gating/testing/rollout rigor is _proportional to the correctness risk_: "move fast" is fine for availability-risk changes (you have budget), "move carefully" for correctness-risk changes (near-zero budget). The pace of change is _correctness-risk-weighted_ — which is why money-system changes are so heavily tested and gradually rolled out, and why the testing (Topic 4) and chaos (Topic 5) disciplines matter so much: they're how you verify a change doesn't spend the non-negotiable correctness budget.**

---

# Part 5 — How this reframe governs the rest of the section

The correctness-over-availability reframe is the lens for the entire section — it determines the _answer_ to each subsequent topic's central question.

```text
CORRECTNESS-FIRST GOVERNS THE WHOLE SECTION (the lens for each topic):
  OBSERVABILITY (Topic 2) — monitor CORRECTNESS (the invariant SLIs), not just availability → "is the money
     right?" is the primary question.
  GRACEFUL DEGRADATION (Topic 3) — under failure, preserve CORRECTNESS even at the cost of AVAILABILITY →
     fail-CLOSED on correctness (stop rather than process wrong) → the inverse of ordinary degradation.
  TESTING (Topic 4) — test the CORRECTNESS invariants (property-based) because the correctness budget is
     near-zero → verify no change breaks an invariant.
  CHAOS (Topic 5) — verify resilience WITHOUT losing real money (correctness-safe chaos) → test that failures
     don't breach correctness.
  MIGRATIONS (Topic 6) — evolve the data model WITHOUT corrupting money (correctness during change) → the
     correctness budget forbids a migration that loses/duplicates money.
  MULTI-REGION (Topic 7) — consistency (correctness) over availability across regions → you can't double-spend
     across regions (correctness) even if it costs availability.
  DR (Topic 8) — recover WITHOUT losing/duplicating money (financial consistency) over mere availability → DR
     is gated on CORRECTNESS (don't restore a state that double-processes).
  CAPACITY/PEAK (Topic 9) — handle load WITHOUT breaking correctness → shed load (availability) rather than
     corrupt (correctness).
  INCIDENTS (Topic 10) — detect and fix CORRECTNESS breaches (money loss) + prove the books are right (recon).
  OPERABILITY (Topic 11) — operate/evolve for decades WITHOUT ever breaking correctness → the ledger is
     forever and must stay correct.
  → EVERY topic answers its question with "CORRECTNESS FIRST": the recurring resolution is "preserve
     correctness, even at the cost of availability" → this topic sets that lens.
```

**The correctness-first reframe _governs the whole section_ — it's the lens that determines each subsequent topic's answer: _observability_ monitors correctness (the invariant SLIs), not just availability; _graceful degradation_ preserves correctness even at the cost of availability (fail-_closed_ on correctness — the inverse of ordinary degradation); _testing_ verifies the correctness invariants (near-zero budget); _chaos_ verifies resilience without losing real money; _migrations_ evolve the data model without corrupting money; _multi-region_ chooses consistency (correctness) over availability (no cross-region double-spend); _DR_ recovers without losing/duplicating money (financial consistency over mere availability); _capacity/peak_ sheds load rather than corrupts; _incidents_ detect and fix correctness breaches and prove the books right; and _operability_ evolves for decades without ever breaking correctness. _Every topic answers its central question with "correctness first"_ — the recurring resolution throughout the section is "preserve correctness, even at the cost of availability." This topic sets that lens, and the rest of the section applies it to each operational challenge — which is why this reframe is the foundational first topic: it's the principle from which every subsequent answer follows.**

---

# Part 6 — Failure modes, the mandatory questions, operations

Run the curriculum's questions against money-system reliability:

- **What if the system is up but wrong (available but incorrect)?** → _Worse_ than down — a correctness breach (double-charge, money lost) — the defining money-reliability failure. Correctness is the higher dimension; you'd rather be down than up-and-wrong.
- **What if you spend the correctness budget for velocity?** → You can't — the correctness budget is near-zero/non-negotiable; a correctness breach is an incident, not a budgeted cost. Gate correctness-risking changes with extreme scrutiny.
- **What if you've exhausted the availability error budget?** → Freeze risky changes, focus on reliability (the error-budget policy) until you recover — the velocity/reliability balance.
- **What if a correctness SLI goes nonzero (conservation breaks, a double-charge)?** → An _incident_ (Topic 10) — not "within budget" — detect it (Topic 2), contain, correct (reversing entries, L2.1), reconcile.
- **What's the source of truth for "is the money right?"** → The correctness SLIs (the invariants: conservation, no-double-charge, balance accuracy, reconciliation, solvency) — continuously measured (Topic 2).
- **How reliable should the system be?** → Availability: meet the SLO (a real budget); correctness: near-zero errors (a non-negotiable budget) — reliability engineered to a _target_, not maximized, with correctness held highest.
- **How do you balance shipping features vs staying reliable?** → The error budget (availability) governs velocity objectively; correctness risk gates changes more strictly (correctness-risk-weighted pace).
- **Operational signals (reliability-specific):** the correctness SLIs (conservation residual, double-charge rate, balance drift, reconciliation gap, solvency residual — all should be ~0, any nonzero = an incident); the availability SLIs (payment success rate, latency — vs the SLO); error-budget burn rate (availability — how fast are you spending it?); change-induced incident rate (are changes the cause?); the correctness-vs-availability incident split (how often up-and-wrong vs down?). **The correctness SLIs (the invariants at ~0) are the headline reliability signals — a reliable money system continuously verifies the money is right, holds that to a near-zero budget, and manages availability to a real budget.**

---

# Part 7 — Common mistakes, trade-offs, interview Qs, exercises, mastery

## 7.1 Mistakes (each a real money-reliability failure)

1. **Treating availability as the only reliability dimension** (ignoring correctness) → optimizing uptime while the money goes wrong. 2. **Maximizing availability at the cost of correctness** (up-and-wrong) → the defining money-reliability failure (a wrong answer is worse than no answer). 3. **Trading correctness for velocity** ("ship it, we have budget") → correctness has no spendable budget. 4. **No correctness SLIs** (not measuring whether the money is right) → correctness breaches undetected. 5. **Same error budget for correctness and availability** → treating a double-charge like a brief outage (it's far worse). 6. **No error budget at all** (either "100% or bust" or no target) → can't balance velocity vs reliability. 7. **Not gating correctness-risking changes more strictly** → shipping a ledger-corrupting change casually. 8. **Measuring availability but calling it reliability** → missing the correctness dimension. 9. **Not treating a correctness-SLI breach as an incident** → letting a double-charge be "within tolerance". 10. **Chasing 100% availability** (over-investing in uptime past the SLO) → wasted effort; meet the SLO, not maximize. 11. **Not deriving correctness SLIs from the invariants** → missing the ready-made correctness targets (conservation, etc.). 12. **Letting the availability instinct drive degradation/DR/multi-region decisions** → favoring availability over correctness (wrong for money). 13. **No error-budget policy** (no rule for when to freeze changes) → velocity vs reliability fought by argument, not data. 14. **Confusing available with correct** → believing "it's up, so it's fine."

## 7.2 Trade-offs (reason, don't memorize)

- **Correctness vs availability:** right but maybe down (correctness) vs up but maybe wrong (availability). → Correctness first for money (a wrong answer is worse than no answer); availability second.
- **Velocity vs reliability:** ship fast (velocity) vs stay reliable (reliability). → The error budget balances them objectively; for correctness, velocity yields (near-zero budget).
- **Strict vs relaxed availability SLO:** higher uptime + more cost/effort vs lower + cheaper. → Set the SLO to the business need (not 100%); meet it, don't maximize.
- **Near-zero vs some correctness budget:** no money errors + strict change gating vs tolerate some + faster. → Near-zero for correctness (money errors are incidents, not budget).
- **Measure more SLIs vs fewer:** comprehensive correctness visibility + overhead vs simpler + blind spots. → Measure the key invariant SLIs (conservation, double-charge, reconciliation, solvency); they're the correctness definition.
- **Fail-closed vs fail-open (preview, Topic 3):** correct-but-down (closed) vs up-but-maybe-wrong (open). → Fail-closed on correctness for money (preserve correctness over availability).

## 7.3 Interview questions you should answer cold

1. What does "reliability" mean for a money system, and how does it differ from ordinary software? 2. What's the correctness-vs-availability distinction, and why is a wrong answer worse than no answer? 3. Why does money invert the ordinary "maximize availability" instinct? 4. What are SLIs, SLOs, and error budgets? 5. Why have separate SLOs for correctness and availability, and why is the correctness budget near-zero? 6. How do the course's invariants become correctness SLIs? 7. How does the error budget govern the pace of change? 8. Why doesn't the correctness budget flex, and what does that mean for changes? 9. Why are money-system changes gated more on correctness risk than availability risk? 10. How does correctness-first govern the rest of the section (degradation, DR, multi-region)? 11. What are concrete correctness SLIs (conservation, double-charge, reconciliation, solvency)? 12. Why is a correctness-SLI breach an incident, not "within budget"? 13. What's an SLA vs an SLO? 14. Why is "100% reliable" neither achievable nor the goal?

## 7.4 Hands-on exercises (for when we implement)

1. **Correctness SLIs:** instrument the ledger (reusing earlier packages) to continuously measure the correctness invariants as SLIs — conservation residual (should be 0), double-charge rate (0), balance drift (0), reconciliation gap (0), solvency residual (0); show each going nonzero = a breach. 2. **Availability vs correctness:** simulate (a) an unavailable-but-correct state (payments fail, money is right) and (b) an available-but-incorrect state (payments succeed but double-charge); show (b) is worse. 3. **Error budget:** model an availability SLO (99.95%) + its error budget; track budget burn; show the policy (budget left → ship; budget spent → freeze). 4. **Near-zero correctness budget:** show a correctness breach (a double-charge) is an incident (not "within budget"), vs an availability failure (within budget). 5. **Change gating by correctness risk:** classify a change as availability-risk vs correctness-risk; show the correctness-risk change gets stricter gating. 6. **Correctness-SLI dashboard:** a continuous view of the invariant SLIs (all ~0) → the "is the money right?" dashboard (bridging to Topic 2). 7. **The asymmetry in action:** show a system that maximizes availability (ships risky changes) breaching correctness, vs one that gates on correctness staying right.

## 7.5 Mastery checklist (before "observability for correctness")

- [ ] I understand that **reliability for money = correctness**, a _distinct and higher_ dimension than **availability**, and the **asymmetry**: a _wrong_ answer is worse than _no_ answer (money errors are irreversible/propagating/trust-breaching) → **correctness first, availability second** (inverting the ordinary instinct).
- [ ] I know the **SLI → SLO → error-budget** framework and that for money you need **separate SLOs for correctness and availability**, with the **correctness budget near-zero** (a breach is an incident, not budgeted) and the availability budget real (some failure acceptable).
- [ ] I can define **correctness SLIs** by operationalizing the course's **invariants** (conservation residual, double-charge rate, balance drift, reconciliation gap, solvency residual — all should be ~0), making correctness **measured, targeted, monitored**.
- [ ] I understand the **error budget governs the pace of change** (velocity vs reliability — budget left → ship, budget spent → freeze) as a **data-driven arbiter**, and that reliability is **engineered to a target, not maximized** (100% is neither achievable nor the goal).
- [ ] I understand the **money twist**: the **correctness budget doesn't flex** (non-negotiable), so **changes are gated more on correctness risk than availability risk** (correctness-risk-weighted pace — move fast on availability risk, carefully on correctness risk).
- [ ] I understand the **correctness-first reframe governs the whole section** — the recurring resolution "preserve correctness, even at the cost of availability" determines the answer to observability, degradation, testing, chaos, migrations, multi-region, DR, capacity, incidents, and operability.
- [ ] I can name the **operational signals** (the correctness SLIs at ~0 as the headline; availability SLIs vs the SLO; error-budget burn; change-induced incidents) and know a **correctness-SLI breach is an incident**.

---

## One-paragraph synthesis

Reliability for money systems opens with the reframe that governs the entire section: **reliability for money is not the same as reliability for ordinary software**, because _availability_ (is the system up, responding, and fast?) and _correctness_ (is it producing the right answer — for money, _is the money right_: conservation holds, no double-charge, accurate balances, nothing lost or created?) are **two distinct dimensions**, and a system can be perfectly _available_ yet _wrong_; the decisive insight is the **asymmetry** — for money, _a wrong answer is worse than no answer_, because an unavailable payment is recoverable (the customer retries) while a _wrong_ payment (double-charged, money lost, balance corrupted) is real, often-irreversible financial harm that _propagates_ through the ledger into every downstream decision and breaches the trust and compliance on which the business rests — so money systems **invert the ordinary "maximize availability" instinct**: **correctness comes first, availability second** ("fail _closed_ on correctness" — you'd rather be down-but-correct than up-but-wrong). To _manage_ reliability you use the SRE framework — an **SLI** (a measured reliability metric), an **SLO** (a target for it), and an **error budget** (the allowed unreliability, 1 − SLO) — but the crucial money adaptation is to hold **separate SLOs for correctness and availability with correctness at a far higher standard**: availability SLOs ("99.95% of payments succeed", "p99 < 500ms") carry a _real error budget_ you can spend (some unavailability is acceptable), while correctness SLOs ("100% reconcile", "0 double-charges", "conservation always holds") carry a **near-zero, non-negotiable budget** (you cannot "spend" a budget of money errors — any correctness breach is an _incident_, not a budgeted cost). And the **correctness SLIs are precisely the course's invariants operationalized as metrics** — the conservation residual (L2.3, should be 0), the double-charge/duplicate rate (L2.5, 0), balance drift (L2.4, 0), the reconciliation gap (L2-recon, 0), the solvency residual (Section 3, 0), settlement discrepancies, and invalid-transition counts (L2.17) — so every invariant the course built as a _correctness property_ now becomes a _measured, targeted, continuously-monitored reliability SLI_ held to a near-zero budget, meaning the moment any goes nonzero it is an incident, not tolerance. The **error budget then governs the pace of change** — the objective, data-driven arbiter between shipping features (velocity) and staying reliable, since change is the #1 cause of incidents: when the availability budget remains you can afford risk and ship faster; when it's exhausted you freeze risky changes and focus on reliability — making reliability a _feature engineered to a target_, not an absolute to maximize ("100% reliable" is neither achievable nor the goal). But the **money twist** is that the _correctness_ budget **doesn't flex**: you can never knowingly trade correctness for velocity, so the error-budget policy is _asymmetric_ — availability risk governs velocity normally while _any_ correctness-risking change gets extreme scrutiny (property testing, gradual rollout, reconciliation verification), which means **changes to a money system are gated more on correctness risk than availability risk** (a change that might cause a brief outage is less frightening than one that might corrupt the ledger), and the pace of change becomes _correctness-risk-weighted_ ("move fast" on availability-risk changes, "move carefully" on correctness-risk changes). This correctness-first reframe is the **lens for the whole section**: it determines that observability monitors _correctness_ (the invariant SLIs), graceful degradation preserves _correctness even at the cost of availability_ (the inverse of ordinary systems), testing verifies the _correctness invariants_, chaos verifies resilience _without losing real money_, migrations evolve the data _without corrupting money_, multi-region chooses _consistency over availability_ (no cross-region double-spend), disaster recovery recovers _without losing or duplicating money_, capacity _sheds load rather than corrupts_, incidents detect and fix _correctness breaches_ and prove the books right, and operability evolves for decades _without ever breaking correctness_ — so that the recurring resolution throughout the section, and the foundational principle this topic establishes, is always the same: **preserve correctness, even at the cost of availability, because for a money system a wrong answer is worse than no answer, and the correctness of the money is the reliability that matters most.**

When you've reviewed, say **continue** and we'll cover the next topic — **observability for correctness** — the nervous system that watches the invariants: how to monitor a money system to answer "is the money _right_?" (not just "is it up?"), the financial observability stack (metrics/logs/traces centered on the correctness SLIs), real-time invariant monitoring (conservation, held==owed, reconciliation gaps, balance drift), the money-specific signals (settlement lag, stuck transactions, in-flight aging) that have recurred throughout the course, and detecting _correctness_ problems before they become money loss — turning the correctness SLIs of this topic into continuously-watched, alerting reality.
