---
title: Two rule gates I built before opening a C2C marketplace to real listings
tags: fraud, compliance, nodejs, python
---

I'm building a peer-to-peer resale marketplace (gift cards, to start). Before I let real listings through, I needed two things to exist and be self-tested, not just designed on paper:

1. A gate that catches suspicious listings without a human reviewing every single one.
2. A gate that catches a required legal disclosure quietly going missing from the page.

Both turned out to have the same shape: a small set of deterministic rules, plus a self-test suite that includes at least one input specifically designed to break the rule. Here's what each one caught.

## 1. Fraud-risk scoring engine

Six signals feed the engine: seller history, price deviation from market, code-format validity, duplicate-listing detection, listing velocity, and image-reuse matching. No ML, no external service — just Node with zero dependencies.

The judging logic has four layers, evaluated in order:

| Layer | Condition | Result |
|---|---|---|
| 1. Structural hard-fail | invalid code format or duplicate code detected | straight to `review_queue` |
| 2. Extreme single signal | any one soft signal ≥ 90 (e.g. price is wildly below market) | straight to `review_queue` |
| 3. Missing signal | any of the 6 signals can't be measured | straight to `review_queue` — a missing signal is never treated as a safe 0 |
| 4. Weighted average | none of the above triggered | ≥ 60 → `review_queue`, below → `auto_approve` |

Layer 2 wasn't in the original design. The first working version scored a listing priced 95% below market — a textbook stolen-code signal — and the weighted average from the other five (safe) signals diluted it enough to land on `auto_approve`. The self-test suite caught it before anything shipped: one test fed a listing with exactly one extreme signal and five clean ones, expected `review_queue`, and got `auto_approve` instead. That's the failure a pure weighted-average design can't see on its own — a bad-but-outnumbered signal gets averaged away.

The fix was the layer itself, not a weight adjustment: an extreme single signal now short-circuits straight to the review queue regardless of how clean everything else looks. 12/12 self-tests pass now, five of them adversarial inputs built specifically to try to slip past the rule (missing signals treated as safe, an extreme signal getting diluted, etc.).

What this doesn't tell you: whether the actual thresholds (60 for the weighted average, 90 for "extreme") match real fraud patterns. That needs live listing data this project doesn't have yet — so the thresholds stay open, not guessed at.

## 2. Broker-disclosure completeness checker

Separately: if you're running the marketplace as an intermediary rather than a seller, you generally owe visitors a clear notice — that you're not the party to the transaction, who the seller is, cancellation/refund terms, your own business info, a dispute-resolution channel, a privacy policy. It's easy for one clause to quietly disappear from a page during an edit and for nobody to notice.

So the notice page (`notice.html`) is paired with a checker (`verify_notice.py`) that doesn't just check "is the clause id present" — it checks whether the *required keywords* are actually in the clause text. Six self-test scenarios, one per way this can silently break:

```
[PASS] normal document, all 6 clauses complete           → PASS (expected PASS)
[PASS] a clause id removed entirely                        → REJECT
[PASS] required keyword missing from the business-info clause → REJECT
[PASS] required keyword missing from the privacy clause       → REJECT
[PASS] required keyword missing from the dispute-resolution clause → REJECT
[PASS] adversarial: "intermediary" mentioned, but no explicit
       "not a party to the transaction" language             → REJECT
```

That last one is the one that mattered. A checker that only looks for the word "intermediary" would happily pass a page that says something like "we're a marketplace that connects buyers and sellers" — true, vague, and legally short of the actual disclosure. The self-test was written to fail exactly that kind of near-miss on purpose, before the checker went anywhere near a real page. 6/6 pass.

What this doesn't tell you: whether the disclosure wording itself would survive an actual legal review in a given jurisdiction. It's marked as not-legal-advice in the README and on the page itself — the checker verifies completeness against a fixed rule set, not legal correctness.

## What's actually here

- Fraud-scoring engine: rule code + self-test suite + integration notes. One-time license, **$15**.
- Broker-notice template + completeness checker: HTML template + checker script + self-test suite + README. One-time license, **$10**.

Neither is tied to gift cards specifically — the scoring engine works for any marketplace that needs "auto-approve the safe majority, queue the rest for a human," and the notice checker works for any C2C platform operating as an intermediary. If either is useful to you, reply here or DM and I'll send the package.

*The counter-example in each section — the diluted extreme signal, the vague "intermediary" wording — is the actual adversarial input from each module's self-test suite, not a hypothetical.*
