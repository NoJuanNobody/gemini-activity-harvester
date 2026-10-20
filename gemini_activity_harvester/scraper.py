"""
Browser-based scraper for Google Gemini activity history.
Uses Playwright to automate Chrome and extract conversations from myactivity.google.com/product/gemini
"""

import asyncio
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from playwright.async_api import async_playwright, Page, Browser, BrowserContext


@dataclass
class GeminiActivity:
    """Represents a single Gemini activity/conversation"""
    timestamp: str
    title: str
    content: str
    url: str


class GeminiActivityScraper:
    """Scrapes Gemini activity from myactivity.google.com"""

    def __init__(self, headless: bool = False, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def launch(self):
        """Launch browser"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.timeout)

    async def close(self):
        """Close browser"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()

    async def navigate_to_gemini_activity(self):
        """Navigate to Google MyActivity Gemini section"""
        url = "https://myactivity.google.com/product/gemini"
        print(f"Navigating to {url}...")
        await self.page.goto(url, wait_until="networkidle")
        await asyncio.sleep(2)  # Wait for page to fully load

    async def extract_activity_items(self) -> List[Dict[str, Any]]:
        """Extract all visible activity items from the page"""
        print("Extracting activity items...")

        # Wait for activity items to load
        await self.page.wait_for_selector('[data-item-id], [role="listitem"]', timeout=self.timeout)

        items = []

        # Try to find activity items using common selectors
        item_selectors = [
            'div[data-item-id]',
            'li[role="listitem"]',
            'div[jsname]',
        ]

        for selector in item_selectors:
            elements = await self.page.query_selector_all(selector)
            if elements:
                print(f"Found {len(elements)} items with selector: {selector}")

                for i, element in enumerate(elements):
                    try:
                        # Extract text content
                        text_content = await element.text_content()

                        # Extract timestamp if available
                        timestamp = await self._extract_timestamp(element)

                        # Extract title (usually first line or heading)
                        title = text_content.split('\n')[0][:100] if text_content else "Untitled"

                        item = {
                            "index": i,
                            "timestamp": timestamp or datetime.now().isoformat(),
                            "title": title,
                            "content": text_content or "",
                            "url": self.page.url
                        }

                        # Only add non-empty items
                        if text_content and len(text_content.strip()) > 10:
                            items.append(item)

                    except Exception as e:
                        print(f"Error extracting item {i}: {e}")
                        continue

                break  # Stop after first selector that finds items

        print(f"Extracted {len(items)} activity items")
        return items

    async def _extract_timestamp(self, element) -> Optional[str]:
        """Try to extract timestamp from an element"""
        try:
            # Look for time/date elements
            time_elements = await element.query_selector_all('time, span[data-timestamp], span[aria-label*="201"], span[aria-label*="202"]')

            for time_elem in time_elements:
                timestamp = await time_elem.get_attribute('datetime')
                if timestamp:
                    return timestamp

                aria_label = await time_elem.get_attribute('aria-label')
                if aria_label and any(year in aria_label for year in ['2024', '2025', '2026']):
                    return aria_label

            return None
        except:
            return None

    async def scroll_and_load_more(self, max_scrolls: int = 5):
        """Scroll to load more activities"""
        print(f"Scrolling to load more items (max {max_scrolls} scrolls)...")

        for i in range(max_scrolls):
            # Scroll to bottom
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)

            # Check if we can scroll more
            scroll_height = await self.page.evaluate("document.body.scrollHeight")
            print(f"Scroll {i+1}: Page height = {scroll_height}px")

    async def scrape(self, scroll_count: int = 3) -> List[Dict[str, Any]]:
        """Full scraping pipeline"""
        try:
            await self.launch()
            await self.navigate_to_gemini_activity()
            await self.scroll_and_load_more(max_scrolls=scroll_count)
            items = await self.extract_activity_items()
            return items
        finally:
            await self.close()


async def scrape_gemini_activity(headless: bool = False, scroll_count: int = 3) -> List[Dict[str, Any]]:
    """Convenience function to scrape Gemini activity"""
    scraper = GeminiActivityScraper(headless=headless)
    return await scraper.scrape(scroll_count=scroll_count)


def scrape_gemini_activity_sync(headless: bool = False, scroll_count: int = 3) -> List[Dict[str, Any]]:
    """Synchronous wrapper for scraping"""
    return asyncio.run(scrape_gemini_activity(headless=headless, scroll_count=scroll_count))
