import subprocess
import json
import time
import re
from typing import List, Dict, Any, Optional

def parse_dialog_text(text: str) -> Dict[str, Any]:
    """Parses raw text extracted from the Google My Activity details modal."""
    if not text:
        return {}
        
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    full_prompt = ""
    chat_url = None
    model_response = ""
    timestamp = ""
    
    for i, line in enumerate(lines):
        if line.startswith("Prompted"):
            full_prompt = line.replace("Prompted", "").strip()
            next_idx = i + 1
            while next_idx < len(lines) and not any(lines[next_idx].startswith(k) for k in ["Audio", "Details", "event", "https://"]):
                full_prompt += " " + lines[next_idx]
                next_idx += 1
            break

    url_match = re.search(r"https://gemini\.google\.com/app/[a-zA-Z0-9_-]+", text)
    if url_match:
        chat_url = url_match.group(0)

    for i, line in enumerate(lines):
        if line == "event" and i + 1 < len(lines):
            timestamp = lines[i + 1]
            break
            
    if not timestamp:
        time_match = re.search(r"((Today|Yesterday|[A-Za-z]+ \d{1,2}(?:, \d{4})?) at )?(\d+:\d+\s*[AP]M)", text, re.IGNORECASE)
        if time_match:
            timestamp = time_match.group(0)

    # Extract model response: text between chat url/marker and 'Why this activity?'
    if "gemini.google.com/app/" in text:
        chat_idx = -1
        for i, line in enumerate(lines):
            if "gemini.google.com/app/" in line:
                chat_idx = i
                break
        if chat_idx != -1:
            why_idx = len(lines)
            for j in range(chat_idx + 1, len(lines)):
                if "Why this activity?" in lines[j]:
                    why_idx = j
                    break
            resp_lines = [
                lines[k] for k in range(chat_idx + 1, why_idx)
                if lines[k] != "chat" and not lines[k].startswith('{"contentMetadata"')
            ]
            model_response = "\n\n".join(resp_lines).strip()

    return {
        "full_prompt": full_prompt,
        "chat_url": chat_url,
        "timestamp": timestamp,
        "model_response": model_response
    }

class ChromeScraper:
    def __init__(self, browser_name: str = "Google Chrome"):
        self.browser_name = browser_name

    def is_browser_running(self) -> bool:
        cmd = [
            "osascript", "-e",
            f'tell application "System Events" to return (name of processes) contains "{self.browser_name}"'
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res.stdout.strip().lower() == "true"

    def ensure_tab(self, url: str = "https://myactivity.google.com/product/gemini") -> bool:
        """Ensures an activity tab is open, active, and focused in Google Chrome."""
        if not self.is_browser_running():
            raise RuntimeError(f"{self.browser_name} is not running.")
        
        # Activate Chrome so click events and DOM interactions work smoothly
        activate_script = f"""
tell application "{self.browser_name}"
    activate
    repeat with w in windows
        repeat with t in tabs of w
            if (URL of t contains "myactivity.google.com/product/gemini") then
                set active tab of w to t
                set index of w to 1
                return "found"
            end if
        end repeat
    end repeat
    open location "{url}"
    return "opened"
end tell
"""
        res = subprocess.run(["osascript", "-e", activate_script], capture_output=True, text=True)
        if "opened" in res.stdout:
            time.sleep(2.5)
        return True

    def execute_js(self, js_code: str) -> str:
        """Executes JavaScript inside the active or matching activity tab in Chrome."""
        escaped_js = js_code.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", " ")
        apple_script = f"""
tell application "{self.browser_name}"
    repeat with w in windows
        repeat with t in tabs of w
            if (URL of t contains "myactivity.google.com/product/gemini") then
                return execute t javascript "{escaped_js}"
            end if
        end repeat
    end repeat
    return ""
end tell
"""
        res = subprocess.run(["osascript", "-e", apple_script], capture_output=True, text=True)
        return res.stdout.strip()

    def load_more(self, times: int = 1) -> int:
        """Clicks 'Load more' button to paginate activity history."""
        loaded = 0
        for _ in range(times):
            js = """
(() => {
    const buttons = Array.from(document.querySelectorAll("button"));
    const loadMore = buttons.find(b => b.innerText.includes("Load more"));
    if (loadMore) {
        loadMore.click();
        return "clicked";
    }
    return "none";
})()
"""
            res = self.execute_js(js)
            if res == "clicked":
                loaded += 1
                time.sleep(1.5)
            else:
                break
        return loaded

    def get_cards_summary(self) -> List[Dict[str, Any]]:
        """Extracts the basic summary of all activity cards loaded in the DOM."""
        js = """
(() => {
    const cards = Array.from(document.querySelectorAll("div.uUy2re"));
    return JSON.stringify(cards.map((card, idx) => {
        const promptEl = card.querySelector("div.QTGV3c");
        const timeEl = card.querySelector("div.H3Q9vf");
        const audioEl = card.querySelector("div.SiEggd a");
        const detailsBtn = card.querySelector("a.WFTFcf");
        return {
            index: idx,
            prompt: promptEl ? promptEl.innerText.trim() : "",
            time_text: timeEl ? timeEl.innerText.trim() : "",
            has_audio: !!audioEl,
            audio_url: audioEl ? audioEl.href : null,
            has_details_button: !!detailsBtn,
            aria_label: detailsBtn ? detailsBtn.getAttribute("aria-label") : ""
        };
    }));
})()
"""
        out = self.execute_js(js)
        if not out or out == "missing value":
            return []
        try:
            return json.loads(out)
        except Exception:
            return []

    def get_card_detail(self, card_idx: int) -> Dict[str, Any]:
        """Clicks the details modal for the specified card and parses full details."""
        # Close any open dialog first
        close_js = """
(() => {
    const d = document.querySelector("div[role=\\\"dialog\\\"], div.g3VIld");
    if (d) {
        const btn = d.querySelector("button[aria-label*=\\\"Close\\\" i], button.Uxmn1b");
        if (btn) btn.click();
    }
})()
"""
        self.execute_js(close_js)
        time.sleep(0.15)

        click_js = f"""
(() => {{
    const cards = Array.from(document.querySelectorAll("div.uUy2re"));
    const card = cards[{card_idx}];
    if (!card) return "not_found";
    const btn = card.querySelector("a.WFTFcf");
    if (btn) {{
        btn.click();
        return "clicked";
    }}
    return "no_btn";
}})()
"""
        res = self.execute_js(click_js)
        if res != "clicked":
            return {}

        time.sleep(0.5)
        read_js = """
(() => {
    const dialogs = document.querySelectorAll("div[role=\\\"dialog\\\"], div.g3VIld");
    const d = dialogs[dialogs.length - 1];
    const txt = d ? d.innerText : "";
    if (d) {
        const btn = d.querySelector("button[aria-label*=\\\"Close\\\" i], button.Uxmn1b");
        if (btn) btn.click();
    }
    return txt;
})()
"""
        raw_text = self.execute_js(read_js)
        return parse_dialog_text(raw_text)

    def scrape(
        self,
        limit: Optional[int] = None,
        max_pages: int = 0,
        fetch_details: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Executes complete scrape of Google Gemini activity.
        Extracts prompts, timestamps, voice WAV URLs, full dialog details, and model responses.
        """
        self.ensure_tab()
        
        if max_pages > 0:
            self.load_more(max_pages)
            
        cards = self.get_cards_summary()
        if limit is not None:
            cards = cards[:limit]
            
        items = []
        for card in cards:
            idx = card["index"]
            prompt_raw = card.get("prompt", "")
            if not prompt_raw.startswith("Prompted") and not card.get("has_audio"):
                continue
                
            clean_prompt = prompt_raw.replace("Prompted ", "").strip()
            item = {
                "index": idx,
                "timestamp": card.get("time_text", "").split("•")[0].strip(),
                "prompt": clean_prompt,
                "audio_url": card.get("audio_url"),
                "chat_url": None,
                "model_response": None
            }
            
            is_truncated = "..." in clean_prompt or "…" in clean_prompt
            has_intent_keywords = any(k in clean_prompt.lower() for k in [
                "skill", "prompt", "handoff", "agent", "bot", "tool", "platform", "orchestration", "paper"
            ])
            
            if fetch_details and (is_truncated or has_intent_keywords):
                details = self.get_card_detail(idx)
                if details:
                    if details.get("full_prompt"):
                        item["prompt"] = details["full_prompt"]
                    item["chat_url"] = details.get("chat_url")
                    item["model_response"] = details.get("model_response")
                    if details.get("timestamp"):
                        item["timestamp"] = details["timestamp"]
                        
            items.append(item)
            
        return items
