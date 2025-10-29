
from __future__ import annotations
import argparse, json, sys
from .runner import StageOneRunner

def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="dmtc.stage1", description="DMT Coder Stage 1 CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check", help="Parse and validate the spec only")
    c.add_argument("--spec", required=True)

    pl = sub.add_parser("plan", help="Plan scaffolds from spec; print plan JSON")
    pl.add_argument("--spec", required=True)

    g = sub.add_parser("generate", help="Generate scaffolds to an output directory")
    g.add_argument("--spec", required=True)
    g.add_argument("--out", required=True)

    args = p.parse_args(argv)

    if args.cmd == "check":
        rep = StageOneRunner.check(args.spec)
        if rep.passed:
            print("✅ Spec validation passed.")
            return 0
        else:
            print("❌ Spec validation failed:")
            for m in rep.messages:
                print(" -", m)
            return 1

    if args.cmd == "plan":
        plan = StageOneRunner.plan(args.spec)
        print(json.dumps({"spec_name": plan.spec_name, "version": plan.version,
                          "items": [i.__dict__ for i in plan.items]}, indent=2))
        return 0

    if args.cmd == "generate":
        plan = StageOneRunner.generate(args.spec, args.out)
        print(json.dumps({"spec_name": plan.spec_name, "version": plan.version,
                          "items": [i.__dict__ for i in plan.items]}, indent=2))
        return 0

    return 0

if __name__ == "__main__":
    sys.exit(main())
