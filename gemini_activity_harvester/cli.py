import sys
import argparse
import json
import asyncio
from .core import harvest_and_audit
from .scraper import scrape_gemini_activity_sync

def main():
    parser = argparse.ArgumentParser(description="Gemini Activity Harvester CLI")
    subparsers = parser.add_subparsers(dest="subcommand")

    # Audit subcommand
    audit_parser = subparsers.add_parser("audit", help="Audit an activity dump file")
    audit_parser.add_argument("--file", "-f", required=True, help="Path to raw activity text dump")
    audit_parser.add_argument("--owner", "-o", default="NoJuanNobody", help="GitHub repo owner for deduplication")

    # Scrape subcommand
    scrape_parser = subparsers.add_parser("scrape", help="Scrape live Gemini activity from myactivity.google.com")
    scrape_parser.add_argument("--headless", "-H", action="store_true", help="Run browser in headless mode (default: false)")
    scrape_parser.add_argument("--scrolls", "-s", type=int, default=3, help="Number of scrolls to load more activities (default: 3)")
    scrape_parser.add_argument("--output", "-o", help="Save scraped activity to JSON file")
    scrape_parser.add_argument("--owner", default="NoJuanNobody", help="GitHub repo owner for deduplication")

    args = parser.parse_args()

    if args.subcommand == "audit":
        with open(args.file) as f:
            text = f.read()
        res = harvest_and_audit(text, owner=args.owner)
        print(json.dumps(res, indent=2))

    elif args.subcommand == "scrape":
        print("🚀 Starting Gemini Activity Scraper...")
        print("⚠️  Please ensure you are logged into Google in your browser.")
        print("🌐 Launching browser and navigating to myactivity.google.com/product/gemini...")

        try:
            # Scrape activity
            items = scrape_gemini_activity_sync(headless=args.headless, scroll_count=args.scrolls)

            print(f"\n✅ Scraped {len(items)} activity items")

            # Convert to text format for audit
            activity_text = "\n\n".join([
                f"[{item['timestamp']}] {item['title']}\n{item['content']}"
                for item in items
            ])

            # Run audit
            print("\n📊 Running audit and deduplication...")
            res = harvest_and_audit(activity_text, owner=args.owner)

            # Output results
            print(json.dumps(res, indent=2))

            # Save if requested
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump({
                        "scraped_items": items,
                        "audit_results": res
                    }, f, indent=2)
                print(f"\n💾 Results saved to {args.output}")

        except Exception as e:
            print(f"❌ Error during scraping: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
