# 🔧 AI Spec‑Driven Development Pipeline (v2) — End‑to‑End Blueprint

**Goal:** Turn your OpenSpec setup into a rigorous, automated pipeline that converts specifications into working, validated software with AI assistance — reliably, repeatably, and transparently.

**Audience:** Your coding agents + human maintainers.  
**Scope:** Library (programmatic music), AI assistant layer, Front‑End Studio, and CI/CD.

---

## 0) Guiding Principles

- **Spec is the source of truth.** Code, tests, and docs are generated *from* and validated *against* specs.
- **Determinism > novelty.** Reproducible outputs, pinned toolchains, seeds, checksums.
- **Small, verifiable steps.** Agents work in short loops with measurable success criteria.
- **Explainability everywhere.** Every agent action yields a rationale and evidence link.
- **“Done Means Taught.”** Shipping includes docs, examples, and in‑app guidance.

---

## 1) OpenSpec: Authoritative Intent Layer

**Artifacts**
- `openspec/specs/*.yml` — per‑domain specs with `spec_id`, `version`, and `requirements:`
- `openspec/changes/<change-id>/change.yml` — cross‑spec change proposal

**Minimal requirement entry example:**
```yaml
spec_id: programmatic-music-framework
title: Programmatic Music Framework
version: 0.1.0
requirements:
  - id: PMF-001
    title: Deterministic TimeGrid
    description: Generate reproducible temporal grids, mixed meters.
    validation:
      - type: unit
        file: tests/test_timegrid.py
        target: "pass"
```

**Ground rules**
- Each requirement must be testable: include `validation` hints (test file, tool, or command).
- Every change references affected specs and success criteria.

---

## 2) Spec → Scaffolds & Contracts (Auto‑Generation)

**Purpose:** Convert requirements into *stubs*, *tests*, and *docs* the agent can fill.

**Generator responsibilities**
- Create code stubs with function signatures + docstrings linked to requirement IDs.
- Create test stubs aligned to `validation` hints.
- Create documentation skeletons and runnable examples.

**CLI (example)**
```bash
# Read specs → create scaffolds (idempotent)
tools/specgen generate --from openspec/specs --out scaffolds/
```

**Output layout**
```
scaffolds/
  src/
    pmf/timegrid.py          # TODO: PMF-001
  tests/
    test_timegrid.py         # TODO: PMF-001
  docs/
    pmf_timegrid.md          # TODO: PMF-001
```

**Agent prompt contract (short)**
- Implement only the red TODOs.
- Keep signatures, docstrings, and requirement IDs intact.
- Write tests first if missing; then make them pass.
- Explain design choices; reference requirement IDs in commits.

---

## 3) Validation Suite (Local & CI)

**Layers**
- **Static:** lint, type check, format (ruff/flake8, mypy/pyright, prettier, eslint)
- **Unit/Property:** pytest/vitest + hypothesis
- **Integration:** end‑to‑end compose→render→analyze
- **Artefact checks:** checksums, LUFS tolerance, key/tempo verification
- **Docs:** doctests and link checks

**Local run (developer/agent)**
```bash
make validate   # or `scripts/validate.sh`
```

**Example `scripts/validate.sh`:**
```bash
#!/usr/bin/env bash
set -euo pipefail
echo "▶ Static checks"; ruff check .; pyright || true; npm run lint || true
echo "▶ Unit tests"; pytest -q
echo "▶ Integration"; python tools/e2e/run_song_pipeline.py --spec specs/demo.yml
echo "▶ OpenSpec"; openspec validate
echo "✅ All validations complete"
```

---

## 4) CI Orchestration (GitHub Actions example)

**.github/workflows/ci.yml**
```yaml
name: CI
on:
  pull_request:
  push:
    branches: [ main ]
jobs:
  build-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Install deps
        run: |
          pip install -r requirements-dev.txt
          npm ci || true
      - name: Validate
        run: bash scripts/validate.sh
      - name: Upload artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: ci-artifacts
          path: |
            artifacts/**
            reports/**
            openspec/**/*.log
```

**Gates (fail build if):**
- Unit or integration tests fail
- OpenSpec validation fails
- Docs regress (broken links, missing examples)
- Audio analysis outside tolerance (e.g., LUFS ±0.2, clipping > 0)

---

## 5) AI Agent Roles & Contracts

**A. Planner**
- Reads change + specs → creates task queue with priorities
- Produces execution plan with expected outputs, tests, and timebox

**B. Builder**
- Implements stubs, updates tests, runs local `validate.sh`
- Commits with requirement IDs: `feat(PMF-001): deterministic grid`

**C. Verifier**
- Reviews diffs vs spec natural language
- Ensures tests match requirements and cover failure cases
- Writes human‑readable validation summary

**D. Doc Writer**
- Updates docs/cookbook/examples for each feature
- Ensures front‑end help panels reference new features

**Agent execution loop (pseudo):**
```
while change not complete:
  Planner: pick top requirement R
  Builder: implement R (TDD), run validate.sh
  if validation fails:
    Verifier: explain failure cause
    Builder: fix; re-run
  Doc Writer: update docs/examples
  Commit + push with #R
  Post summary + artifacts
```

---

## 6) Self‑Healing Loop (Autonomous Repair)

**Trigger:** Any of (unit fail, spec fail, perf regression) → open an “auto‑fix” branch:
```
autofix/R-<id>-<slug>
```

**Autofix steps:**
1. Localize failure (stacktrace, coverage, recent diff).
2. Propose minimal patch (guard clauses, bounds checks, tolerance fix).
3. Re-run `validate.sh`. If green: open PR with summary and evidence.
4. If not green after N attempts → escalate with diagnostic bundle.

**PR template (auto‑generated)**
```markdown
### Why
Fix failing PMF-001 tolerance check (LUFS drift).

### What
- Adjust limiter headroom by 0.2 dB
- Add regression test `test_lufs_tolerance()`

### Evidence
- Before: -14.6 LUFS; After: -14.2 LUFS (target -14.0±0.2)
- Artifacts: reports/evidence/PMF-001/*
```

---

## 7) Observability & Traceability

**Store per‑run bundle:**
```
artifacts/<run-id>/
  specs/       # normalized spec snapshots
  code/        # stubs + patches
  tests/       # results + coverage
  audio/       # renders + checksums
  reports/     # analysis JSON + plots
  summary.md   # human summary + next steps
```

**Minimal metadata**
- spec versions + checksums
- seeds and toolchain versions
- environment fingerprint (OS, python/node/ffmpeg versions)

---

## 8) Security & Guardrails

- Agents run in sandboxes without production credentials.
- Allow‑list shell commands; no `sudo`, no destructive fs ops.
- Secrets via environment injection; rotated per run.
- Rate‑limit API calls; redact logs by default.

---

## 9) Rollout Plan (Phased Adoption)

**Phase 0 — Baseline**
- Ensure all specs validate
- Add `scripts/validate.sh`
- Stand up CI job with artifacts

**Phase 1 — Scaffolds**
- Implement `specgen generate`
- Enforce TDD workflow for each requirement

**Phase 2 — Agent Loop**
- Introduce Planner/Builder/Verifier/Doc Writer roles
- Require requirement IDs in commits

**Phase 3 — Self‑Healing**
- Enable auto‑fix branches on failure
- Auto PRs with evidence

**Phase 4 — Teaching**
- Embed examples into front‑end help panels
- “Explain this” links to generated docs/plots

---

## 10) Concrete Command Cookbook

```bash
# Validate everything locally
bash scripts/validate.sh

# Generate scaffolds from specs
tools/specgen generate --from openspec/specs --out scaffolds/

# Run e2e scenario (music)
python tools/e2e/run_song_pipeline.py --spec specs/covenant_keeping_god.yml

# Link evidence to requirement
openspec evidence add PMF-001 reports/analysis.json

# Archive completed change (snapshot)
openspec archive implement-covenant-keeping-god
```

---

## 11) Definition of Done (per requirement)

- ✅ Tests pass locally & in CI (unit + integration where applicable)
- ✅ Spec validation passes (`openspec validate`)
- ✅ Docs updated (concept + how‑to + example)
- ✅ Front‑end help updated (panel/tour/tooltips)
- ✅ Evidence attached to requirement (`openspec evidence add`)
- ✅ Commit(s) reference requirement ID
- ✅ If audio: renders within tolerance (LUFS/clip/key/tempo)

---

## 12) Risk Register & Mitigations

| Risk | Mitigation |
|------|------------|
| Spec drift vs code | Specgen idempotent scaffolds; schema checks |
| Non‑deterministic audio | Pin engines/assets; compare checksums; headroom guard |
| Agent overreach | Approval gates; small diffs; one‑layer edits |
| CI flakiness | Rerun with seed; retry strategy; cache deps |
| Doc rot | “Done Means Taught” gate required for merge |

---

## 13) Example: “Covenant Keeping God” Runbook

1. **Change ready:** `implement-covenant-keeping-god` (49 requirements).  
2. **Scaffold:** `tools/specgen generate` → stubs/tests/docs.  
3. **Loop per requirement:** TDD → validate → docs → commit `#ID`.  
4. **E2E:** run pipeline script; store artifacts; attach evidence.  
5. **Archive:** snapshot build with checksums & metrics.  
6. **Ship:** front‑end example + in‑app tutorial loaded.

---

## 14) Agent Prompts (Ready‑to‑Use)

**Planner (input = change + specs):**
> Read all `openspec/specs/*.yml` and the change description. Produce a prioritized task queue mapping each requirement ID → files to implement, tests to run, and acceptance criteria. Timebox each task to ≤ 45 minutes. Output as a Markdown checklist with code paths.

**Builder (input = single requirement):**
> Implement requirement {ID}. Edit only scaffolds that contain TODO for this ID. Write/complete tests first, then code until `bash scripts/validate.sh` passes locally. Keep diffs small and reference {ID} in commit message.

**Verifier (input = diff + test results):**
> Compare the code changes against the requirement. Explain whether the implementation satisfies the contract. Identify missing tests or edge cases. Output a human‑readable summary with links to evidence files.

**Doc Writer (input = requirement + code):**
> Update docs and examples so a new user can use this feature in < 5 minutes. Include a runnable snippet and a brief troubleshooting note. Ensure front‑end help text references this example.

---

## 15) Success Criteria for the Pipeline

- A new requirement can move from “spec only” → “implemented & validated” **without human typing code**, using agent roles + CI gates.
- Failures create actionable auto‑PRs with diagnosis and evidence.
- Every shipped feature teaches itself via examples and in‑app help.

---

**Version:** 1.0  
**Owner:** Dr. Asabaal Horan  
**File:** ai_spec_dev_pipeline_v2.md  
**Purpose:** Operational blueprint for spec‑to‑software automation.
