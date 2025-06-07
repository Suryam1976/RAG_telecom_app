# Telecom RAG Plan Advisor

A sophisticated AI-powered telecom plan recommendation system that combines web scraping, vector search, and large language models to help users find the perfect mobile plan.

## 🚀 Features

### ✅ **Fully Implemented & Production Ready**
- **Live Web Scraping**: Real-time data extraction from Verizon website using Playwright
- **Advanced AI Processing**: Direct API calls to Groq and OpenAI for optimal performance
- **Vector Search**: ChromaDB-powered semantic search for plan recommendations
- **Multi-Data Sources**: Sample data, live scraping, and cached data options
- **Interactive UI**: Streamlit-based web interface with real-time feedback
- **Zero Dependencies**: No LangChain or complex dependency chains

### 🎯 **AI-Powered Capabilities**
- **Query Understanding**: Natural language processing to extract user requirements
- **Intelligent Ranking**: LLM-based plan scoring and reasoning
- **Contextual Responses**: Generated explanations for recommendations
- **Multi-criteria Analysis**: Budget, data needs, features, and provider preferences

### 📊 **Data Management**
- **Real-time Scraping**: Automated extraction from telecom websites
- **Data Caching**: Local JSON storage for improved performance
- **Vector Database**: Persistent ChromaDB storage with provider filtering
- **Data Processing**: Normalization and cleaning of scraped content

## 🏗️ Current Architecture

```
RAG_app/
├── scraper/          # Web scraping components
│   ├── crawler.py    # ✅ Playwright-based web crawler
│   ├── extractor.py  # ✅ HTML parsing and data extraction
│   └── processor.py  # ✅ Data cleaning and normalization
├── knowledge_base/   # Vector storage and embeddings
│   ├── embedder.py   # ✅ Direct OpenAI API integration
│   └── vector_store.py # ✅ ChromaDB vector operations
├── agent/           # AI reasoning components
│   ├── query_parser.py  # ✅ Direct Groq API for query understanding
│   ├── planner.py      # ✅ Plan recommendation logic
│   └── generator.py    # ✅ Response generation
├── docs/            # Complete documentation
│   ├── architecture/   # System architecture diagrams
│   └── roadmap/       # Project roadmap
├── app.py           # ✅ Streamlit web interface
└── requirements.txt # ✅ Minimal dependencies
```

## 🔧 Installation & Setup

### Prerequisites
- Python 3.8+
- OpenAI API key
- Groq API key (for fast LLM processing)

### Quick Start

#### Option 1: Automated Setup (Windows)
```bash
# Run the setup script
setup.bat
```

#### Option 2: Automated Setup (Linux/Mac)
```bash
# Make script executable and run
chmod +x setup.sh
./setup.sh
```

#### Option 3: Manual Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Create environment file
cp .env.example .env
# Edit .env and add your API keys
```

### Configuration

Create a `.env` file with your API keys:
```env
OPENAI_API_KEY=sk-your_openai_api_key_here
GROQ_API_KEY=gsk_your_groq_api_key_here
```

## 🚀 Running the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## 📱 Usage

### Data Sources
1. **Sample Data**: Pre-loaded Verizon plans for demonstration
2. **Live Scraping**: Real-time data from provider websites
3. **Cached Scraping**: Previously scraped data for faster loading

### Supported Providers
- ✅ **Verizon**: Full scraping implementation
- 🔄 **AT&T**: Framework ready (needs selector configuration)
- 🔄 **T-Mobile**: Framework ready (needs selector configuration)

### Query Examples
- "I need unlimited data with the best 5G coverage"
- "What's the cheapest Verizon plan with hotspot?"
- "Compare plans for a family of 4 with heavy streaming"
- "Which plan includes Disney+ or Netflix?"
- "Best plan for gaming and streaming under $85/month"

## 🛠️ Technical Implementation

### Direct API Integration (No Dependencies)

#### OpenAI Embeddings
```python
# Direct HTTPS POST to OpenAI
response = requests.post(
    "https://api.openai.com/v1/embeddings",
    headers={"Authorization": f"Bearer {api_key}"},
    json={"model": "text-embedding-ada-002", "input": texts}
)
```

#### Groq LLM Processing
```python
# Direct HTTPS POST to Groq
response = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={"Authorization": f"Bearer {api_key}"},
    json={"model": "llama3-8b-8192", "messages": messages}
)
```

#### ChromaDB Vector Storage
```python
# Persistent storage with fallback
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(
    name="telecom_plans",
    metadata={"hnsw:space": "cosine"}
)
```

### Web Scraping Implementation

#### Verizon Scraping
```python
# Playwright for dynamic content
async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)
    page = await browser.new_page()
    await page.goto("https://www.verizon.com/plans/unlimited/")
    content = await page.content()
```

#### Data Processing Pipeline
```python
# Complete pipeline
html_content = crawler.crawl_provider("Verizon")
plans = extractor.extract_plans(html_content, "Verizon")
processed_plans = processor.process_plans(plans)
documents = embedder.prepare_plan_documents(processed_plans)
vector_store.add_documents(documents)
```

## 📊 Performance & Monitoring

### Metrics
- **Scraping Success Rate**: Monitored per provider
- **Vector Search Accuracy**: Semantic similarity scores
- **Response Time**: Query processing performance
- **Cache Hit Rate**: Data freshness vs. speed trade-offs

### Logging
Comprehensive logging throughout the system:
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 🔍 Troubleshooting

### Common Issues

1. **API Keys Missing**
   ```
   Error: OpenAI API key is required
   Solution: Add OPENAI_API_KEY to .env file
   ```

2. **Playwright Installation**
   ```
   Error: Browser not found
   Solution: Run 'playwright install chromium'
   ```

3. **Scraping Failures**
   ```
   Error: No plans found
   Solution: Check internet connection and provider website accessibility
   ```

4. **Memory Issues**
   ```
   Error: ChromaDB connection failed
   Solution: Ensure sufficient disk space and permissions
   ```

### Debug Mode
Set logging level to DEBUG in environment:
```env
LOG_LEVEL=DEBUG
```

## 🚧 Development Status

### ✅ Completed Features
- [x] Web scraping framework with Playwright
- [x] Verizon-specific data extraction
- [x] Direct API integration (OpenAI + Groq)
- [x] Vector database with ChromaDB
- [x] LLM-based query processing
- [x] Plan ranking and recommendation
- [x] Streamlit web interface
- [x] Data caching and persistence
- [x] Multi-provider architecture
- [x] Error handling and logging
- [x] Zero dependency implementation

### 🔄 In Progress
- [ ] AT&T scraping implementation
- [ ] T-Mobile scraping implementation
- [ ] Advanced query understanding
- [ ] User preference learning

### 📋 Future Enhancements
- [ ] Real-time price monitoring
- [ ] Plan change notifications
- [ ] Mobile app interface
- [ ] Multi-language support
- [ ] Advanced analytics dashboard

## 🏆 POC Success Criteria

| Criteria | Status | Implementation |
|----------|--------|----------------|
| ✅ Scrape telecom data | **Complete** | Verizon scraping functional |
| ✅ Answer plan questions | **Complete** | AI-powered Q&A system |
| ✅ Provide recommendations | **Exceeded** | LLM-based ranking with explanations |
| ✅ Working demo | **Complete** | Full Streamlit interface |

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Install development dependencies
4. Make changes with tests
5. Submit pull request

### Code Standards
- Python 3.8+ compatibility
- Type hints for all functions
- Comprehensive logging
- Error handling for all external calls
- Documentation for public APIs

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

## 🙏 Acknowledgments

- **OpenAI** for embeddings and language models
- **Groq** for fast LLM inference
- **ChromaDB** for vector database
- **Playwright** for web scraping
- **Streamlit** for the web interface

---

## 🔧 Architecture Updates (Latest)

### Eliminated Dependencies ❌
- **LangChain**: Removed all LangChain imports and dependencies
- **OpenAI Client**: Replaced with direct API calls
- **Complex Chains**: Simplified to direct function calls

### Added Direct Integrations ✅
- **OpenAI Embeddings**: Direct HTTPS API calls with batch processing
- **Groq LLM**: Direct HTTPS API calls for all language processing
- **ChromaDB**: Persistent client with automatic fallback
- **Web Scraping**: Playwright + Requests hybrid approach

### Enhanced Features 🚀
- **Batch Processing**: Efficient embedding generation (20 docs/request)
- **Error Handling**: Comprehensive error recovery and fallbacks
- **Caching**: File-based data persistence with timestamps
- **Monitoring**: Collection statistics and detailed logging
- **Performance**: Optimized for production deployment

**Built with ❤️ for better telecom plan decisions**
