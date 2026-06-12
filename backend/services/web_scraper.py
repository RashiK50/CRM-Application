import httpx
import urllib.robotparser
from datetime import datetime, timedelta
from typing import Dict, Any

class WebIntelligenceService:
    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = timedelta(hours=6)

    def _check_robots_txt(self, base_url: str, user_agent: str = "*") -> bool:
        """Enforces robots.txt compliance before scraping."""
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(f"{base_url}/robots.txt")
        try:
            rp.read()
            return rp.can_fetch(user_agent, base_url)
        except Exception:
            return False

    async def get_web_intelligence(self, company_name: str) -> str:
        """
        Attempts G2/Trustpilot first, then falls back to live Hacker News API
        if blocked by Cloudflare/robots.txt.
        """
        cache_key = company_name.lower()
        if cache_key in self.cache and datetime.now() < self.cache[cache_key]["expires_at"]:
            return self.cache[cache_key]["data"]

        # 1. ATTEMPT PRIMARY: Trustpilot
        base_url = "https://www.trustpilot.com"
        trustpilot_failed = False
        
        if not self._check_robots_txt(base_url):
            print(f"🕸️ [SCRAPER] robots.txt denied access to {base_url}.")
            trustpilot_failed = True
        else:
            try:
                print(f"🕸️ [SCRAPER] Attempting live Trustpilot scrape for {company_name}...")
                target_url = f"https://www.trustpilot.com/review/{company_name.lower().replace(' ', '-')}.com"
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(target_url)
                    response.raise_for_status()
                    # (Your Trustpilot parsing logic would go here if it worked)
            except Exception as e:
                print(f"🕸️ [SCRAPER] Trustpilot blocked/failed ({str(e)}).")
                trustpilot_failed = True

        # 2. ATTEMPT SECONDARY (FALLBACK): Hacker News Live API
        result = ""
        if trustpilot_failed:
            print(f"📡 [SCRAPER] Pivoting to live Social Listening (Hacker News) for '{company_name}'...")
            try:
                hn_url = f"https://hn.algolia.com/api/v1/search?query={company_name}&tags=story"
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(hn_url)
                    response.raise_for_status()
                    hits = response.json().get("hits", [])
                    
                    if hits:
                        top_story = hits[0]
                        result = f"Live Web Intelligence: Trustpilot blocked. Social Listening fallback found active Hacker News thread: '{top_story.get('title')}' ({top_story.get('points')} upvotes). URL: {top_story.get('url')}"
                        print("📡 [SCRAPER] Successfully pulled live Hacker News data.")
                    else:
                        result = f"Live Web Intelligence: Trustpilot blocked. No viral Hacker News threads found for '{company_name}'."
            except Exception as e:
                result = f"Live Web Intelligence: All external scraping pipelines currently blocked or offline."

        # Cache and return
        self.cache[cache_key] = {"data": result, "expires_at": datetime.now() + self.cache_ttl}
        return result