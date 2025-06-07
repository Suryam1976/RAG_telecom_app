# Mini POC Implementation Guide

## Setup Instructions

### Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Requirements.txt
```
beautifulsoup4==4.12.2
requests==2.31.0
playwright==1.40.0
langchain==0.0.335
openai==1.3.5
chromadb==0.4.18
pydantic==2.5.2
streamlit==1.28.2
python-dotenv==1.0.0
```

## Component Implementation

### 1. Web Scraper

#### `scraper/crawler.py`
```python
from playwright.sync_api import sync_playwright
import time

class PlanCrawler:
    def __init__(self, base_url):
        self.base_url = base_url
        
    def crawl_plan_pages(self):
        """Crawl telecom website to find plan pages"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(self.base_url)
            
            # Navigate to plans section (customize for target website)
            page.click('text=Plans')
            time.sleep(2)
            
            # Extract plan page URLs
            plan_links = page.eval_on_selector_all('a[href*="plan"]', 
                                                 'elements => elements.map(el => el.href)')
            
            browser.close()
            return plan_links
```

#### `scraper/extractor.py`
```python
import requests
from bs4 import BeautifulSoup

class PlanExtractor:
    def extract_plan_details(self, url):
        """Extract plan details from a plan page"""
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract plan details (customize selectors for target website)
        plan = {
            'name': soup.select_one('h1.plan-name').text.strip(),
            'price': soup.select_one('span.plan-price').text.strip(),
            'data': soup.select_one('div.data-amount').text.strip(),
            'features': [li.text.strip() for li in soup.select('ul.features li')],
            'url': url
        }
        
        return plan
```

### 2. Knowledge Base

#### `knowledge_base/embedder.py`
```python
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import json

class PlanEmbedder:
    def __init__(self, api_key):
        self.embeddings = OpenAIEmbeddings(openai_api_key=api_key)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
    
    def prepare_plan_texts(self, plans):
        """Convert plan dictionaries to text chunks for embedding"""
        plan_texts = []
        
        for plan in plans:
            # Create a detailed text representation of the plan
            text = f"Plan Name: {plan['name']}\n"
            text += f"Price: {plan['price']}\n"
            text += f"Data: {plan['data']}\n"
            text += "Features:\n"
            for feature in plan['features']:
                text += f"- {feature}\n"
            text += f"More information: {plan['url']}"
            
            # Add metadata
            metadata = {
                'name': plan['name'],
                'price': plan['price'],
                'data': plan['data'],
                'url': plan['url'],
                'source': 'plan_details'
            }
            
            plan_texts.append({"text": text, "metadata": metadata})
            
        return plan_texts
```

#### `knowledge_base/vector_store.py`
```python
import chromadb
from chromadb.config import Settings

class VectorStore:
    def __init__(self, embedder, persist_directory="./chroma_db"):
        self.embedder = embedder
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory
        ))
        self.collection = self.client.get_or_create_collection("telecom_plans")
    
    def add_plans(self, plan_texts):
        """Add plans to the vector store"""
        for i, item in enumerate(plan_texts):
            text = item["text"]
            metadata = item["metadata"]
            
            # Get embedding
            embedding = self.embedder.embeddings.embed_query(text)
            
            # Add to collection
            self.collection.add(
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata],
                ids=[f"plan_{i}"]
            )
    
    def search(self, query, n_results=3):
        """Search for relevant plans"""
        query_embedding = self.embedder.embeddings.embed_query(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        return results
```

### 3. AI Agent

#### `agent/query_parser.py`
```python
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate

class QueryParser:
    def __init__(self, api_key):
        self.llm = OpenAI(openai_api_key=api_key)
        self.prompt = PromptTemplate(
            input_variables=["query"],
            template="""
            Extract the key information from this telecom plan query:
            
            Query: {query}
            
            Please identify:
            1. Budget constraints (if any)
            2. Data needs (if any)
            3. Number of lines/users (if any)
            4. Special features requested (if any)
            5. Primary concern (price, data, coverage, etc.)
            
            Format as JSON with these fields.
            """
        )
    
    def parse(self, query):
        """Parse the user query to extract key parameters"""
        result = self.llm(self.prompt.format(query=query))
        # In a real implementation, parse the JSON response
        # For simplicity, we'll return a mock structured result
        return {
            "budget": "under $80",
            "data_needs": "unlimited",
            "users": 1,
            "features": ["5G", "hotspot"],
            "primary_concern": "data"
        }
```

#### `agent/planner.py`
```python
class SimplePlanner:
    def __init__(self, vector_store):
        self.vector_store = vector_store
    
    def get_recommendations(self, parsed_query):
        """Generate plan recommendations based on parsed query"""
        # Create a search query based on parsed parameters
        search_query = f"Plan with {parsed_query['data_needs']} data "
        search_query += f"for {parsed_query['users']} user "
        search_query += f"with budget {parsed_query['budget']} "
        search_query += f"including {', '.join(parsed_query['features'])}"
        
        # Retrieve relevant plans
        results = self.vector_store.search(search_query)
        
        # In a real implementation, rank and filter results
        # For simplicity, we'll return the raw results
        return results
```

#### `agent/generator.py`
```python
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate

class ResponseGenerator:
    def __init__(self, api_key):
        self.llm = OpenAI(openai_api_key=api_key)
        self.prompt = PromptTemplate(
            input_variables=["query", "plans", "parsed_query"],
            template="""
            The user has asked: {query}
            
            Based on their needs:
            - Budget: {parsed_query['budget']}
            - Data needs: {parsed_query['data_needs']}
            - Users: {parsed_query['users']}
            - Desired features: {parsed_query['features']}
            - Primary concern: {parsed_query['primary_concern']}
            
            I found these relevant plans:
            {plans}
            
            Please provide a helpful response that:
            1. Recommends the best plan(s) for their needs
            2. Explains why these plans are recommended
            3. Compares key features and pricing
            4. Asks if they need any clarification
            
            Keep the response conversational and helpful.
            """
        )
    
    def generate_response(self, query, plans, parsed_query):
        """Generate a response with recommendations"""
        plans_text = "\n\n".join([p["document"] for p in plans["documents"]])
        response = self.llm(self.prompt.format(
            query=query,
            plans=plans_text,
            parsed_query=parsed_query
        ))
        return response
```

### 4. Demo Interface

#### `app.py`
```python
import streamlit as st
import os
from dotenv import load_dotenv
from scraper.crawler import PlanCrawler
from scraper.extractor import PlanExtractor
from knowledge_base.embedder import PlanEmbedder
from knowledge_base.vector_store import VectorStore
from agent.query_parser import QueryParser
from agent.planner import SimplePlanner
from agent.generator import ResponseGenerator

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialize components
@st.cache_resource
def initialize_components():
    # In a real app, you'd run the scraper separately
    # For demo purposes, we'll assume plans are already scraped
    sample_plans = [
        {
            'name': 'Unlimited Elite',
            'price': '$85/month',
            'data': 'Unlimited',
            'features': ['5G access', 'HD streaming', '40GB hotspot', 'International texting'],
            'url': 'https://example.com/unlimited-elite'
        },
        {
            'name': 'Unlimited Extra',
            'price': '$75/month',
            'data': 'Unlimited',
            'features': ['5G access', 'SD streaming', '15GB hotspot'],
            'url': 'https://example.com/unlimited-extra'
        },
        {
            'name': 'Unlimited Starter',
            'price': '$65/month',
            'data': 'Unlimited',
            'features': ['5G access', 'SD streaming', 'No hotspot'],
            'url': 'https://example.com/unlimited-starter'
        }
    ]
    
    # Set up knowledge base
    embedder = PlanEmbedder(openai_api_key)
    plan_texts = embedder.prepare_plan_texts(sample_plans)
    vector_store = VectorStore(embedder)
    vector_store.add_plans(plan_texts)
    
    # Set up agent components
    query_parser = QueryParser(openai_api_key)
    planner = SimplePlanner(vector_store)
    generator = ResponseGenerator(openai_api_key)
    
    return query_parser, planner, generator

# Streamlit UI
st.title("Telecom Plan Advisor")
st.write("Ask me about mobile plans, and I'll help you find the best option!")

query_parser, planner, generator = initialize_components()

query = st.text_input("Your question:")

if query:
    with st.spinner("Thinking..."):
        # Process query
        parsed_query = query_parser.parse(query)
        recommendations = planner.get_recommendations(parsed_query)
        response = generator.generate_response(query, recommendations, parsed_query)
        
        # Display response
        st.write("### Recommendation")
        st.write(response)
        
        # Display found plans
        st.write("### Available Plans")
        for i, doc in enumerate(recommendations["documents"]):
            with st.expander(f"Plan {i+1}"):
                st.write(doc)
```

## Running the POC
```bash
# Start the Streamlit app
streamlit run app.py
```

## Next Steps After POC
1. Enhance scraper to handle multiple telecom providers
2. Improve query understanding with more sophisticated NLP
3. Add user profiles and preference tracking
4. Implement more advanced recommendation algorithms
5. Develop a more polished user interface