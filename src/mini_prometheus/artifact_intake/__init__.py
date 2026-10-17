"""RDAI-1: real design-artifact intake (upstream adapter; NOT part of frozen RM1 intake).

This package grounds the pre-existing OPAQUE STEP seam (``ManufacturingRequest.step_artifact_ref`` /
``DesignArtifactRef``) in a REAL file: it reads bytes from disk, performs basic structural validation of
an ISO-10303-21 *container* (start/end markers + section boundaries — NOT grammar, NOT geometry), and
derives a byte-exact identity (``content_hash`` over raw bytes; ``id = uuid5(NS_MP, content_hash)``).

Four distinct concepts, kept separate (RDAI-1 spec §A/§D):
  1. file identity            — byte SHA-256 (this adapter);
  2. structural validation    — ISO-10303-21 container markers/sections (this adapter);
  3. declared-intent verification — the RM1 oracle verdict on the engineer-declared intent (downstream);
  4. geometric manufacturability  — NOT evaluated, explicitly OUT OF SCOPE.

The adapter extracts and evaluates NO geometry; it imports only the frozen contracts + ``_hashing`` +
stdlib, is a LEAF (no RM module imports it), and performs no planning/verification/persistence. It is an
upstream helper: callers attach the returned ``StepArtifactRef`` to a ``ManufacturingRequest`` and run the
unchanged RM1 path. No CAD kernel, no DFM, no ``ArtifactEvidence`` contract (Option A: no contract change).
"""
