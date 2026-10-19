import os
import subprocess
from typing import Set, List, Dict, Any

def get_local_repos_and_skills(workspace_dir: str = "/Users/alejandrolondono/dev") -> Set[str]:
    """Inspects local filesystem for existing repositories and agent skills."""
    existing = set()
    if os.path.exists(workspace_dir):
        for entry in os.listdir(workspace_dir):
            full_path = os.path.join(workspace_dir, entry)
            if os.path.isdir(full_path):
                existing.add(entry.lower())
                
    # Check ~/.gemini/config/skills and ~/.agents/skills
    extra_dirs = [
        os.path.expanduser("~/.gemini/config/skills"),
        os.path.expanduser("~/.agents/skills"),
        os.path.expanduser("~/.claude/skills"),
    ]
    for ed in extra_dirs:
        if os.path.exists(ed):
            for skill_dir in os.listdir(ed):
                existing.add(skill_dir.lower())
                
    return existing

def get_remote_github_repos(owner: str = "NoJuanNobody") -> Set[str]:
    """Queries GitHub CLI for existing repositories under the target owner."""
    existing = set()
    try:
        res = subprocess.run(
            ["gh", "repo", "list", owner, "--limit", "150", "--json", "name"],
            capture_output=True,
            text=True,
            check=True
        )
        import json
        repos = json.loads(res.stdout)
        for r in repos:
            existing.add(r["name"].lower())
    except Exception:
        # If gh fails or offline, return empty set or fallback
        pass
    return existing

class Deduplicator:
    def __init__(self, workspace_dir: str = "/Users/alejandrolondono/dev", owner: str = "NoJuanNobody"):
        self.workspace_dir = workspace_dir
        self.owner = owner
        self.local_items = get_local_repos_and_skills(workspace_dir)
        self.remote_repos = get_remote_github_repos(owner)
        self.all_existing = self.local_items.union(self.remote_repos)

    def is_duplicate(self, target_name: str) -> bool:
        """Determines if the target name or its variants already exist."""
        clean_name = target_name.lower().strip()
        variants = [
            clean_name,
            clean_name.replace("-", ""),
            clean_name.replace("_", "-"),
            f"cli-anything-{clean_name}",
            f"{clean_name}-skill",
            f"{clean_name}-app",
        ]
        return any(v in self.all_existing for v in variants)

    def filter_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filters out items that already exist either locally or remotely."""
        actionable = []
        for c in candidates:
            name = c.get("recommended_name")
            if not name:
                continue
            if self.is_duplicate(name):
                c["status"] = "DUPLICATE_SKIPPED"
            else:
                c["status"] = "ACTIONABLE"
                actionable.append(c)
        return actionable
