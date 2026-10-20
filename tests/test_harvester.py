import unittest
import sys
import os

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gemini_activity_harvester.parser import parse_activity_dump, classify_prompt_intent
from gemini_activity_harvester.dedupe import Deduplicator
from gemini_activity_harvester.core import harvest_and_audit
from gemini_activity_harvester.scraper import parse_dialog_text

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

SAMPLE_DIALOG_TEXT = """Item details
more_vert
close
Gemini Apps
Prompted Create a custom skill that defines the interaction between the conversational interface and autonomous background agents
Audio included.
Details
event
Today at 10:18 PM
apps
Gemini Apps
https://gemini.google.com/app/dab487a9895d6b65
chat

I've created and activated your custom skill, background-agent-orchestration.

Why this activity?

This activity was saved to your Google Account.
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

        res_bg = classify_prompt_intent("Create a custom skill for conversational interface and autonomous background agents")
        self.assertEqual(res_bg["type"], "skill")
        self.assertEqual(res_bg["recommended_name"], "background-agent-orchestration")

        res_edge = classify_prompt_intent("Create a skill incorporating local AI edge agents and graph loop pipelines")
        self.assertEqual(res_edge["type"], "skill")
        self.assertEqual(res_edge["recommended_name"], "edge-agent-creative-pipeline")

        res_tmux = classify_prompt_intent("Create a startup command that uses tmux to create eight cloud code sessions with dangerously skip permissions")
        self.assertEqual(res_tmux["type"], "skill")
        self.assertEqual(res_tmux["recommended_name"], "tmux-agent-fleet")

        res_vault = classify_prompt_intent("I want to host an Obsidian vault in the cloud and put an API paywall over it")
        self.assertEqual(res_vault["type"], "mcp_or_agent_repo")
        self.assertEqual(res_vault["recommended_name"], "vault-graphrag-paywall")

        res_lex = classify_prompt_intent("I want to create lexigraphical taxonomy for all of the domains and graphic engineering")
        self.assertEqual(res_lex["type"], "skill")
        self.assertEqual(res_lex["recommended_name"], "multi-domain-lexicon")

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

    def test_parse_dialog_text(self):
        parsed = parse_dialog_text(SAMPLE_DIALOG_TEXT)
        self.assertIn("Create a custom skill", parsed["full_prompt"])
        self.assertEqual(parsed["chat_url"], "https://gemini.google.com/app/dab487a9895d6b65")
        self.assertIn("Today at 10:18 PM", parsed["timestamp"])
        self.assertIn("background-agent-orchestration", parsed["model_response"])

if __name__ == "__main__":
    unittest.main()
