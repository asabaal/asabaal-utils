
from __future__ import annotations
from typing import Dict, Any
from .model import Plan, PlanItem

def _norm_pkg(name: str) -> str:
    return name.replace(" ", "_").lower()

def build_plan(doc: Dict[str, Any]) -> Plan:
    spec_name = doc.get("spec", "unnamed")
    version = doc.get("version", "0.0.0")
    pkg = _norm_pkg(spec_name)
    plan = Plan(spec_name=spec_name, version=version, items=[])

    plan.items.append(PlanItem(kind="plan_file", path="build/plan.json"))
    plan.items.append(PlanItem(kind="manifest_file", path="artifacts/manifest.json"))

    for fn in doc.get("functions", []) or []:
        f_id = fn.get("id","")
        f_name = fn.get("name","")
        plan.items.append(PlanItem(kind="code_stub",
                                   path=f"scaffolds/src/{pkg}/{f_name}.py",
                                   function_id=f_id, function_name=f_name, template_id="code_stub",
                                   notes={"behavior": fn.get("behavior", []), "io": fn.get("io", {})}))
        plan.items.append(PlanItem(kind="test_stub",
                                   path=f"scaffolds/tests/test_{f_name}.py",
                                   function_id=f_id, function_name=f_name, template_id="test_stub",
                                   notes={"validation": fn.get("validation", []), "function": f_name}))
        lessons = ((fn.get("dmt") or {}).get("teach") or {}).get("lessons", []) or []
        for lesson in lessons:
            lesson_name = lesson.get("name","lesson")
            script = ((lesson.get("demo") or {}).get("script") or f"notebooks/{f_name}_taught.py")
            plan.items.append(PlanItem(kind="teach_stub",
                                       path=f"scaffolds/{script}",
                                       function_id=f_id, function_name=f_name, template_id="teach_stub",
                                       notes={"lesson_name": lesson_name, "expects": (lesson.get("demo") or {}).get("expects", [])}))
            plan.items.append(PlanItem(kind="validate_step",
                                       path=f"validate:teach:{f_name}:{lesson_name}",
                                       function_id=f_id, function_name=f_name, template_id=None,
                                       notes={"script": script}))
            for exp in (lesson.get("demo") or {}).get("expects", []) or []:
                if isinstance(exp, dict) and exp:
                    out_path = list(exp.values())[0]
                    plan.items.append(PlanItem(kind="manifest_entry",
                                               path="artifacts/manifest.json",
                                               function_id=f_id, function_name=f_name, template_id=None,
                                               notes={"artifact": out_path, "type": list(exp.keys())[0]}))
        plan.items.append(PlanItem(kind="doc_stub",
                                   path=f"scaffolds/docs/{f_name}.md",
                                   function_id=f_id, function_name=f_name, template_id="doc_stub",
                                   notes={"function": f_name}))
    return plan
