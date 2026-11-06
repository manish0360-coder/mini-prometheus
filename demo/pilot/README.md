# Shop-owner pilot demonstrator

A static, offline page that shows a workshop owner, in about five minutes, what Mini Prometheus does with a
declared workshop and a job. See ADR-0023.

**Everything here is synthetic example data.** No real workshop, customer or job appears. The verdicts are actual
MP-S1 CLI output on that example data; the page itself calculates nothing.

## Open it

Double-click `index.html`, or open it in any current browser. It needs no server, build step or network connection.

The page has four steps:
1. The workshop.
2. A job (pick one of four).
3. The check.
4. What it does not know.

Move between them with the step buttons, Back/Next, or the left and right arrow keys. The top bar always shows the
**Example data** badge, a language switch (English / हिन्दी) and a light/dark switch.

To start a visit from a fixed point, add parameters to the address:

```
index.html?lang=hi&job=turned_shaft#check
```

| Parameter | Values |
|---|---|
| `lang` | `en`, `hi` |
| `job` | `bracket`, `turned_shaft`, `brass_cover`, `precision_plate` |
| `theme` | `light`, `dark` |
| `#…` (the step) | `#workshop`, `#job`, `#check`, `#limits` |

## What is in this folder

| Path | What it is |
|---|---|
| `index.html` | The four screens. Display only: every status and reason is read from `snapshots/data.js`. |
| `strings.js` | Every visible word, keyed, in English (`en`) and Hindi (`hi`), with the same keys in both. |
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

`tests/boundary/test_demo_pilot.py` fails if any of these happens:
- a re-captured snapshot differs from the committed one;
- a displayed verdict differs from the CLI output;
- a code, machine, material or target shown has no label;
- English and Hindi hold different keys.

Review a re-capture before committing it.

## Hindi

The Hindi text is a **first draft**. Before it is shown to a shop owner, a Hindi-speaking person should read it on
the screen. Machine words that owners usually say in English (milling, drilling, CNC) are written that way in
Devanagari on purpose. To change a word, edit `hi` in `strings.js`. To add a language, add a table with the same
keys.

## Limits

- No drawings, 3D models or Velith geometry.
- No machine size limits or per-machine materials.
- No cost, cycle-time, delivery-time or lead-time estimate.
- No live evaluation, accounts, storage or hosting.
