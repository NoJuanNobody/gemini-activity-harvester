import sys
import argparse
import json
from .core import harvest_and_audit

def main():
    parser = argparse.ArgumentParser(description="Gemini Activity Harvester CLI")
    subparsers = parser.add_subparsers(dest="subcommand")

    audit_parser = subparsers.add_parser("audit", help="Audit an activity dump file")
    audit_parser.add_argument("--file", "-f", required=True, help="Path to raw activity text dump")
    audit_parser.add_argument("--owner", "-o", default="NoJuanNobody", help="GitHub repo owner for deduplication")

    args = parser.parse_args()

    if args.subcommand == "audit":
        with open(args.file) as f:
            text = f.read()
        res = harvest_and_audit(text, owner=args.owner)
        print(json.dumps(res, indent=2))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
