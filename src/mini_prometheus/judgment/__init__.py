"""RM4 — Engineering Judgment (Mini Prometheus domain reasoning content).

Engineering Judgment is the deterministic, advisory capability of *judging a proposed manufacturing
solution in the full engineering context of its case*. Its first implementation is Engineering Critique;
future forms (comparison, ranking, evaluation, optimization advice) fit beneath this identity without
changing it.

This package also hosts the **internal** ``EngineeringSituation`` primitive — the coherent engineering
state of one manufacturing case — which is assembled and consumed **only within** ``judgment/``: it is
not a contract, not a schema, never persisted, carries no external identity, and is never exposed
outside this package. Boundaries: consumes RM1/RM2/RM3 outputs read-only; never imports MiniFlyWire
(Law 4); no Noetica store/lifecycle engine (Law 6); no planning, verification, retrieval, ML, or
persistence.
"""
