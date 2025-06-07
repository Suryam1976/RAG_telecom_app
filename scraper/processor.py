import logging
import json
import os
from typing import List, Dict, Any
from datetime import datetime
from scraper.extractor import PlanData
from scraper.crawler import PlanCrawler
from scraper.extractor import PlanExtractor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self):
        """Initialize the data processor."""
        self.crawler = PlanCrawler()
        self.extractor = PlanExtractor()
        logger.info("Initialized DataProcessor")
    
    def scrape_and_process_provider(self, provider: str) -> List[Dict[str, Any]]:
        """
        Scrape and process plans from a telecom provider.
        
        Args:
            provider: Name of the telecom provider
            
        Returns:
            List of processed plan dictionaries
        """
        logger.info(f"Starting scrape and process for {provider}")
        
        try:
            # Step 1: Crawl the provider's website
            html_content = self.crawler.crawl_provider(provider)
            
            if not html_content:
                logger.error(f"Failed to crawl {provider} website")
                return []
            
            logger.info(f"Successfully crawled {len(html_content)} characters from {provider}")
            
            # Step 2: Extract plan data
            plans = self.extractor.extract_plans(html_content, provider)
            
            if not plans:
                logger.warning(f"No plans extracted from {provider}")
                return []
            
            logger.info(f"Extracted {len(plans)} plans from {provider}")
            
            # Step 3: Process the plans
            processed_plans = self.process_plans(plans)
            
            # Step 4: Save the data
            self.save_scraped_data(provider, processed_plans)
            
            return processed_plans
            
        except Exception as e:
            logger.error(f"Error scraping and processing {provider}: {str(e)}")
            return []
    
    def process_plans(self, plans: List[PlanData]) -> List[Dict[str, Any]]:
        """
        Process raw plan data into a standardized format.
        
        Args:
            plans: List of PlanData objects
            
        Returns:
            List of processed plan dictionaries
        """
        logger.info(f"Processing {len(plans)} plans")
        processed_plans = []
        
        for plan in plans:
            try:
                processed_plan = {
                    'name': self.clean_plan_name(plan.name),
                    'price': self.normalize_price(plan.price),
                    'price_numeric': self.extract_numeric_price(plan.price),
                    'data': self.normalize_data(plan.data),
                    'features': self.clean_features(plan.features),
                    'url': plan.url,
                    'provider': plan.provider,
                    'additional_info': plan.additional_info or {},
                    'processed_at': datetime.now().isoformat(),
                    'data_source': 'web_scraping'
                }
                processed_plans.append(processed_plan)
            except Exception as e:
                logger.warning(f"Error processing plan {plan.name}: {str(e)}")
                continue
        
        logger.info(f"Successfully processed {len(processed_plans)} plans")
        return processed_plans
    
    def clean_plan_name(self, name: str) -> str:
        """
        Clean and standardize plan names.
        
        Args:
            name: Raw plan name
            
        Returns:
            Cleaned plan name
        """
        if not name:
            return "Unknown Plan"
        
        # Remove extra whitespace and normalize
        cleaned = ' '.join(name.strip().split())
        
        # Remove common unwanted text
        unwanted_phrases = [
            'Learn more', 'See details', 'View plan', 'Select plan',
            'Starting at', 'From', 'As low as'
        ]
        
        for phrase in unwanted_phrases:
            cleaned = cleaned.replace(phrase, '').strip()
        
        return cleaned[:100]  # Limit length
    
    def normalize_price(self, price: str) -> str:
        """
        Normalize price string to a standard format.
        
        Args:
            price: Price string (e.g., "$75/month")
            
        Returns:
            Normalized price string
        """
        if not price:
            return "Price not available"
        
        # Extract numeric price and format consistently
        numeric_price = self.extract_numeric_price(price)
        
        if numeric_price > 0:
            return f"${numeric_price:.0f}/month"
        else:
            return price  # Return original if we can't parse it
    
    def extract_numeric_price(self, price: str) -> float:
        """
        Extract numeric price value from price string.
        
        Args:
            price: Price string (e.g., "$75/month")
            
        Returns:
            Numeric price as float
        """
        if not price:
            return 0.0
        
        try:
            # Remove currency symbol, '/month', and any other non-numeric characters
            import re
            price_match = re.search(r'(\d+(?:\.\d{2})?)', price.replace('$', '').replace(',', ''))
            if price_match:
                return float(price_match.group(1))
        except (ValueError, AttributeError):
            logger.debug(f"Could not extract numeric price from: {price}")
        
        return 0.0
    
    def normalize_data(self, data: str) -> str:
        """
        Normalize data string to standardized format.
        
        Args:
            data: Data string (e.g., "Unlimited", "10GB")
            
        Returns:
            Normalized data string
        """
        if not data:
            return "Data amount not specified"
        
        data_lower = data.lower().strip()
        
        if "unlimited" in data_lower:
            return "Unlimited"
        
        # Extract numeric value if present
        import re
        match = re.search(r'(\d+(?:\.\d+)?)\s*(gb|mb|tb)', data_lower)
        if match:
            value, unit = match.groups()
            value = float(value)
            
            if unit == 'mb':
                # Convert MB to GB
                gb_value = value / 1000
                return f"{gb_value:.1f}GB"
            elif unit == 'tb':
                # Convert TB to GB
                gb_value = value * 1000
                return f"{gb_value:.0f}GB"
            else:
                return f"{value:.0f}GB"
        
        return data
    
    def clean_features(self, features: List[str]) -> List[str]:
        """
        Clean and standardize feature list.
        
        Args:
            features: List of raw features
            
        Returns:
            List of cleaned features
        """
        if not features:
            return []
        
        cleaned_features = []
        seen_features = set()
        
        for feature in features:
            if not feature or not isinstance(feature, str):
                continue
            
            # Clean the feature
            cleaned = ' '.join(feature.strip().split())
            
            # Skip very short or very long features
            if len(cleaned) < 3 or len(cleaned) > 150:
                continue
            
            # Skip duplicates (case-insensitive)
            if cleaned.lower() not in seen_features:
                cleaned_features.append(cleaned)
                seen_features.add(cleaned.lower())
        
        # Limit to reasonable number of features
        return cleaned_features[:15]
    
    def save_scraped_data(self, provider: str, processed_plans: List[Dict[str, Any]]) -> None:
        """
        Save scraped data to a JSON file for backup and analysis.
        
        Args:
            provider: Provider name
            processed_plans: List of processed plan dictionaries
        """
        try:
            # Create data directory if it doesn't exist
            data_dir = "scraped_data"
            os.makedirs(data_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{data_dir}/{provider.lower().replace(' ', '_')}_{timestamp}.json"
            
            # Save data
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'provider': provider,
                    'scraped_at': datetime.now().isoformat(),
                    'plan_count': len(processed_plans),
                    'plans': processed_plans
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(processed_plans)} plans to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving scraped data: {str(e)}")
    
    def load_scraped_data(self, provider: str) -> List[Dict[str, Any]]:
        """
        Load the most recent scraped data for a provider.
        
        Args:
            provider: Provider name
            
        Returns:
            List of plan dictionaries or empty list if no data found
        """
        try:
            data_dir = "scraped_data"
            if not os.path.exists(data_dir):
                return []
            
            # Find the most recent file for this provider
            provider_files = [
                f for f in os.listdir(data_dir) 
                if f.startswith(provider.lower().replace(' ', '_')) and f.endswith('.json')
            ]
            
            if not provider_files:
                return []
            
            # Get the most recent file
            latest_file = sorted(provider_files)[-1]
            filepath = os.path.join(data_dir, latest_file)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Loaded {len(data.get('plans', []))} plans from {filepath}")
            return data.get('plans', [])
            
        except Exception as e:
            logger.error(f"Error loading scraped data for {provider}: {str(e)}")
            return []
    
    def get_provider_data(self, provider: str, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get provider data, either from cache or by scraping.
        
        Args:
            provider: Provider name
            force_refresh: Whether to force a new scrape even if cached data exists
            
        Returns:
            List of plan dictionaries
        """
        logger.info(f"Getting data for {provider} (force_refresh={force_refresh})")
        
        # Check for cached data first (unless force refresh is requested)
        if not force_refresh:
            cached_data = self.load_scraped_data(provider)
            if cached_data:
                logger.info(f"Using cached data for {provider}")
                return cached_data
        
        # Scrape fresh data
        logger.info(f"Scraping fresh data for {provider}")
        return self.scrape_and_process_provider(provider)
