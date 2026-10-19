# gemini-activity-harvester

Autonomous skill and toolchain to scrape, index, and audit Google Gemini activity history (`myactivity.google.com/product/gemini`), identify actionable prompt tools, skills, and architectures, deduplicate against existing local and remote repositories, and swarm on scaffolded packages.

## Features

- **Activity Index Parser**: Ingests Google MyActivity streams, extracting prompts, voice audio attachments, timestamps, and model responses.
- **Intent Classification**: Classifies conversation records into:
  - Agent Skills (`SKILL.md`)
  - Prompt Tools (e.g., agent handoff protocols)
  - Autonomous System Repositories (e.g., Discord Gemini voice bot, OpenHaul logistics loop, KiCad agent tools)
- **Multi-Level Deduplication**: Cross-checks candidates against `~/dev`, local agent skills registries (`~/.gemini/config/skills/`, `~/.agents/skills/`), and the user's remote GitHub repositories (`gh repo list`) to guarantee zero duplicate repositories.
- **Verification Engine**: Built-in test suite adhering to acceptance criteria with 100% test pass guarantee.

## Installation

### Via `npx skills`
Install the skill into your coding agent environment with [`npx skills`](https://skills.sh):

```bash
npx skills add NoJuanNobody/gemini-activity-harvester -g
```

### Local Development
```bash
git clone https://github.com/NoJuanNobody/gemini-activity-harvester.git
cd gemini-activity-harvester
pip install -e .
```

## Running Tests

```bash
python3 -m unittest discover -s tests
```

## License
MIT
