# Updated System Architecture & Flow Documentation

## 🏗️ **Current Architecture Overview**

The Telecom RAG Planning & Reasoning Agent has been significantly updated to use direct API calls and eliminate dependency conflicts. Here's the current system architecture:

```mermaid
graph TB
    subgraph "🌐 External APIs"
        OpenAI[OpenAI Embeddings API<br/>text-embedding-ada-002]
        Groq[Groq LLM API<br/>llama3-8b-8192]
        Verizon[Verizon Website<br/>Plans Data]
    end
    
    subgraph "📱 User Interface"
        Streamlit[Streamlit Web App<br/>- Data Source Selection<br/>- Query Input<br/>- Results Display]
    end
    
    subgraph "🕸️ Web Scraping Layer"
        Crawler[PlanCrawler<br/>- Playwright Browser<br/>- Requests Fallback<br/>- Anti-bot Handling]
        Extractor[PlanExtractor<br/>- CSS Selectors<br/>- Pattern Matching<br/>- Data Validation]
        Processor[DataProcessor<br/>- Data Cleaning<br/>- Normalization<br/>- Caching]
    end
    
    subgraph "📚 Knowledge Base"
        Embedder[PlanEmbedder<br/>- Direct API Calls<br/>- Batch Processing<br/>- Error Handling]
        VectorDB[(ChromaDB<br/>- Persistent Storage<br/>- Cosine Similarity<br/>- Provider Filtering)]
    end
    
    subgraph "🤖 AI Agent"
        Parser[QueryParser<br/>- Direct Groq API<br/>- JSON Parsing<br/>- Parameter Extraction]
        Planner[SimplePlanner<br/>- Semantic Search<br/>- LLM Ranking<br/>- Multi-criteria Analysis]
        Generator[ResponseGenerator<br/>- Natural Language<br/>- Contextual Responses<br/>- Conversational Tone]
    end
    
    subgraph "💾 Data Storage"
        Cache[File Cache<br/>- JSON Storage<br/>- Timestamped Data<br/>- Provider Separation]
        ChromaFiles[ChromaDB Files<br/>- Vector Index<br/>- Metadata<br/>- Persistence]
    end
    
    %% User Interactions
    Streamlit --> Parser
    Parser --> Planner
    Planner --> Generator
    Generator --> Streamlit
    
    %% Data Flow
    Verizon --> Crawler
    Crawler --> Extractor
    Extractor --> Processor
    Processor --> Cache
    Processor --> Embedder
    Embedder --> VectorDB
    VectorDB --> Planner
    
    %% API Calls
    Embedder -.->|HTTPS POST| OpenAI
    Parser -.->|HTTPS POST| Groq
    Planner -.->|HTTPS POST| Groq
    Generator -.->|HTTPS POST| Groq
    
    %% Storage
    VectorDB --> ChromaFiles
    Cache --> ChromaFiles
    
    classDef api fill:#e1f5fe,stroke:#0277bd,stroke-width:2px
    classDef scraper fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef knowledge fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef agent fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef storage fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef ui fill:#f1f8e9,stroke:#689f38,stroke-width:2px
    
    class OpenAI,Groq,Verizon api
    class Crawler,Extractor,Processor scraper
    class Embedder,VectorDB knowledge
    class Parser,Planner,Generator agent
    class Cache,ChromaFiles storage
    class Streamlit ui
```

## 🔄 **Updated Data Flow Diagram**

```mermaid
sequenceDiagram
    participant U as User
    participant S as Streamlit UI
    participant QP as QueryParser
    participant VS as VectorStore
    participant PL as Planner
    participant RG as ResponseGenerator
    participant E as Embedder
    participant OAI as OpenAI API
    participant GA as Groq API
    participant WS as Web Scraper
    participant VZ as Verizon Website
    
    Note over U,VZ: Data Ingestion Phase
    U->>S: Select "Live Scraping"
    S->>WS: Trigger scraping for Verizon
    WS->>VZ: Playwright browser automation
    VZ-->>WS: HTML content
    WS->>E: Processed plan data
    E->>OAI: POST /v1/embeddings (batch)
    OAI-->>E: Embedding vectors
    E->>VS: Store documents + vectors
    
    Note over U,GA: Query Processing Phase
    U->>S: "I need unlimited data plan"
    S->>QP: Parse natural language query
    QP->>GA: POST /chat/completions
    GA-->>QP: Structured parameters JSON
    
    Note over QP,GA: Recommendation Phase
    QP->>PL: Parsed query parameters
    PL->>E: Generate query embedding
    E->>OAI: POST /v1/embeddings (single)
    OAI-->>E: Query vector
    PL->>VS: Similarity search
    VS-->>PL: Relevant plan documents
    PL->>GA: Rank plans with context
    GA-->>PL: Scored recommendations
    
    Note over PL,S: Response Generation Phase
    PL->>RG: Query + ranked plans
    RG->>GA: Generate natural response
    GA-->>RG: Conversational response
    RG->>S: Final recommendation
    S->>U: Display results + explanations
```

## 📋 **Architecture Components (Updated)**

### **1. Web Scraping Layer** 🕸️

#### **PlanCrawler** (Updated)
```python
# Current Implementation Highlights:
- Playwright for dynamic content (Verizon)
- Requests fallback for static sites
- Provider-specific configurations
- Anti-bot measures and timeouts
- Comprehensive error handling
```

**Key Features:**
- ✅ Asynchronous Playwright execution
- ✅ Multiple user agents and headers
- ✅ Configurable timeouts and retries
- ✅ Provider-specific scraping strategies

#### **PlanExtractor** (Enhanced)
```python
# Advanced Extraction Capabilities:
- Multiple CSS selector strategies
- Pattern-based text extraction
- Fallback parsing methods
- Robust data validation
```

**Extraction Strategy:**
1. **Primary**: CSS selectors for structured data
2. **Secondary**: Pattern matching for unstructured text
3. **Fallback**: Known plan name recognition

#### **DataProcessor** (Comprehensive)
```python
# Complete Pipeline:
- Data normalization and cleaning
- Price standardization ($XX/month)
- Feature deduplication
- JSON-based caching with timestamps
- Provider-specific data management
```

### **2. Knowledge Base Layer** 📚

#### **PlanEmbedder** (Rewritten)
```python
# Direct API Implementation:
- No OpenAI client dependency
- Direct HTTPS POST requests
- Batch processing (20 documents/request)
- Comprehensive error handling
- Timeout management
```

**API Call Structure:**
```json
{
  "model": "text-embedding-ada-002",
  "input": ["Plan text 1", "Plan text 2", "..."]
}
```

#### **VectorStore** (Enhanced)
```python
# ChromaDB Integration:
- PersistentClient with fallback
- Batch document processing
- Provider-based filtering
- Collection statistics
- Robust error handling
```

**Storage Features:**
- ✅ Persistent storage with automatic fallback
- ✅ Provider-based document management
- ✅ Efficient similarity search
- ✅ Collection statistics and monitoring

### **3. AI Agent Layer** 🤖

#### **QueryParser** (Direct API)
```python
# Groq API Integration:
- Direct HTTPS POST to Groq
- JSON-structured prompt templates
- Parameter extraction and validation
- Fallback to default values
```

**Query Processing:**
```json
{
  "budget": "under $80",
  "data_needs": "unlimited",
  "users": 1,
  "features": ["5G", "hotspot"],
  "primary_concern": "data"
}
```

#### **SimplePlanner** (LLM-Powered)
```python
# Advanced Planning:
- Semantic similarity search
- LLM-based plan ranking
- Multi-criteria decision making
- Detailed reasoning and explanations
```

**Ranking Output:**
```json
[
  {
    "plan_name": "5G Get More",
    "provider": "Verizon",
    "score": 8.5,
    "reasoning": "Excellent match for unlimited data needs...",
    "pros": ["30GB hotspot", "Premium features"],
    "cons": ["Higher price point"]
  }
]
```

#### **ResponseGenerator** (Conversational)
```python
# Natural Language Generation:
- Context-aware responses
- Conversational tone
- Detailed explanations
- Follow-up questions
```

## 🔧 **Technical Implementation Details**

### **API Integration Patterns**

#### **OpenAI Embeddings** (Direct)
```python
def embed_documents(self, texts: List[str]) -> List[List[float]]:
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        response = requests.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": "text-embedding-ada-002", "input": batch_texts}
        )
        # Process response...
```

#### **Groq LLM** (Direct)
```python
def generate_response(self, prompt: str) -> str:
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "llama3-8b-8192",
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    # Process response...
```

### **Data Flow Mechanisms**

#### **Caching Strategy**
```python
# File-based caching with timestamps
{
  "provider": "Verizon",
  "scraped_at": "2025-06-07T19:30:00",
  "plan_count": 4,
  "plans": [...]
}
```

#### **Vector Storage**
```python
# ChromaDB with metadata filtering
collection.add(
    embeddings=embeddings,
    documents=texts,
    metadatas=[{"provider": "Verizon", "name": "5G Get More"}],
    ids=["doc_20250607_193000_0"]
)
```

## 🎯 **Key Architecture Changes**

### **Eliminated Dependencies** ❌
- **LangChain**: Removed all LangChain imports and dependencies
- **OpenAI Client**: Replaced with direct API calls
- **Complex Chains**: Simplified to direct function calls

### **Added Direct Integrations** ✅
- **OpenAI Embeddings**: Direct HTTPS API calls
- **Groq LLM**: Direct HTTPS API calls  
- **ChromaDB**: Persistent client with fallback
- **Web Scraping**: Playwright + Requests hybrid

### **Enhanced Features** 🚀
- **Batch Processing**: Efficient embedding generation
- **Error Handling**: Comprehensive error recovery
- **Caching**: File-based data persistence
- **Monitoring**: Collection statistics and logging

## 📊 **Performance Characteristics**

### **Latency Breakdown**
- **Web Scraping**: 5-15 seconds (Verizon full site)
- **Embedding Generation**: 1-3 seconds (batch of 20)
- **Vector Search**: <100ms (5 results)
- **LLM Processing**: 1-2 seconds (Groq)
- **Total Query Time**: 2-5 seconds (cached data)

### **Scalability Features**
- **Batch Processing**: Handles large document sets
- **Provider Isolation**: Independent data management
- **Fallback Mechanisms**: Graceful degradation
- **Memory Management**: Efficient resource usage

## 🛠️ **Deployment Architecture**

### **Production Deployment**
```yaml
Services:
  - Streamlit App (Port 8501)
  - ChromaDB Persistent Storage
  - File Cache Directory
  - Log Management

External Dependencies:
  - OpenAI API (Embeddings)
  - Groq API (LLM Processing)
  - Target Websites (Scraping)

Storage Requirements:
  - ChromaDB: ~100MB per 1000 plans
  - File Cache: ~10MB per provider
  - Logs: ~1MB per day
```

### **Environment Variables**
```bash
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...
LOG_LEVEL=INFO
CHROMA_PERSIST_DIRECTORY=./chroma_db
CACHE_DIRECTORY=./scraped_data
```

## 🔄 **Data Refresh Strategy**

### **Update Mechanisms**
1. **Manual Refresh**: User-triggered via UI
2. **Scheduled Updates**: Planned for production
3. **Cache Validation**: Timestamp-based freshness
4. **Fallback Data**: Sample plans when scraping fails

### **Data Consistency**
- **Vector Store**: Provider-based document management
- **File Cache**: Timestamped JSON files
- **Error Recovery**: Graceful fallback to cached data

This updated architecture provides a robust, scalable, and maintainable foundation for the Telecom RAG system with direct API control and comprehensive error handling.
