# Artifact-Blocker Sourcing Check (Direction 2 value probe)

**Type:** Read-only sourcing check. No download performed, no artifact added to the repo, no code/contract/
schema/test/dependency/frozen-spec/ADR/Git change. Probe NOT started. Prior deferred hypotheses not
reopened. HEAD `ab8cc44`; working tree CRLF-only; untracked `research/`, `uv.lock` preserved.

**Question:** can we obtain two suitable, real STEP artifacts from public, legally accessible datasets —
(1) a part with independently documented geometry and a specific, objectively verifiable property, and
(2) a matched control for the same narrow rule — without inventing ground truth or modifying the source?

**Note checked first:** the four existing `research/` notes name the artifact blocker but contain no CAD
dataset sources. This check adds them. Bounded, direction-specific lookup — not a broad sweep.

## Evidence table

| Source | Format | Ground-truth metadata | License / access | Independent validation | Fit for the test |
|---|---|---|---|---|---|
| **MFCAD++** (QUB; Colligan et al., *Computer-Aided Design* 2022; DOI 10.17034/d1fec5a0-…) | **STEP B-rep**, 59,665 models, 3–10 machining features each; train/val/test splits | **Per-B-rep-face machining-feature class label** in `feature_labels.txt`; extractable from the STEP | **CC BY** (stated on the dataset page), 1.5 GB zip, embargo ended 2022-02-12 | Peer-reviewed (CAD journal, 131 Scopus cites); labels authored by dataset creators, reproducible from the files | **Primary fit** — labels = "which machining features the geometry contains"; contradiction + control both selectable |
| **Fusion 360 Gallery – Segmentation** (Autodesk; BRepNet, CVPR 2021) | STEP B-rep, >35,000 models | **Per-face modeling-operation label** (extrude, fillet, …) | License **not confirmed** in results (Autodesk; commonly non-commercial research) — must verify before use | Peer-reviewed; labels authored by Autodesk | Backup — modeling-op (not machining) labels; license unverified |
| **ABC Dataset** (NYU; 1M Onshape models) | STEP B-rep | Geometry only (no machining-feature labels) | Release **MIT**; individual models under **Onshape Terms** (model copyright stays with creators) | Geometry deterministic from STEP (OCCT) | For Direction-1 geometry-extraction checks only; **not** for Direction-2 property/contradiction |

## Can these support a controlled contradiction test without inventing ground truth?

**Yes, with MFCAD++.** The per-face machining-feature labels are the independently documented, objectively
verifiable property. A contradiction/control pair is drawn *as-is* from the dataset:
- **Contradiction case:** a model whose labels include a machining feature (e.g. a pocket/slot) that a
  chosen declared-operation set would *not* produce → declared intent contradicts the geometry; the current
  declared-only pipeline would still return MANUFACTURABLE.
- **Matched control:** a model whose labeled features are all covered by that same declared-operation set →
  consistent → the rule must not flag.
Same dataset, same labeling scheme, same narrow rule — no invented ground truth, no artifact modification
(read-only; held in a scratch space outside the MP repo).

## Honest caveats (must not be overstated)

1. **Synthetic-but-valid, not production parts.** MFCAD++ models are *programmatically generated*
   (PythonOCC), not parts someone physically manufactured. They are genuine STEP B-rep solids with real,
   published ground truth — sufficient to test *whether a geometry rule catches a declared/geometry
   contradiction* (the Direction-2 **value** hypothesis). They do **not** establish real-world **frequency
   or demand** — that remains the separately-listed missing evidence (capability-to-evidence §7 item 3).
2. **Label→ProcessOp mapping is an interpretation step.** Mapping a machining-feature class to MP's declared
   `ProcessOp` ontology is a modeling choice made for the probe; the *labels themselves* are not invented,
   but the mapping must be stated explicitly and kept conservative.
3. **CC BY attribution** is required on any use/redistribution; keep artifacts out of the MP repo regardless.

## Recommendation

**The artifact blocker is resolvable: use MFCAD++ (CC BY) as the source for the Direction-2 value probe.**
It supplies, legally and with independently documented per-feature ground truth, both a contradiction case
and a matched control for one narrow rule — the exact pair the probe needs. ABC (MIT) is a backup for
Direction-1 geometry-extraction validation only; Fusion 360 Gallery is a secondary option pending license
confirmation.

**Exactly what this unblocks and what it does not:** it clears evidence item #1 (a real, ground-truthed
artifact pair) and makes item #2 (demonstrated catch) testable. It does **not** clear item #3 (real-world
frequency/importance) — MFCAD++ being synthetic means the probe can prove the rule *works*, not that the
error it catches is *common in practice*.

**Next step (not yet taken, per instruction):** on authorization, select one labeled contradiction model +
one matched control from MFCAD++ into a scratch space outside the repo, record the chosen feature, declared
operation set, and label→op mapping — then (separately) run the geometry probe. No download or probe done
here.

*No code, contract, schema, test, dependency, frozen spec, ADR, or Git state was changed. This note is the
only artifact produced; no dataset was downloaded or added to the repository.*
