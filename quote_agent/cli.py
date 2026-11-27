"""Command line: python -m quote_agent.cli samples/* --lang en"""
from __future__ import annotations

import argparse

from .export import to_dataframe
from .graph import run
from .loaders import load_path


def main():
    ap = argparse.ArgumentParser(description="Compare supplier quotes with AI")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--lang", default="ar", choices=["ar", "en"])
    ap.add_argument("--model", default=None)
    args = ap.parse_args()

    result = run([load_path(f) for f in args.files], language=args.lang, model=args.model)
    for err in result.get("errors", []):
        print("ERROR:", err)
    if result.get("rows"):
        print(to_dataframe(result["rows"], args.lang).to_string(index=False))
    rec = result.get("recommendation")
    if rec:
        print("\n==>", rec.best_supplier, "\n", rec.summary)
        for r in rec.reasons:
            print(" +", r)
        for r in rec.risks:
            print(" !", r)
        print("\n--- Email ---\n", rec.email_subject, "\n\n", rec.email_body)


if __name__ == "__main__":
    main()
