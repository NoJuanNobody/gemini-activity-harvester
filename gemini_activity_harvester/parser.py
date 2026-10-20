import re
from typing import List, Dict, Any, Optional

class ActivityItem:
    def __init__(
        self,
        raw_text: str,
        timestamp: str = "",
        prompt: str = "",
        details_url: str = "",
        audio_url: Optional[str] = None,
        model_response: Optional[str] = None
    ):
        self.raw_text = raw_text
        self.timestamp = timestamp
        self.prompt = prompt
        self.details_url = details_url
        self.audio_url = audio_url
        self.model_response = model_response
        self.category: Optional[str] = None
        self.target_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "prompt": self.prompt,
            "category": self.category,
            "target_name": self.target_name,
            "details_url": self.details_url,
            "audio_url": self.audio_url,
            "model_response": self.model_response
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
        audio_url = None
        audio_match = re.search(r'https?://[^\s"\']+\.wav[^\s"\']*', chunk)
        if audio_match:
            audio_url = audio_match.group(0)
            
        item = ActivityItem(raw_text=chunk, timestamp=timestamp, prompt=prompt, audio_url=audio_url)
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
    
    # Check for specific skill sub-types
    if any(k in p_lower for k in ["skill", "agent skill", "custom skill"]):
        rec_name = "agent-skill"
        if "remote control" in p_lower:
            rec_name = "remote-control-skill"
        elif any(k in p_lower for k in ["background", "background agent", "conversational interface", "orchestration"]):
            rec_name = "background-agent-orchestration"
        elif any(k in p_lower for k in ["edge", "local ai", "edge agent"]):
            rec_name = "edge-agent-graph-loop"
        elif "artcraft" in p_lower:
            rec_name = "artcraft-pipeline"
            
        return {
            "type": "skill",
            "confidence": 0.95,
            "recommended_name": rec_name
        }
    
    # Check for Handoff / Prompt tool
    if any(k in p_lower for k in ["handoff", "handoff prompt", "write a prompt", "generate a prompt", "prompt template", "hand-off document"]):
        return {
            "type": "prompt_tool",
            "confidence": 0.90,
            "recommended_name": "baton" if ("handoff" in p_lower or "coding agent" in p_lower) else "prompt-tool"
        }
        
    # Check for bot / platform / agent architecture / hardware
    if any(k in p_lower for k in ["discord bot", "graph loop", "zero-knowledge", "distributed logistics", "kicad", "pcb design", "artcraft"]):
        name = "bot"
        if "discord" in p_lower:
            name = "discord-voice-gemini"
        elif "kicad" in p_lower or "pcb" in p_lower:
            name = "agent-pcb-designer"
        elif "artcraft" in p_lower:
            name = "artcraft"
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
