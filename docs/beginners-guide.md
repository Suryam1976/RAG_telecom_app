# Beginner's Guide to Telecom Plan Advisor

This guide will help you set up and run the Telecom Plan Advisor application, which uses AI to recommend telecom plans based on user needs.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Using the Application](#using-the-application)
- [Understanding the Components](#understanding-the-components)
- [Troubleshooting](#troubleshooting)
- [Next Steps](#next-steps)

## Prerequisites

Before you begin, ensure you have:
- Python 3.8 or higher installed
- Git installed (to clone the repository)
- API keys for:
  - OpenAI (for embeddings)
  - Groq (for the Deepseek-r1-distill-llama-70b model)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/telecom-plan-advisor.git
   cd telecom-plan-advisor
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Install Playwright browsers** (for web scraping)
   ```bash
   playwright install
   ```

## Configuration

1. **Create environment file**
   ```bash
   cp .env.example .env
   ```

2. **Edit the .env file** with your API keys
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   GROQ_API_KEY=your_groq_api_key_here
   ```

## Running the Application

Start the Streamlit application:
```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`.

## Using the Application

### Sample Queries for Verizon Plans

1. In the sidebar, make sure "Use sample data" is checked
2. Select "Verizon" from the dropdown menu
3. Try these example queries:

   - "I need a plan with unlimited data and good hotspot capabilities"
   - "What's the best Verizon plan for streaming videos?"
   - "I need a family plan for 4 people with at least 25GB hotspot data"
   - "Which Verizon plan includes Disney+?"
   - "I'm looking for a budget-friendly plan under $70 per month"

### Understanding the Results

The application will:
1. Parse your query to understand your requirements
2. Search for relevant plans in the knowledge base
3. Rank the plans based on how well they match your needs
4. Generate a natural language response with recommendations

The response will include:
- Top recommended plans
- Reasoning for each recommendation
- Comparison of key features
- Follow-up questions to refine recommendations

## Understanding the Components

The application consists of several key components:

### 1. Web Scraper
- **Purpose**: Collects plan data from telecom websites
- **Files**: `scraper/crawler.py`, `scraper/extractor.py`, `scraper/processor.py`
- **Note**: In demo mode, this is bypassed in favor of sample data

### 2. Knowledge Base
- **Purpose**: Stores plan information with vector embeddings for semantic search
- **Files**: `knowledge_base/embedder.py`, `knowledge_base/vector_store.py`
- **Technology**: Uses ChromaDB for vector storage and OpenAI embeddings

### 3. AI Agent
- **Purpose**: Understands queries, finds relevant plans, and generates responses
- **Files**: `agent/query_parser.py`, `agent/planner.py`, `agent/generator.py`
- **Technology**: Uses Deepseek-r1-distill-llama-70b on Groq for reasoning

### 4. Streamlit Interface
- **Purpose**: Provides a user-friendly way to interact with the system
- **File**: `app.py`
- **Features**: Text input, configuration options, and formatted responses

## Troubleshooting

### Common Issues

1. **API Key Errors**
   - **Symptom**: Error messages about invalid API keys
   - **Solution**: Double-check your API keys in the `.env` file

2. **Model Errors with Groq**
   - **Symptom**: Errors about model availability or timeouts
   - **Solution**: Try using a different model by changing the `model_name` parameter in the agent files:
     ```python
     self.llm = Groq(
         api_key=self.api_key,
         model_name="llama2-70b-4096",  # Alternative model
         temperature=0.7,
         max_tokens=2000
     )
     ```

3. **Memory Issues**
   - **Symptom**: Application crashes or becomes unresponsive
   - **Solution**: Reduce the number of sample plans in `app.py`

4. **Browser Automation Errors**
   - **Symptom**: Errors related to Playwright or browser automation
   - **Solution**: Ensure Playwright is installed correctly with `playwright install`

## Next Steps

Once you're comfortable with the basic application:

1. **Customize Sample Data**
   - Add more plans to the `get_sample_plans()` function in `app.py`
   - Include plans from different providers for comparison

2. **Implement Live Scraping**
   - Modify the `PlanCrawler` and `PlanExtractor` classes to work with real telecom websites
   - Create a scheduled job to update plan data regularly

3. **Enhance the AI Agent**
   - Experiment with different prompts in the agent components
   - Add conversation history to enable multi-turn interactions

4. **Extend the UI**
   - Add visualizations for plan comparisons
   - Implement user profiles to save preferences

5. **Deploy the Application**
   - Deploy to Streamlit Cloud for sharing with others
   - Set up a proper database for storing plan information

Happy exploring!