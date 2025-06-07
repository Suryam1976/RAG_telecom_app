import logging
import os
from typing import List, Dict, Any
import httpx

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Document:
    """Simple document class to replace LangChain's Document"""
    def __init__(self, page_content, metadata=None):
        self.page_content = page_content
        self.metadata = metadata or {}

class PlanEmbedder:
    def __init__(self, api_key: str = None):
        """
        Initialize the plan embedder with OpenAI embeddings.
        
        Args:
            api_key (str, optional): OpenAI API key. If None, uses OPENAI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set it directly or via OPENAI_API_KEY env var.")
        
        # Use direct HTTP requests to avoid OpenAI client compatibility issues
        self.api_url = "https://api.openai.com/v1/embeddings"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        self.embeddings = self  # Use self as the embeddings object
        logger.info("Initialized PlanEmbedder with direct OpenAI API calls")
    
    def prepare_plan_documents(self, plans: List[Dict[str, Any]]) -> List[Document]:
        """
        Convert plan dictionaries to Document objects for embedding.
        
        Args:
            plans (list): List of processed plan dictionaries
        
        Returns:
            list: List of Document objects
        """
        logger.info(f"Preparing {len(plans)} plans for embedding")
        documents = []
        
        for plan in plans:
            # Create a detailed text representation of the plan
            text = f"Plan Name: {plan.get('name', 'Unknown')}\n"
            text += f"Provider: {plan.get('provider', 'Unknown')}\n"
            text += f"Price: {plan.get('price', 'Unknown')}\n"
            text += f"Data: {plan.get('data', 'Unknown')}\n"
            
            # Add features
            features = plan.get('features', [])
            if features:
                text += "Features:\n"
                for feature in features:
                    text += f"- {feature}\n"
            
            # Add additional info
            additional_info = plan.get('additional_info', {})
            if additional_info:
                text += "Additional Information:\n"
                for key, value in additional_info.items():
                    text += f"- {key}: {value}\n"
            
            # Add URL
            text += f"More information: {plan.get('url', 'No URL provided')}"
            
            # Create metadata
            metadata = {
                'name': plan.get('name', 'Unknown'),
                'provider': plan.get('provider', 'Unknown'),
                'price': plan.get('price', 'Unknown'),
                'data': plan.get('data', 'Unknown'),
                'url': plan.get('url', 'No URL provided'),
                'source': 'plan_details'
            }
            
            # Create document
            doc = Document(page_content=text, metadata=metadata)
            documents.append(doc)
        
        logger.info(f"Created {len(documents)} documents")
        return documents
    
    def embed_query(self, text: str) -> List[float]:
        """
        Get embedding for a single text using direct OpenAI API calls.
        
        Args:
            text (str): Text to embed
        
        Returns:
            list: Embedding vector
        """
        try:
            import requests
            
            data = {
                "model": "text-embedding-ada-002",
                "input": text
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            return result["data"][0]["embedding"]
            
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            raise
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for multiple texts using direct OpenAI API calls.
        
        Args:
            texts (list): List of texts to embed
        
        Returns:
            list: List of embedding vectors
        """
        try:
            import requests
            
            # Process in batches to avoid token limits
            batch_size = 20
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                
                data = {
                    "model": "text-embedding-ada-002",
                    "input": batch_texts
                }
                
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=data,
                    timeout=60
                )
                response.raise_for_status()
                
                result = response.json()
                batch_embeddings = [item["embedding"] for item in result["data"]]
                all_embeddings.extend(batch_embeddings)
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Error getting embeddings: {str(e)}")
            raise

