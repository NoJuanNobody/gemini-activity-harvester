import re
from typing import List, Dict, Any, Optional

class ActivityItem:
    def __init__(self, raw_text: str, timestamp: str = "", prompt: str = "", details_url: str = ""):
        self.raw_text = raw_text
        self.timestamp = timestamp
        self.prompt = prompt
        self.details_url = details_url
        self.category: Optional[str] = None
        self.target_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "prompt": self.prompt,
            "category": self.category,
            "target_name": self.target_name,
            "details_url": self.details_url,
        }

def parse_activity_dump(text: str) -> List[ActivityItem]:
    """Parse raw text dump from Google My Activity (Gemini product)."""
    items = []
    # Split by activity delimiter "Gemini Apps"
    chunks = re.split(r'Gemini Apps\s+', text)
    for chunk in chunks[1:]:
        chunk = chunk.strip()
        if not chunk:
            continue
        
        # Extract prompt
        prompt_match = re.search(r'Prompted\s*(.*?)(?=\n\d+:\d+|\nAudio|\nDetails|$)', chunk, re.DOTALL)
        prompt = prompt_match.group(1).strip() if prompt_match else ""
        
        # Extract timestamp
        time_match = re.search(r'(\d+:\d+\s*[AP]M)', chunk)
        timestamp = time_match.group(1) if time_match else ""
        
        # Extract audio / details indicator
        item = ActivityItem(raw_text=chunk, timestamp=timestamp, prompt=prompt)
        items.append(item)
    return items

def classify_prompt_intent(prompt: str) -> Dict[str, Any]:
    """
    Classifies whether a prompt/conversation aims to create:
    - prompt_tool (e.g. handoff template, prompt generator)
    - skill (agent skill, SKILL.md specification)
    - mcp_or_agent_repo (e.g. discord bot, logistics platform, hardware design)
    - other (general search, personal query)
    """
    p_lower = prompt.lower()
    
    # Check for Agent Skill
    if any(k in p_lower for k in ["skill", "agent skill", "remote control skill"]):
        return {
            "type": "skill",
            "confidence": 0.95,
            "recommended_name": "remote-control-skill" if "remote control" in p_lower else "agent-skill"
        }
    
    # Check for Handoff / Prompt tool
    if any(k in p_lower for k in ["handoff", "handoff prompt", "write a prompt", "generate a prompt", "prompt template"]):
        return {
            "type": "prompt_tool",
            "confidence": 0.90,
            "recommended_name": "baton" if "handoff" in p_lower else "prompt-tool"
        }
        
    # Check for bot / platform / agent architecture
    if any(k in p_lower for k in ["discord bot", "graph loop", "zero-knowledge", "distributed logistics", "kicad", "pcb design"]):
        name = "bot"
        if "discord" in p_lower:
            name = "discord-voice-gemini"
        elif "kicad" in p_lower or "pcb" in p_lower:
            name = "agent-pcb-designer"
        elif "logistics" in p_lower or "graph" in p_lower:
            name = "openhaul"
            
        return {
            "type": "mcp_or_agent_repo",
            "confidence": 0.85,
            "recommended_name": name
        }
        
    return {
        "type": "other",
        "confidence": 0.1,
        "recommended_name": None
    }
