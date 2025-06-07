# Complete System Flow Diagram

## 🎯 **End-to-End User Journey Flow**

```mermaid
flowchart TD
    Start([User Opens App]) --> UI{Streamlit Interface}
    
    UI --> DataChoice{Choose Data Source}
    DataChoice -->|Sample Data| SampleData[Load Sample Plans]
    DataChoice -->|Live Scraping| LiveScrape[Trigger Web Scraping]
    DataChoice -->|Cached Data| CacheCheck[Check Cached Data]
    
    %% Live Scraping Flow
    LiveScrape --> Crawler[PlanCrawler]
    Crawler --> Browser{Use Playwright?}
    Browser -->|Yes| PlaywrightScrape[Playwright Browser Automation]
    Browser -->|No| RequestsScrape[Requests HTTP Client]
    
    PlaywrightScrape --> VerizonSite[Verizon Website]
    RequestsScrape --> VerizonSite
    VerizonSite --> HTMLContent[HTML Content]
    
    HTMLContent --> Extractor[PlanExtractor]
    Extractor --> ParseHTML[Parse with CSS Selectors]
    ParseHTML --> ExtractedData[Plan Data Objects]
    
    ExtractedData --> Processor[DataProcessor]
    Processor --> CleanData[Clean & Normalize Data]
    CleanData --> SaveCache[Save to JSON Cache]
    
    %% Cached Data Flow
    CacheCheck --> CacheExists{Cache Available?}
    CacheExists -->|Yes| LoadCache[Load from JSON Files]
    CacheExists -->|No| LiveScrape
    
    %% Sample Data Flow
    SampleData --> SamplePlans[Hardcoded Verizon Plans]
    
    %% Common Processing Path
    SaveCache --> ProcessedPlans[Processed Plan Data]
    LoadCache --> ProcessedPlans
    SamplePlans --> ProcessedPlans
    
    ProcessedPlans --> Embedder[PlanEmbedder]
    Embedder --> BatchProcess[Batch Process Plans]
    BatchProcess --> OpenAICall[Direct OpenAI API Call]
    OpenAICall --> Embeddings[Text Embeddings]
    
    Embeddings --> VectorStore[ChromaDB Vector Store]
    VectorStore --> StoredDocs[Stored Documents + Vectors]
    
    %% Query Processing Flow
    StoredDocs --> QueryInput[User Query Input]
    QueryInput --> QueryParser[QueryParser]
    QueryParser --> GroqAPI1[Groq API Call - Parse]
    GroqAPI1 --> ParsedQuery[Structured Query Parameters]
    
    ParsedQuery --> Planner[SimplePlanner]
    Planner --> SearchEmbedding[Generate Query Embedding]
    SearchEmbedding --> OpenAICall2[OpenAI API Call - Query]
    OpenAICall2 --> QueryVector[Query Embedding Vector]
    
    QueryVector --> VectorSearch[ChromaDB Similarity Search]
    VectorSearch --> RelevantDocs[Retrieved Relevant Documents]
    
    RelevantDocs --> RankPlans[Rank Plans with LLM]
    RankPlans --> GroqAPI2[Groq API Call - Rank]
    GroqAPI2 --> RankedPlans[Scored Plan Rankings]
    
    RankedPlans --> Generator[ResponseGenerator]
    Generator --> GroqAPI3[Groq API Call - Generate]
    GroqAPI3 --> FinalResponse[Natural Language Response]
    
    FinalResponse --> DisplayResults[Display Results to User]
    DisplayResults --> End([User Sees Recommendations])
    
    %% Error Handling
    Crawler -->|Error| FallbackSample[Fallback to Sample Data]
    OpenAICall -->|Error| EmbedError[Embedding Error]
    GroqAPI1 -->|Error| DefaultParams[Use Default Parameters]
    GroqAPI2 -->|Error| SimpleRank[Basic Ranking]
    GroqAPI3 -->|Error| ErrorResponse[Error Message]
    
    FallbackSample --> SamplePlans
    EmbedError --> RetryEmbed[Retry with Exponential Backoff]
    RetryEmbed --> OpenAICall
    
    %% Styling
    classDef userAction fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef processing fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef apiCall fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef storage fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef error fill:#ffebee,stroke:#d32f2f,stroke-width:2px
    
    class Start,UI,QueryInput,DisplayResults,End userAction
    class Crawler,Extractor,Processor,Embedder,QueryParser,Planner,Generator processing
    class OpenAICall,OpenAICall2,GroqAPI1,GroqAPI2,GroqAPI3 apiCall
    class VectorStore,StoredDocs,SaveCache,LoadCache storage
    class FallbackSample,EmbedError,DefaultParams,SimpleRank,ErrorResponse error
```

## 🔄 **Detailed Component Interaction Flow**

```mermaid
sequenceDiagram
    participant U as User
    participant ST as Streamlit
    participant DP as DataProcessor
    participant CR as Crawler
    participant EX as Extractor
    participant EM as Embedder
    participant VS as VectorStore
    participant QP as QueryParser
    participant PL as Planner
    participant RG as ResponseGenerator
    participant OAI as OpenAI API
    participant GQ as Groq API
    participant VW as Verizon Website
    
    Note over U,VW: 🚀 Application Startup & Data Loading
    U->>ST: Open Application
    ST->>ST: Initialize Components
    ST->>DP: Check for cached data
    DP->>DP: Load from JSON files
    
    alt No Cache Available
        ST->>DP: Trigger live scraping
        DP->>CR: Crawl Verizon
        CR->>VW: Playwright browser automation
        VW-->>CR: HTML content (plans page)
        CR->>EX: Extract plan data
        EX->>EX: Parse with CSS selectors
        EX->>DP: Return PlanData objects
        DP->>DP: Clean and normalize data
        DP->>DP: Save to JSON cache
    end
    
    DP->>EM: Process plans for embedding
    EM->>EM: Create document representations
    
    loop Batch Processing
        EM->>OAI: POST /v1/embeddings (batch)
        OAI-->>EM: Embedding vectors
    end
    
    EM->>VS: Store documents + embeddings
    VS->>VS: Save to ChromaDB
    ST->>U: Display "Ready" status
    
    Note over U,GQ: 💬 Query Processing & Recommendation
    U->>ST: Enter query: "I need unlimited data"
    ST->>QP: Parse natural language
    QP->>GQ: POST /chat/completions
    Note right of GQ: Extract: budget, data_needs,<br/>users, features, concern
    GQ-->>QP: Structured parameters JSON
    
    QP->>PL: Send parsed query
    PL->>EM: Generate query embedding
    EM->>OAI: POST /v1/embeddings (single)
    OAI-->>EM: Query vector
    
    PL->>VS: Similarity search
    VS->>VS: Find relevant documents
    VS-->>PL: Top 5 matching plans
    
    PL->>GQ: Rank plans with context
    Note right of GQ: Score plans 1-10<br/>with reasoning
    GQ-->>PL: Ranked recommendations
    
    PL->>RG: Query + ranked plans
    RG->>GQ: Generate natural response
    Note right of GQ: Create conversational<br/>recommendation
    GQ-->>RG: Natural language response
    
    RG->>ST: Final recommendation
    ST->>U: Display results + explanations
    
    Note over U,ST: 🔍 Additional User Interactions
    U->>ST: Click "Show Collection Stats"
    ST->>VS: Get statistics
    VS-->>ST: Provider counts, total docs
    ST->>U: Display stats in sidebar
    
    U->>ST: Click "Clear Cache"
    ST->>VS: Clear collection
    VS->>VS: Delete all documents
    ST->>U: Show "Cache cleared" message
```

## 📊 **Data State Transitions**

```mermaid
stateDiagram-v2
    [*] --> AppStart
    
    AppStart --> DataSelection: User chooses source
    
    DataSelection --> SampleData: Sample Data
    DataSelection --> CacheCheck: Cached Data
    DataSelection --> LiveScraping: Live Scraping
    
    SampleData --> DataReady: Load hardcoded plans
    
    CacheCheck --> CacheFound: Files exist
    CacheCheck --> LiveScraping: No cache
    CacheFound --> DataReady: Load from JSON
    
    LiveScraping --> Crawling: Start scraper
    Crawling --> Extracting: HTML retrieved
    Extracting --> Processing: Plans extracted
    Processing --> Caching: Data cleaned
    Caching --> DataReady: Cache saved
    
    DataReady --> Embedding: Generate embeddings
    Embedding --> VectorStorage: Store in ChromaDB
    VectorStorage --> QueryReady: Ready for queries
    
    QueryReady --> QueryReceived: User enters query
    QueryReceived --> QueryParsing: Parse with LLM
    QueryParsing --> VectorSearch: Search similar docs
    VectorSearch --> PlanRanking: Rank with LLM
    PlanRanking --> ResponseGen: Generate response
    ResponseGen --> ResultsShown: Display to user
    
    ResultsShown --> QueryReady: New query
    ResultsShown --> DataRefresh: Refresh data
    DataRefresh --> LiveScraping: Re-scrape
    
    note right of LiveScraping
        Playwright automation
        Anti-bot measures
        Error handling
    end note
    
    note right of Embedding
        Batch processing
        OpenAI API calls
        Error retry logic
    end note
    
    note right of QueryParsing
        Groq API calls
        JSON parameter extraction
        Fallback defaults
    end note
```

## 🔧 **Error Handling Flow**

```mermaid
flowchart TD
    Error[Error Detected] --> ErrorType{Error Type?}
    
    ErrorType -->|Scraping Error| ScrapingError[Web Scraping Failed]
    ErrorType -->|Embedding Error| EmbeddingError[OpenAI API Failed]
    ErrorType -->|LLM Error| LLMError[Groq API Failed]
    ErrorType -->|Storage Error| StorageError[ChromaDB Failed]
    
    ScrapingError --> CheckCache{Cache Available?}
    CheckCache -->|Yes| UseCached[Use Cached Data]
    CheckCache -->|No| UseSample[Use Sample Data]
    
    EmbeddingError --> RetryEmbed[Retry with Backoff]
    RetryEmbed --> RetryCount{Retry < 3?}
    RetryCount -->|Yes| EmbeddingRetry[Retry Embedding]
    RetryCount -->|No| EmbedFallback[Skip Embeddings]
    
    LLMError --> LLMFallback{Component?}
    LLMFallback -->|Parser| DefaultParams[Use Default Parameters]
    LLMFallback -->|Planner| SimpleRank[Basic Score Ranking]
    LLMFallback -->|Generator| ErrorMessage[Show Error Message]
    
    StorageError --> MemoryFallback[Use In-Memory Storage]
    MemoryFallback --> WarnUser[Warn User: No Persistence]
    
    UseCached --> DataReady[Data Ready]
    UseSample --> DataReady
    EmbeddingRetry --> DataReady
    EmbedFallback --> LimitedFunction[Limited Functionality]
    DefaultParams --> ContinueFlow[Continue Processing]
    SimpleRank --> ContinueFlow
    ErrorMessage --> UserNotified[User Informed]
    WarnUser --> DataReady
    
    DataReady --> Resume[Resume Normal Operation]
    ContinueFlow --> Resume
    LimitedFunction --> Resume
    UserNotified --> Resume
    
    classDef error fill:#ffebee,stroke:#d32f2f,stroke-width:2px
    classDef fallback fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef success fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    
    class Error,ScrapingError,EmbeddingError,LLMError,StorageError error
    class UseCached,UseSample,RetryEmbed,DefaultParams,SimpleRank,MemoryFallback fallback
    class DataReady,Resume,ContinueFlow success
```

## 🎯 **Key Architectural Improvements**

### **Eliminated Complex Dependencies**
- ❌ **LangChain**: Removed 15+ dependency packages
- ❌ **OpenAI Client**: Eliminated httpx/proxies conflicts  
- ❌ **Complex Chains**: Simplified to direct function calls

### **Enhanced Reliability**
- ✅ **Direct API Control**: Full control over HTTP requests
- ✅ **Comprehensive Error Handling**: Graceful degradation at every level
- ✅ **Multiple Fallback Strategies**: Sample data, cached data, retry logic
- ✅ **Robust Data Pipeline**: Validation and cleaning at each step

### **Improved Performance**
- ✅ **Batch Processing**: Efficient embedding generation
- ✅ **Persistent Storage**: ChromaDB with automatic fallback
- ✅ **Smart Caching**: Timestamp-based data freshness
- ✅ **Resource Management**: Memory-efficient processing

### **Production Ready**
- ✅ **Monitoring**: Comprehensive logging and statistics
- ✅ **Configuration**: Environment-based settings
- ✅ **Scalability**: Provider-independent architecture
- ✅ **Maintainability**: Clear separation of concerns

This updated architecture provides a robust foundation for the Telecom RAG system with direct API control, comprehensive error handling, and production-ready features.
