import logging
import json
from typing import Dict, Any, List
import requests
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QueryParser:
    def __init__(self, api_key: str = None):
        """
        Initialize the query parser with Groq API.
        
        Args:
            api_key (str, optional): Groq API key. If None, uses GROQ_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key is required. Set it directly or via GROQ_API_KEY env var.")
        
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama3-8b-8192"
        
        self.prompt_template = """
You are an AI assistant specialized in understanding telecom plan queries.
Extract the key information from this telecom plan query:

Query: {query}

Please identify:
1. Budget constraints (if any)
2. Data needs (if any)
3. Number of lines/users (if any)
4. Special features requested (if any)
5. Primary concern (price, data, coverage, etc.)

Format your response as a JSON object with these fields:
{{
    "budget": "string or null",
    "data_needs": "string or null",
    "users": number or null,
    "features": ["feature1", "feature2", ...],
    "primary_concern": "string or null"
}}

Only return the JSON object, nothing else.
"""
        
        logger.info("Initialized QueryParser with Groq API")
    
    def parse(self, query: str) -> Dict[str, Any]:
        """
        Parse the user query to extract key parameters.
        
        Args:
            query (str): User's natural language query
            
        Returns:
            dict: Structured representation of the query parameters
        """
        logger.info(f"Parsing query: {query}")
        
        try:
            # Prepare the API request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": self.prompt_template.format(query=query)
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 1000
            }
            
            # Make API request
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            # Extract response
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            # Parse JSON response
            parsed_result = json.loads(content)
            
            logger.info(f"Successfully parsed query into structured format")
            return parsed_result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request error: {str(e)}")
            return self._get_default_result()
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            return self._get_default_result()
        except Exception as e:
            logger.error(f"Error parsing query: {str(e)}")
            return self._get_default_result()
    
    def _get_default_result(self) -> Dict[str, Any]:
        """
        Return default values if parsing fails.
        
        Returns:
            dict: Default structured query parameters
        """
        return {
            "budget": None,
            "data_needs": None,
            "users": 1,
            "features": [],
            "primary_concern": "price"
        }


