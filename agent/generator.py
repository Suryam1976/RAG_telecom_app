import logging
import json
from typing import Dict, Any, List
import requests
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResponseGenerator:
    def __init__(self, api_key: str = None):
        """
        Initialize the response generator with Groq API.
        
        Args:
            api_key (str, optional): Groq API key
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key is required. Set it directly or via GROQ_API_KEY env var.")
        
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama3-8b-8192"
        
        # Prompt for generating responses
        self.response_prompt_template = """
You are a helpful telecom plan advisor assistant. The user has asked:

"{query}"

Based on their needs:
- Budget: {budget}
- Data needs: {data_needs}
- Number of users/lines: {users}
- Desired features: {features}
- Primary concern: {primary_concern}

I've analyzed the available plans and ranked them for the user:
{ranked_plans}

Please provide a helpful, conversational response that:
1. Acknowledges their query
2. Recommends the top 2-3 plans that best match their needs
3. Explains why these plans are recommended (focusing on how they match the user's requirements)
4. Compares the key features and pricing of the recommended plans
5. Asks if they need any clarification or have additional requirements

Keep your response friendly, informative, and concise.
"""
        
        logger.info("Initialized ResponseGenerator with Groq API")
    
    def generate_response(self, query: str, recommendations: Dict[str, Any]) -> str:
        """
        Generate a natural language response with plan recommendations.
        
        Args:
            query (str): Original user query
            recommendations (dict): Recommendations from the planner
            
        Returns:
            str: Natural language response with recommendations
        """
        logger.info(f"Generating response for query: {query}")
        
        try:
            # Format ranked plans for the prompt
            ranked_plans_text = self._format_ranked_plans(recommendations.get("ranked_plans", []))
            
            # Get user requirements from recommendations
            user_query = recommendations.get("query", {})
            
            # Prepare the API request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Format the prompt
            prompt_content = self.response_prompt_template.format(
                query=query,
                budget=user_query.get('budget', 'Not specified'),
                data_needs=user_query.get('data_needs', 'Not specified'),
                users=user_query.get('users', 1),
                features=', '.join(user_query.get('features', [])) or 'None specified',
                primary_concern=user_query.get('primary_concern', 'Not specified'),
                ranked_plans=ranked_plans_text
            )
            
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt_content
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            # Make API request
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            # Extract response
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            logger.info("Successfully generated response")
            return content
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request error: {str(e)}")
            return "I'm sorry, I'm having trouble generating recommendations right now. Please try again later."
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I'm sorry, I couldn't generate recommendations at this time. Please try again later."
    
    def _format_ranked_plans(self, ranked_plans: List[Dict[str, Any]]) -> str:
        """Format ranked plans for the prompt"""
        if not ranked_plans:
            return "No suitable plans found."
        
        plans_text = ""
        for i, plan in enumerate(ranked_plans):
            plans_text += f"Plan {i+1}: {plan.get('plan_name', 'Unknown')} ({plan.get('provider', 'Unknown')})\n"
            plans_text += f"Score: {plan.get('score', 'N/A')}/10\n"
            plans_text += f"Reasoning: {plan.get('reasoning', 'No reasoning provided')}\n"
            
            pros = plan.get('pros', [])
            if pros:
                plans_text += "Pros:\n"
                for pro in pros:
                    plans_text += f"- {pro}\n"
            
            cons = plan.get('cons', [])
            if cons:
                plans_text += "Cons:\n"
                for con in cons:
                    plans_text += f"- {con}\n"
            
            plans_text += "\n"
        
        return plans_text
