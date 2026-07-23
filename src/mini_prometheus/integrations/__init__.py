"""Integrations: adapters ONLY (no business logic).

The single layer permitted to reference upstreams. Per the strict DAG (Law 9) and Law 4,
Mini Prometheus imports **Velith** (engineering entry point) and consumes **Noetica**
platform mechanisms (twin engine, provenance) through versioned interfaces (Law 14).
It never imports MiniFlyWire (Law 4). Adapters translate upstream <-> contract types only.
"""
