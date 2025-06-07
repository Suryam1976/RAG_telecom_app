# Mini POC Vision: Telecom Plan Advisor

## Overview
A focused proof-of-concept that demonstrates the core capabilities of the Telecom RAG Planning & Reasoning Agent by scraping a single telecom provider's website, building a simple knowledge base, and creating a basic AI agent that can answer queries and make recommendations about telecom plans.

## Scope
- Single telecom provider (e.g., AT&T, Verizon, or T-Mobile)
- Limited to consumer mobile plans only
- Basic recommendation capabilities for individual users
- Simple web interface for demonstration

## Core Components

### 1. Web Scraper
- Targeted scraping of plan pages, pricing, and features
- Basic data extraction and structuring
- Manual trigger for updates (no real-time monitoring)

### 2. Knowledge Base
- Simple vector database implementation
- Basic embedding generation
- Limited to plan details and common FAQs

### 3. Query Engine
- Basic intent recognition for plan questions
- Simple parameter extraction (budget, data needs, etc.)
- Retrieval of relevant plan information

### 4. Recommendation System
- Rule-based recommendation logic
- Simple comparison between 3-5 plans
- Basic explanation of recommendations

### 5. Demo Interface
- Streamlit web application
- Text input for queries
- Formatted display of recommendations

## Two-Week Timeline

### Week 1: Data & Knowledge Base
- Day 1-2: Set up scraper for telecom website
- Day 3-4: Extract and structure plan data
- Day 5: Implement vector embeddings and storage

### Week 2: Agent & Interface
- Day 6-7: Build query understanding and retrieval
- Day 8-9: Implement recommendation logic
- Day 10: Create Streamlit interface and demo

## Success Criteria
1. Successfully scrape and structure data from telecom website
2. Answer basic questions about available plans
3. Provide simple recommendations based on user requirements
4. Demonstrate end-to-end flow in a working demo