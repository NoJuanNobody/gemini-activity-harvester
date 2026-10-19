import unittest
import sys
import os

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gemini_activity_harvester.parser import parse_activity_dump, classify_prompt_intent
from gemini_activity_harvester.dedupe import Deduplicator
from gemini_activity_harvester.core import harvest_and_audit

SAMPLE_ACTIVITY_DUMP = """
Gemini Apps
Prompted Can you come up with a plan for a harness and model agnostic remote control skill for all harnesses?
Audio included.
6:11 PM • • Details

Gemini Apps
Prompted Generate a prompt to Handoff to a coding agent
6:13 PM • • Details

Gemini Apps
Prompted Okay. So, we want to create a Discord bot.Gemini. I want to be able to in Discord have a call
3:21 PM • • Details

Gemini Apps
Prompted Tell me about all the Bufords.
Audio included.
7:32 PM • • Details
"""

class TestHarvester(unittest.TestCase):
    def test_parse_activity_dump(self):
        items = parse_activity_dump(SAMPLE_ACTIVITY_DUMP)
        self.assertEqual(len(items), 4)
        self.assertIn("remote control skill", items[0].prompt)
        self.assertEqual(items[0].timestamp, "6:11 PM")
        self.assertIn("Handoff to a coding agent", items[1].prompt)
        self.assertEqual(items[1].timestamp, "6:13 PM")
        self.assertIn("Discord bot", items[2].prompt)

    def test_classify_prompt_intent(self):
        res_skill = classify_prompt_intent("Can you come up with a plan for a remote control skill?")
        self.assertEqual(res_skill["type"], "skill")
        self.assertEqual(res_skill["recommended_name"], "remote-control-skill")

        res_handoff = classify_prompt_intent("Generate a prompt to Handoff to a coding agent")
        self.assertEqual(res_handoff["type"], "prompt_tool")
        self.assertEqual(res_handoff["recommended_name"], "baton")

        res_bot = classify_prompt_intent("Okay. So, we want to create a Discord bot.Gemini.")
        self.assertEqual(res_bot["type"], "mcp_or_agent_repo")
        self.assertEqual(res_bot["recommended_name"], "discord-voice-gemini")

        res_other = classify_prompt_intent("What is the closest bathroom around my location?")
        self.assertEqual(res_other["type"], "other")
        self.assertIsNone(res_other["recommended_name"])

    def test_deduplicator(self):
        deduper = Deduplicator(workspace_dir="/Users/alejandrolondono/dev", owner="NoJuanNobody")
        self.assertTrue(deduper.is_duplicate("baton"))
        self.assertTrue(deduper.is_duplicate("tin-can"))
        self.assertTrue(deduper.is_duplicate("openhaul"))
        self.assertFalse(deduper.is_duplicate("random-nonexistent-project-xyz123"))

    def test_harvest_and_audit(self):
        result = harvest_and_audit(SAMPLE_ACTIVITY_DUMP, workspace_dir="/Users/alejandrolondono/dev", owner="NoJuanNobody")
        self.assertEqual(result["total_activities_parsed"], 4)
        self.assertEqual(result["total_creation_events"], 3)
        baton_entry = next(i for i in result["items"] if i["recommended_name"] == "baton")
        self.assertTrue(baton_entry["is_duplicate"])

if __name__ == "__main__":
    unittest.main()
