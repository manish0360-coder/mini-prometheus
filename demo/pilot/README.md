# Shop-owner pilot demonstrator

A static, offline page that shows a workshop owner, in about five minutes, what Mini Prometheus does with a
declared workshop and a job. See ADR-0023.

**Everything here is synthetic example data.** No real workshop, customer or job appears. The verdicts are actual
MP-S1 CLI output on that example data; the page itself calculates nothing.

## Open it

Open `index.html` in a browser. It needs no server, build step or network connection.

## What is in this folder

| Path | What it is |
|---|---|
| `index.html` | The four screens: the workshop, a job, the check, what it does not know. Display only. |
| `strings.js` | Every visible word, keyed. `en` is complete; `hi` is empty. |
| `inputs/shop.example_workshop.json` | Synthetic shop declaration (`evidence_class: synthetic`). |
| `inputs/job_*.json` | Four synthetic job requests. |
| `capture.py` | Runs the shipped CLI for each job and writes `snapshots/`. Orchestration only. |
| `snapshots/` | Captured CLI output, the plan steps and verdict the CLI stored, `data.js` for the page, `MANIFEST.json`. |

## Re-capture after a Mini Prometheus change

From the repository root, in the Docker verifier (Python 3.11):

```bash
python demo/pilot/capture.py --commit "$(git rev-parse HEAD)"
```

`MANIFEST.json` records the commit, the SHA-256 of every input and output, and the exact command for each case:

```
python -m mini_prometheus.orchestration.runner demo/pilot/inputs/<job>.json --capability-model-file demo/pilot/inputs/shop.example_workshop.json
```

`tests/boundary/test_demo_pilot.py` re-runs the capture and fails if any snapshot differs, if a displayed verdict
differs from the CLI output, or if a shown code has no label. Review a re-capture before committing it.

## Add Hindi

Fill `hi` in `strings.js` with the same keys as `en`. Any key left out falls back to English. The language switch
appears as soon as `hi` has a key. Have a native speaker check the text with a shop owner.

## Limits

- No drawings, 3D models or Velith geometry.
- No machine size limits or per-machine materials.
- No cost, cycle-time, delivery-time or lead-time estimate.
- No live evaluation, accounts, storage or hosting.
