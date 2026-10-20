import os
import sys
import argparse
import json
from datetime import datetime
from .core import harvest_and_audit, harvest_live_chrome
from .parser import classify_prompt_intent, parse_activity_dump
from .dedupe import Deduplicator
from .scraper import ChromeScraper

def main():
    parser = argparse.ArgumentParser(description="Gemini Activity Harvester CLI")
    subparsers = parser.add_subparsers(dest="subcommand")

    # audit subcommand
    audit_parser = subparsers.add_parser("audit", help="Audit an activity dump file")
    audit_parser.add_argument("--file", "-f", required=True, help="Path to raw activity text dump")
    audit_parser.add_argument("--owner", "-o", default="NoJuanNobody", help="GitHub repo owner for deduplication")

    # scrape subcommand
    scrape_parser = subparsers.add_parser("scrape", help="Scrape live Chrome session")
    scrape_parser.add_argument("--active-browser", default="chrome", choices=["chrome"], help="Browser to scrape from")
    scrape_parser.add_argument("--limit", "-l", type=int, default=50, help="Maximum number of items to scrape")
    scrape_parser.add_argument("--max-pages", "-p", type=int, default=0, help="Number of times to click Load More")
    scrape_parser.add_argument("--output", "-o", help="Path to save scraped JSON results")
    scrape_parser.add_argument("--dedupe", action="store_true", default=True, help="Run deduplication check")
    scrape_parser.add_argument("--owner", default="NoJuanNobody", help="GitHub repo owner for deduplication")

    # scan subcommand
    scan_parser = subparsers.add_parser("scan", help="Scan and analyze Gemini activity text")
    scan_parser.add_argument("--input", "-i", required=True, help="Path to activity file")
    scan_parser.add_argument("--dedupe", action="store_true", default=True, help="Run deduplication check")
    scan_parser.add_argument("--owner", "-o", default="NoJuanNobody", help="GitHub repo owner")

    # classify subcommand
    classify_parser = subparsers.add_parser("classify", help="Run classification on scraped chats")
    classify_parser.add_argument("path", help="Path to text or json file of scraped chats")

    # run subcommand
    run_parser = subparsers.add_parser("run", help="Full pipeline: Harvest, classify, deduplicate, and report")
    run_parser.add_argument("--limit", type=int, default=50, help="Max items to scrape")
    run_parser.add_argument("--max-pages", type=int, default=1, help="Max pages to load")
    run_parser.add_argument("--owner", default="NoJuanNobody", help="GitHub repo owner")
    run_parser.add_argument("--output", "-o", help="Output JSON path")

    args = parser.parse_args()

    if args.subcommand == "audit":
        with open(args.file) as f:
            text = f.read()
        res = harvest_and_audit(text, owner=args.owner)
        print(json.dumps(res, indent=2))

    elif args.subcommand == "scrape" or args.subcommand == "run":
        limit = args.limit if hasattr(args, "limit") else 50
        max_pages = args.max_pages if hasattr(args, "max_pages") else 0
        owner = args.owner if hasattr(args, "owner") else "NoJuanNobody"
        
        print(f"[*] Starting Gemini Activity Harvester (browser: chrome, limit: {limit}, pages: {max_pages})...")
        res = harvest_live_chrome(
            owner=owner,
            limit=limit,
            max_pages=max_pages,
            fetch_details=True
        )
        
        # Save output if specified or default
        out_file = args.output
        if not out_file:
            os.makedirs("scrapes", exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_file = f"scrapes/gemini_activity_{ts}.json"
            
        with open(out_file, "w") as f:
            json.dump(res, f, indent=2)
            
        print(f"[+] Scraped {res['total_activities_scraped']} activities.")
        print(f"[+] Identified {res['total_creation_events']} tool/skill/mcp creation events.")
        print(f"[+] Actionable Candidates (new): {res['total_actionable']}")
        print(f"[+] Duplicates (already exist): {res['total_duplicates']}")
        print(f"[+] Results saved to: {out_file}")
        
        if res["actionable_candidates"]:
            print("\nActionable Candidates Found:")
            for cand in res["actionable_candidates"]:
                print(f" - [{cand['type']}] {cand['recommended_name']}: {cand['prompt'][:80]}...")
                if cand.get("chat_url"):
                    print(f"   URL: {cand['chat_url']}")

    elif args.subcommand == "scan":
        with open(args.input) as f:
            text = f.read()
        res = harvest_and_audit(text, owner=args.owner)
        print(json.dumps(res, indent=2))

    elif args.subcommand == "classify":
        with open(args.path) as f:
            content = f.read()
        # Handle JSON or raw text
        try:
            data = json.loads(content)
            items = data.get("all_items", data) if isinstance(data, dict) else data
            for item in items:
                prompt = item.get("prompt", "")
                print(f"Prompt: {prompt[:60]}... -> {classify_prompt_intent(prompt)}")
        except Exception:
            items = parse_activity_dump(content)
            for item in items:
                print(f"Prompt: {item.prompt[:60]}... -> {classify_prompt_intent(item.prompt)}")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
