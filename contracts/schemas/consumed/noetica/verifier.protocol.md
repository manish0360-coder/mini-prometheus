# Noetica `Verifier` protocol — CONSUMED interface stub (Law 15)

**Owner:** Noetica (the *protocol*). Mini Prometheus owns the *concrete oracle* that implements it.
**Status:** RM1 pins this interface shape until the real Noetica contract publishes. Not a data schema — an
interface; therefore no `.schema.json`. See `contracts/RM1-contract-package.md` §4.3.

## Interface

```
verify(plan: ProductionPlan, capability_model) -> Verdict
```

- **Deterministic and pure** for RM1 (spec §9): same `plan` + same `capability_model` ⇒ same `Verdict`.
- Returns a Noetica `Verdict` (`consumed/noetica/verdict.schema.json`) whose `status`/`reason_codes` MP fills
  from its own closed taxonomies (`manufacturing/manufacturability.schema.json`).
- `capability_model` is an **internal** MP representation (not a contract — package §6); it is passed by
  reference/opaque handle across this boundary.

## Conformance

MP's manufacturability oracle **implements** this signature. A protocol-conformance test (RM1 spec §5.6)
asserts the oracle satisfies it. MP must not alter the protocol signature (that is a Noetica-owned MAJOR event).
