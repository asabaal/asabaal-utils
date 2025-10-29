
from __future__ import annotations
from typing import Dict, Any, List
import json, pathlib
from .model import Plan
from .templates import CODE_STUB, TEST_STUB, TEACH_STUB, DOC_STUB

def _ensure_dir(path: pathlib.Path):
    path.parent.mkdir(parents=True, exist_ok=True)

def _summarize_io(io: Dict[str, Any]) -> str:
    ins = io.get("inputs", []) or []
    ins_s = ", ".join(f"{i.get('name')}:{i.get('type')}" for i in ins if isinstance(i, dict))
    out = io.get("output", {}) or {}
    return f"({ins_s}) -> {out.get('type','Any')}"

def _block(items: List[str], prefix: str = "- ") -> str:
    return "\\n".join(prefix + s for s in items) if items else prefix + "(none)"

def _behavior_lines(behavior: List[Any]) -> List[str]:
    lines = []
    for b in behavior or []:
        if isinstance(b, dict):
            s = b.get("step","").strip()
        else:
            s = str(b).strip()
        if s: lines.append(s)
    return lines

def _validation_lines(validation: List[Any]) -> List[str]:
    vals = []
    for v in validation or []:
        if isinstance(v, dict):
            t = v.get("type","")
            r = v.get("rule","")
            if t or r:
                vals.append(f"- [{t}] {r}")
        else:
            vals.append(f"- {v}")
    return vals

def render_plan_to_disk(plan: Plan, out_dir: str):
    root = pathlib.Path(out_dir)

    # plan file
    plan_file = root / "build" / "plan.json"
    _ensure_dir(plan_file)
    with plan_file.open("w", encoding="utf-8") as f:
        json.dump({"spec_name": plan.spec_name, "version": plan.version,
                   "items":[i.__dict__ for i in plan.items]}, f, indent=2)

    # manifest
    manifest_path = root / "artifacts" / "manifest.json"
    _ensure_dir(manifest_path)
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
        except Exception:
            manifest = {"artifacts": []}
    else:
        manifest = {"artifacts": []}

    for it in plan.items:
        if it.kind.endswith("_stub"):
            p = root / it.path
            _ensure_dir(p)
            if it.kind == "code_stub":
                behavior_lines = _behavior_lines(it.notes.get("behavior"))
                io_summary = _summarize_io(it.notes.get("io", {}))
                content = CODE_STUB.format(function_name=it.function_name,
                                           function_id=it.function_id,
                                           io_summary=io_summary,
                                           behavior_block=_block(behavior_lines, prefix="- "))
            elif it.kind == "test_stub":
                validation_lines = _validation_lines(it.notes.get("validation"))
                content = TEST_STUB.format(function_name=it.function_name,
                                           validation_block="\n".join(validation_lines) or "# (no validation rules)")
            elif it.kind == "teach_stub":
                expects = it.notes.get("expects") or []
                exp_lines = []
                for exp in expects:
                    if isinstance(exp, dict) and exp:
                        k, v = list(exp.items())[0]
                        exp_lines.append(f"- {k}: {v}")
                content = TEACH_STUB.format(function_name=it.function_name,
                                            lesson_name=it.notes.get("lesson_name","lesson"),
                                            expects_block="\n".join(exp_lines) or "# (no expected artifacts declared)")
            elif it.kind == "doc_stub":
                expects = it.notes.get("expects") or []
                exp_lines = []
                for exp in expects:
                    if isinstance(exp, dict) and exp:
                        k, v = list(exp.items())[0]
                        exp_lines.append(f"  - {k}: {v}")
                content = DOC_STUB.format(function_name=it.function_name,
                                          lesson_hint=it.notes.get("lesson_name","lesson"),
                                          expects_block="\n".join(exp_lines) or "  - (none)")
            else:
                content = ""
            p.write_text(content, encoding="utf-8")

        elif it.kind == "manifest_entry":
            art = it.notes.get("artifact")
            typ = it.notes.get("type")
            if art:
                manifest["artifacts"].append({"path": art, "type": typ, "checksum": None})

    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
