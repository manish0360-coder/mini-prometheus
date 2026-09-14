"""RM5 — Compounding Validation Experiment (Mini Prometheus, MP-local measurement).

RM5 is a *measurement/validation* milestone, not a reasoning capability. It asks whether Mini
Prometheus's accumulated verified experience produces a measurable improvement in engineering judgment
against the deterministic RM1 oracle, on strictly held-out, analogous-but-non-identical cases, within
one fixed capability regime.

This package is **MP-local and minimal**. It consumes RM1 (oracle/planner/runner), RM3 (precedent), and
RM4 (judgment) read-only, generates a deterministic corpus (materialized to a committed fixture), and
writes an evaluation report to an isolated sink (``artifacts/evaluation/``) — **never** the episode
store. It introduces **no** contract, no general experiment framework, no new cognitive primitive, and
no real-Velith integration. It never imports MiniFlyWire (Law 4) or a Noetica engine (Law 6).
"""
