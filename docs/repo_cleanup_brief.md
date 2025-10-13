# 🧹 Repo Cleanup & Preparation Brief (for PR Agent + OpenSpec Integration)

### **Objective**
Reorganize the current repository into a clean, modular structure to isolate the **PR agent** and prepare the codebase for **OpenSpec initialization**.  
The goal is to create a maintainable, self-documenting layout where each agent or subsystem can evolve independently and safely under OpenSpec control.

---

## 🧭 1. Repository Audit

**Task:**  
Perform a structural audit of the repository to understand:
- Existing top-level directories (e.g., `/src`, `/agents`, `/data`, `/tests`, `/scripts`)
- Locations of the **PR agent’s** files (prompt logic, merge handling, LLM API code, test harnesses)
- Any shared utilities or dependencies the PR agent uses (config files, helper scripts, etc.)

**Deliverable:**  
Create a short report (`REPO_AUDIT.md`) with:
- List of major directories and their purpose  
- Location of the PR agent’s primary files  
- Any circular or unclear dependencies identified  

---

## 🧱 2. Folder Reorganization Plan

**Goal:**  
Restructure the repository around a **modular agent pattern** — each agent or subsystem gets its own isolated folder.

**Target Layout Example:**
```
repo-root/
  agents/
    pr-agent/
      src/
        __init__.py
        main.py
        logic/
        utils/
      tests/
      configs/
      openspec/          ← (will be added later)
      AGENTS.md          ← (will be added later)
      README.md
  shared/
    utils/
    data_loaders/
  configs/
  scripts/
  notebooks/
  docs/
  openspec/              ← (optional: root-level OpenSpec later)
  README.md
  requirements.txt
  pyproject.toml
```

**Instructions:**
1. Move all code related to the **PR agent** into `agents/pr-agent/src/`.
2. Move its tests into `agents/pr-agent/tests/`.
3. Place any environment or prompt configuration files (YAML, JSON, `.env`, etc.) into `agents/pr-agent/configs/`.
4. Shared scripts (utilities used by multiple agents) go under `shared/utils/`.
5. Update import paths and relative references accordingly.

---

## 🧩 3. Dependency & Import Refactor

**Task:**
- Update all `import` statements or relative paths broken by the move.  
- Ensure the PR agent can still run end-to-end from its new directory.  
- If using Python, add appropriate `__init__.py` files to mark packages.  
- Verify that no relative imports cross between agents (e.g., `from ..dispatch_agent import ...` should be replaced with shared abstractions).

**Deliverable:**  
A fully runnable PR agent with consistent imports and updated dependencies.

---

## 🧪 4. Environment Verification

**Task:**  
Confirm that after reorganization:
- The PR agent can be executed independently (`python agents/pr-agent/src/main.py` or equivalent entrypoint).  
- Tests under `agents/pr-agent/tests/` all pass.  
- Shared utilities are accessible without circular dependencies.

**Deliverable:**  
A summary (`VERIFY_ENVIRONMENT.md`) documenting:
- How to run the PR agent.  
- How to run its test suite.  
- Any remaining dependency issues.

---

## 🧠 5. Documentation & Metadata

**Task:**  
For clarity and AI-integration, add or update the following docs:

- `agents/pr-agent/README.md` — describe purpose, dependencies, and entrypoint.  
- Root `README.md` — include an overview of all agents and how they relate.  
- Create a `docs/ARCHITECTURE.md` explaining high-level structure (especially if there are multiple agents or modules).

---

## 🚀 6. Preparation for OpenSpec

Once cleanup is done and verified:

**Inside the PR agent folder:**
```bash
cd agents/pr-agent
openspec init
```

**This will create:**
```
agents/pr-agent/openspec/
agents/pr-agent/AGENTS.md
```

Then immediately:
1. Add your **baseline spec** describing the PR agent’s current capabilities:
   ```
   openspec/specs/pr_agent_overview.md
   ```
2. Create your first **change proposal**:
   ```bash
   openspec propose "Refactor prompt evaluation for improved merge reasoning"
   ```
3. Begin managing all future refactors and enhancements through `openspec/changes/`.

---

## 🧾 7. Deliverables Checklist

| Deliverable | Description |
|--------------|-------------|
| `REPO_AUDIT.md` | Summary of current repo structure |
| New folder structure | As shown above |
| Updated imports | All code runs in the new layout |
| `VERIFY_ENVIRONMENT.md` | Confirmation that PR agent works |
| `agents/pr-agent/README.md` | Local documentation |
| `docs/ARCHITECTURE.md` | Repo-wide architectural overview |
| Initialized `openspec/` | Ready for spec-first iteration |

---

## 🧭 8. Guardrails

- ❌ Do **not** delete or rewrite existing logic until it’s confirmed working after relocation.  
- ✅ Use **relative imports** for intra-agent modules, **absolute imports** for cross-agent ones.  
- ❌ Do not run `openspec init` in the root repo yet — only inside the PR agent folder.  
- ✅ Use Git to commit each phase separately (`git add -p`), so the history remains auditable.
