import logging
import time
import asyncio
from typing import Dict, Any, Optional, List
from playwright.async_api import async_playwright
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PlanCrawler:
    def __init__(self, headless: bool = True, timeout: int = 30):
        """
        Initialize the plan crawler.
        
        Args:
            headless: Whether to run the browser in headless mode
            timeout: Timeout for page loading in seconds
        """
        self.headless = headless
        self.timeout = timeout * 1000  # Convert to milliseconds for Playwright
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        logger.info(f"Initialized PlanCrawler (headless={headless}, timeout={timeout}s)")
    
    def crawl_provider(self, provider: str) -> Optional[str]:
        """
        Crawl a telecom provider's website to get plan information.
        
        Args:
            provider: Name of the telecom provider
            
        Returns:
            HTML content of the provider's plans page, or None if failed
        """
        logger.info(f"Crawling provider: {provider}")
        
        # Map provider names to URLs and methods
        provider_configs = {
            "Verizon": {
                "url": "https://www.verizon.com/plans/unlimited/",
                "method": "playwright",
                "wait_for": ".plan-card, .plan-tile, [data-testid*='plan']"
            },
            "AT&T": {
                "url": "https://www.att.com/plans/unlimited-data-plans/",
                "method": "requests",
                "wait_for": None
            },
            "T-Mobile": {
                "url": "https://www.t-mobile.com/cell-phone-plans",
                "method": "requests",
                "wait_for": None
            }
        }
        
        if provider not in provider_configs:
            logger.error(f"Unknown provider: {provider}. Supported: {list(provider_configs.keys())}")
            return None
        
        config = provider_configs[provider]
        
        try:
            if config["method"] == "playwright":
                return asyncio.run(self._crawl_with_playwright(config["url"], config.get("wait_for")))
            else:
                return self._crawl_with_requests(config["url"])
        except Exception as e:
            logger.error(f"Error crawling {provider}: {str(e)}")
            return None
    
    async def _crawl_with_playwright(self, url: str, wait_for_selector: str = None) -> Optional[str]:
        """
        Crawl using Playwright for dynamic content.
        
        Args:
            url: URL to crawl
            wait_for_selector: CSS selector to wait for before extracting content
            
        Returns:
            HTML content or None if failed
        """
        logger.info(f"Using Playwright to crawl: {url}")
        
        try:
            async with async_playwright() as p:
                # Launch browser
                browser = await p.chromium.launch(
                    headless=self.headless,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                
                # Create context with user agent
                context = await browser.new_context(
                    user_agent=self.user_agent,
                    viewport={'width': 1920, 'height': 1080}
                )
                
                # Create page
                page = await context.new_page()
                
                # Set timeout
                page.set_default_timeout(self.timeout)
                
                # Navigate to page
                logger.info(f"Navigating to {url}")
                await page.goto(url, wait_until='networkidle')
                
                # Wait for specific content if specified
                if wait_for_selector:
                    logger.info(f"Waiting for selector: {wait_for_selector}")
                    try:
                        await page.wait_for_selector(wait_for_selector, timeout=10000)
                    except Exception as e:
                        logger.warning(f"Selector not found, continuing anyway: {e}")
                
                # Wait a bit more for dynamic content
                await page.wait_for_timeout(3000)
                
                # Get page content
                content = await page.content()
                
                # Close browser
                await browser.close()
                
                logger.info(f"Successfully crawled {len(content)} characters")
                return content
                
        except Exception as e:
            logger.error(f"Playwright crawling failed: {str(e)}")
            return None
    
    def _crawl_with_requests(self, url: str) -> Optional[str]:
        """
        Crawl using requests for static content.
        
        Args:
            url: URL to crawl
            
        Returns:
            HTML content or None if failed
        """
        logger.info(f"Using requests to crawl: {url}")
        
        try:
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            logger.info(f"Successfully crawled {len(response.text)} characters")
            return response.text
            
        except Exception as e:
            logger.error(f"Requests crawling failed: {str(e)}")
            return None
    
    def get_plan_urls(self, provider: str, html_content: str) -> List[str]:
        """
        Extract individual plan URLs from the main plans page.
        
        Args:
            provider: Provider name
            html_content: HTML content of the main plans page
            
        Returns:
            List of plan URLs
        """
        logger.info(f"Extracting plan URLs for {provider}")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        plan_urls = []
        
        try:
            if provider == "Verizon":
                # Look for plan links in Verizon's structure
                plan_links = soup.find_all('a', href=True)
                for link in plan_links:
                    href = link.get('href', '')
                    if '/plans/' in href and ('unlimited' in href.lower() or 'prepaid' in href.lower()):
                        if href.startswith('/'):
                            href = 'https://www.verizon.com' + href
                        if href not in plan_urls:
                            plan_urls.append(href)
            
            logger.info(f"Found {len(plan_urls)} plan URLs")
            return plan_urls[:10]  # Limit to first 10 to avoid overwhelming
            
        except Exception as e:
            logger.error(f"Error extracting plan URLs: {str(e)}")
            return []
