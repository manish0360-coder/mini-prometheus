"""Experience read side (RM2) — the *consume* half of the Experience Flow (Handbook §2.4).

Reads Mini Prometheus's own emitted ``ManufacturingEpisode`` records back for reuse. This is MP
manufacturing content and the extraction seed for Noetica's memory framework (Law 8, N.3). It is
**not** a memory/store engine: no retention, compression, pruning, or general query — those are
Noetica's lifecycle framework (Law 6, §11.11) and are deferred.
"""
