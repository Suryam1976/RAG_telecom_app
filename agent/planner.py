import logging
import json
from typing import Dict, Any, List, Optional
import requests
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimplePlanner:
    def __init__(self, vector_store, api_key: str = None):
        """
        Initialize the planner with a vector store and Groq API.
        
        Args:
            vector_store: Vector store containing plan embeddings
            api_key (str, optional): Groq API key
        """
        self.vector_store = vector_store
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key is required. Set it directly or via GROQ_API_KEY env var.")
        
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama3-8b-8192"
        
        # Prompt for ranking plans
        self.ranking_prompt_template = """
You are a telecom plan recommendation expert. Based on the user's requirements and the available plans, 
rank the plans from most suitable to least suitable.

User requirements:
- Budget: {budget}
- Data needs: {data_needs}
- Number of users/lines: {users}
- Desired features: {features}
- Primary concern: {primary_concern}

Available plans:
{retrieved_plans}

For each plan, provide:
1. A suitability score from 1-10 (10 being perfect match)
2. Brief reasoning for the score
3. Pros and cons relative to the user's requirements

Format your response as a JSON array of objects, sorted by suitability score in descending order:
[
    {{
        "plan_name": "Plan Name",
        "provider": "Provider Name",
        "score": 8.5,
        "reasoning": "This plan is a good match because...",
        "pros": ["Pro 1", "Pro 2", ...],
        "cons": ["Con 1", "Con 2", ...]
    }},
    ...
]

Only return the JSON array, nothing else.
"""
        
        logger.info("Initialized SimplePlanner with Groq API")
    
    def get_recommendations(self, parsed_query: Dict[str, Any], k: int = 5) -> Dict[str, Any]:
        """
        Generate plan recommendations based on parsed query.
        
        Args:
            parsed_query (dict): Structured representation of the query
            k (int): Number of plans to retrieve
            
        Returns:
            dict: Recommendations with ranked plans and reasoning
        """
        logger.info(f"Generating recommendations for query: {parsed_query}")
        
        # Create a search query based on parsed parameters
        search_query = self._build_search_query(parsed_query)
        
        # Retrieve relevant plans
        retrieved_docs = self.vector_store.similarity_search(search_query, k=k)
        
        # Format retrieved plans for the LLM
        plans_text = self._format_plans_for_llm(retrieved_docs)
        
        # Rank plans using LLM reasoning
        ranked_plans = self._rank_plans(parsed_query, plans_text)
        
        return {
            "query": parsed_query,
            "search_query": search_query,
            "retrieved_docs": retrieved_docs,
            "ranked_plans": ranked_plans
        }
    
    def _build_search_query(self, parsed_query: Dict[str, Any]) -> str:
        """Build a search query from parsed parameters"""
        query_parts = []
        
        if parsed_query.get("data_needs"):
            query_parts.append(f"plan with {parsed_query['data_needs']} data")
        
        if parsed_query.get("budget"):
            query_parts.append(f"budget {parsed_query['budget']}")
        
        if parsed_query.get("users") and parsed_query["users"] > 1:
            query_parts.append(f"for {parsed_query['users']} users")
        
        features = parsed_query.get("features", [])
        if features:
            query_parts.append(f"with features: {', '.join(features)}")
        
        if parsed_query.get("primary_concern"):
            query_parts.append(f"optimized for {parsed_query['primary_concern']}")
        
        search_query = " ".join(query_parts)
        if not search_query:
            search_query = "mobile plan"
        
        logger.info(f"Built search query: {search_query}")
        return search_query
    
    def _format_plans_for_llm(self, docs: List[Any]) -> str:
        """Format retrieved documents for LLM input"""
        plans_text = ""
        
        for i, doc in enumerate(docs):
            plans_text += f"Plan {i+1}:\n"
            plans_text += f"{doc.page_content}\n\n"
        
        return plans_text
    
    def _rank_plans(self, parsed_query: Dict[str, Any], plans_text: str) -> List[Dict[str, Any]]:
        """Rank plans using LLM reasoning"""
        try:
            # Prepare the API request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Format the prompt
            prompt_content = self.ranking_prompt_template.format(
                budget=parsed_query.get('budget', 'Not specified'),
                data_needs=parsed_query.get('data_needs', 'Not specified'),
                users=parsed_query.get('users', 1),
                features=', '.join(parsed_query.get('features', [])) or 'None specified',
                primary_concern=parsed_query.get('primary_concern', 'Not specified'),
                retrieved_plans=plans_text
            )
            
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt_content
                    }
                ],
                "temperature": 0.2,
                "max_tokens": 1500
            }
            
            # Make API request
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            # Extract response
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            # Parse JSON response
            ranked_plans = json.loads(content)
            
            logger.info(f"Successfully ranked {len(ranked_plans)} plans")
            return ranked_plans
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request error in ranking: {str(e)}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in ranking: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error ranking plans: {str(e)}")
            return []

