# RM3 Architectural Debt Register

- **Status:** Recorded at RM3-M5 (governance). This is **architectural debt**, not RM3 implementation
  work. No RM3 milestone (M0–M6) implements any item here; recording it discharges the review finding.
- **Scope:** Engineering Precedent Reasoning (RM3). Governed by the frozen RM3 Specification
  (`specs/milestones/RM3-engineering-precedent-reasoning.md` §6/§7, Appendix A), the RM3 Engineering
  Package, and Handbook Laws 3/6/8 (N.3).

---

## DEBT-RM3-1 — The retriever is an intentional O(N) local extraction seed

The RM3-M2 retriever (`src/mini_prometheus/precedent/retriever.py`) scores the entire episode corpus
linearly (O(N)) on every query. **This is deliberate, not an oversight.** Per RM3 spec §7 and the
Engineering Package, the retrieval/distance machinery is *mechanism*, held MP-local only as the
**extraction seed** for Noetica's future memory/retrieval mechanism — never RM3's architectural
identity. A simple, deterministic, read-only linear scan is the correct seed: it is easy to verify,
carries no hidden state, and keeps the seed/identity boundary crisp.

**Not to be "optimized" inside RM3.** Introducing an index, caching, embeddings, or a vector store into
the RM3 retriever would (a) pull Noetica's lifecycle/retrieval framework into Mini Prometheus (Law 6
violation), and (b) blur the mechanism/identity boundary (Law 3). Algorithmic optimization of the
retriever is explicitly **out of RM3 scope**.

## DEBT-RM3-2 — Large-scale indexed retrieval belongs to future Noetica extraction

Scalable retrieval (indexing, approximate nearest-neighbour, retention/compression/pruning, a memory
lifecycle) is **Noetica platform mechanism** (Law 8 grow-by-extraction; N.3), not Mini Prometheus
domain content. When Noetica publishes its retrieval/memory interface, RM3 swaps its local retriever
for that interface **with no change to RM3's identity, responsibilities, or the PrecedentReport
contract** (spec §7). Until then, the O(N) seed stands.

**Governance hook (non-normative, spec Appendix A):** any future milestone that *extends* this
extraction seed should pass through an "Extraction Review Gate" — explicitly deciding whether the
extended capability still belongs inside Mini Prometheus (domain content) or should now extract into
Noetica (platform mechanism). Adopting that gate would require a ratified CAP (Laws 22/23) and is out
of scope here.

## DEBT-RM3-3 — Signal relevance threshold has no canonical home yet

The "strongly relevant" threshold (and top-K) that gate signal derivation are, per spec §5, conceptually
part of `precedent_model_version`. The frozen RM3-M1 `PrecedentModel` does not yet carry them, so they
are surfaced as overridable defaults (`retriever.rank(top_k=…)`, `reasoner.DEFAULT_RELEVANCE_THRESHOLD`).
Consolidating them into the versioned `PrecedentModel` is a **future, ratified** change (it would bump
`precedent_model_version`), not RM3-M5 work. Flagged at RM3-M1/M2/M3; recorded here for continuity.

---

*Recorded as governance at RM3-M5. No implementation, no algorithm change, no contract change follows
from this register. Each item is discharged only by a future, separately-ratified milestone.*
