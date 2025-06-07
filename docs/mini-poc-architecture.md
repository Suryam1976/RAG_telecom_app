%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#f5f5f5', 'primaryTextColor': '#333', 'primaryBorderColor': '#666', 'lineColor': '#666', 'secondaryColor': '#f0f0f0', 'tertiaryColor': '#fff' }}}%%
flowchart TB
    subgraph Scraper["🕸️ Web Scraper"]
        Crawler(["Plan Page Crawler"]) --> Extractor(["Data Extractor"])
        Extractor --> Processor(["Data Processor"])
    end
    
    subgraph KB["📚 Knowledge Base"]
        Processor --> Embedder(["Text Embedder"])
        Embedder --> VectorDB[(Vector Store)]
    end
    
    subgraph Agent["🤖 AI Agent"]
        QueryParser(["Query Parser"]) --> Retriever(["Retriever"])
        Retriever --> Planner(["Simple Planner"])
        Planner --> Generator(["Response Generator"])
        VectorDB --> Retriever
    end
    
    subgraph UI["🖥️ Demo Interface"]
        Streamlit(["Streamlit App"]) --> QueryParser
        Generator --> Streamlit
    end
    
    classDef scraper fill:#a8dadc80,stroke:#457b9d,stroke-width:1px,color:#1d3557,font-family:Arial
    classDef kb fill:#8ecae680,stroke:#219ebc,stroke-width:1px,color:#023047,font-family:Arial
    classDef agent fill:#bee3db80,stroke:#89b0ae,stroke-width:1px,color:#3a506b,font-family:Arial
    classDef ui fill:#e9c46a80,stroke:#f4a261,stroke-width:1px,color:#264653,font-family:Arial
    
    class Crawler,Extractor,Processor scraper
    class Embedder,VectorDB kb
    class QueryParser,Retriever,Planner,Generator agent
    class Streamlit ui