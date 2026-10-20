import os
import json
from typing import List, Dict, Any, Optional
from .parser import parse_activity_dump, classify_prompt_intent, ActivityItem
from .dedupe import Deduplicator
from .scraper import ChromeScraper

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
            is_dup = deduper.is_duplicate(intent["recommended_name"])
            entry = {
                "timestamp": item.timestamp,
                "prompt": item.prompt,
                "type": intent["type"],
                "recommended_name": intent["recommended_name"],
                "confidence": intent["confidence"],
                "audio_url": item.audio_url,
                "is_duplicate": is_dup,
                "status": "DUPLICATE_SKIPPED" if is_dup else "ACTIONABLE"
            }
            analyzed.append(entry)
            
    summary = {
        "total_activities_parsed": len(items),
        "total_creation_events": len(analyzed),
        "items": analyzed,
        "existing_entities_checked": len(deduper.all_existing)
    }
    return summary

def harvest_live_chrome(
    workspace_dir: str = "/Users/alejandrolondono/dev",
    owner: str = "NoJuanNobody",
    limit: Optional[int] = 50,
    max_pages: int = 0,
    fetch_details: bool = True
) -> Dict[str, Any]:
    """
    Scrapes live Google Chrome Gemini activity tab, classifies intents,
    and audits against existing local and remote repositories.
    """
    scraper = ChromeScraper()
    scraped_items = scraper.scrape(limit=limit, max_pages=max_pages, fetch_details=fetch_details)
    deduper = Deduplicator(workspace_dir=workspace_dir, owner=owner)
    
    analyzed = []
    actionable = []
    duplicates = []
    
    for item in scraped_items:
        prompt = item.get("prompt", "")
        intent = classify_prompt_intent(prompt)
        
        entry = {
            "index": item.get("index"),
            "timestamp": item.get("timestamp"),
            "prompt": prompt,
            "type": intent["type"],
            "recommended_name": intent["recommended_name"],
            "confidence": intent["confidence"],
            "chat_url": item.get("chat_url"),
            "audio_url": item.get("audio_url"),
            "model_response": item.get("model_response"),
            "is_duplicate": False,
            "status": "NON_ACTIONABLE"
        }
        
        if intent["type"] != "other" and intent["recommended_name"]:
            is_dup = deduper.is_duplicate(intent["recommended_name"])
            entry["is_duplicate"] = is_dup
            if is_dup:
                entry["status"] = "DUPLICATE_SKIPPED"
                duplicates.append(entry)
            else:
                entry["status"] = "ACTIONABLE"
                actionable.append(entry)
                
        analyzed.append(entry)
        
    return {
        "total_activities_scraped": len(scraped_items),
        "total_creation_events": len(actionable) + len(duplicates),
        "total_actionable": len(actionable),
        "total_duplicates": len(duplicates),
        "actionable_candidates": actionable,
        "duplicate_candidates": duplicates,
        "all_items": analyzed,
        "existing_entities_checked": len(deduper.all_existing)
    }
