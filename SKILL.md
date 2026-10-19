---
name: gemini-activity-harvester
description: Scrape, index, and analyze Google Gemini activity history (myactivity.google.com/product/gemini) via authenticated browser sessions, identify actionable prompts/skills/tools, deduplicate against existing repositories, and scaffold validated agent packages.
---

# Gemini Activity Harvester

Autonomous skill to index, extract, and convert Google Gemini prompts, reasoning traces, and conversational outputs into reusable tools, skills, and code repositories.

## Overview

Users often explore architectures, design agent skills, and draft system specifications conversationally inside Google Gemini. `gemini-activity-harvester` bridges the gap between conversational ideation and concrete software repositories by:

1. **Scraping Activity Indexes**: Traverses Google MyActivity (`myactivity.google.com/product/gemini`) and connected Gemini Web client sessions via local browser automation (AppleScript / Playwright CDP / Chrome DevTools Protocol).
2. **Dialogue & Output Extraction**: Captures user prompts, voice audio references, full reasoning traces, and model deliverables without triggering anti-bot hurdles.
3. **Semantic Classification**: Identifies conversations that propose, design, or specify:
   - **Agent Skills** (conforming to the Agent Skills standard with YAML frontmatter)
   - **CLI Tools / MCP Servers** (Model Context Protocol endpoints or CLI-Anything harnesses)
   - **Architecture Specifications** (e.g. distributed logistics, hardware design, graph loops)
4. **Deduplication Engine**: Checks local directories (`~/dev/`, `~/.gemini/config/skills/`, `~/.agents/skills/`) and remote GitHub accounts (`gh repo list`) to skip existing repositories and prevent redundant work.
5. **Swarm Execution & Repo Scaffolding**: Automatically initializes git repositories, synthesizes production code, generates rigorous pytest test suites, verifies 100% passing tests, and publishes installable packages to GitHub and `npx skills`.

## Installation

Install using [`npx skills`](https://skills.sh):

```bash
npx skills add NoJuanNobody/gemini-activity-harvester -g
```

Or install locally with pip:

```bash
pip install -e /Users/alejandrolondono/dev/gemini-activity-harvester
```

## CLI Usage

```bash
# Scan and analyze Gemini activity text
gemini-activity-harvester scan --input /path/to/activity.txt --dedupe

# Run classification on scraped chats
gemini-activity-harvester classify /path/to/gemini_scrapes/

# Scrape live Chrome session
gemini-activity-harvester scrape --active-browser chrome

# Full pipeline: Harvest, classify, deduplicate, and report
gemini-activity-harvester run
```

## Architecture

```
Google MyActivity (Chrome)
           │
           ▼
[ Browser Bridge / Scraper ]
           │
           ▼
[ Activity Parser & Classifier ]
   ├── Agent Skills (SKILL.md)
   ├── MCP Servers / CLI Tools
   └── Research Specs / Hand-offs
           │
           ▼
[ Deduplication Check ] ── (Local ~/dev + GitHub CLI gh repo list)
           │
           ▼
[ Scaffolder & Test Swarm ] ──► Verified Repos & npx skills packages
```

## Verification & Tests

Run test suite:
```bash
pytest -v tests/
```
