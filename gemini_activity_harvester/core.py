import os
import json
from typing import List, Dict, Any
from .parser import parse_activity_dump, classify_prompt_intent
from .dedupe import Deduplicator

def harvest_and_audit(activity_text: str, workspace_dir: str = "/Users/alejandrolondono/dev", owner: str = "NoJuanNobody") -> Dict[str, Any]:
    """
    Parses activity dump, identifies all tool/skill/prompt creations,
    and runs deduplication against local workspace and remote GitHub.
    """
    items = parse_activity_dump(activity_text)
    deduper = Deduplicator(workspace_dir=workspace_dir, owner=owner)
    
    analyzed = []
    for item in items:
        intent = classify_prompt_intent(item.prompt)
        if intent["type"] != "other":
            entry = {
                "timestamp": item.timestamp,
                "prompt": item.prompt,
                "type": intent["type"],
                "recommended_name": intent["recommended_name"],
                "confidence": intent["confidence"],
                "is_duplicate": deduper.is_duplicate(intent["recommended_name"])
            }
            analyzed.append(entry)
            
    summary = {
        "total_activities_parsed": len(items),
        "total_creation_events": len(analyzed),
        "items": analyzed,
        "existing_entities_checked": len(deduper.all_existing)
    }
    return summary
