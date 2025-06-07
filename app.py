import streamlit as st
import os
import json
import logging
from dotenv import load_dotenv
from scraper.crawler import PlanCrawler
from scraper.extractor import PlanExtractor, PlanData
from scraper.processor import DataProcessor
from knowledge_base.embedder import PlanEmbedder
from knowledge_base.vector_store import VectorStore
from agent.query_parser import QueryParser
from agent.planner import SimplePlanner
from agent.generator import ResponseGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")

# Page configuration
st.set_page_config(
    page_title="Telecom Plan Advisor",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar for configuration
st.sidebar.title("Configuration")
data_source = st.sidebar.radio(
    "Data Source",
    ["Sample Data", "Live Scraping", "Cached Scraping"],
    index=0,
    help="Choose between sample data, live web scraping, or cached scraped data"
)

provider_name = st.sidebar.selectbox(
    "Telecom Provider",
    ["Verizon", "AT&T", "T-Mobile"],
    index=0,
    help="Select the telecom provider to analyze"
)

# Scraping controls in sidebar
if data_source != "Sample Data":
    st.sidebar.markdown("### Scraping Controls")
    
    if st.sidebar.button("🔄 Refresh Data", help="Scrape fresh data from provider website"):
        st.session_state.force_refresh = True
    
    if st.sidebar.button("📊 Show Collection Stats", help="Display vector database statistics"):
        st.session_state.show_stats = True
    
    if st.sidebar.button("🗑️ Clear Cache", help="Clear cached scraped data"):
        st.session_state.clear_cache = True

# Sample plan data (fallback)
def get_sample_plans():
    """Get sample plan data for demonstration"""
    return [
        PlanData(
            name="5G Get More",
            price="$90/month",
            data="Unlimited",
            features=[
                "5G Ultra Wideband access", 
                "Premium unlimited data",
                "30GB premium mobile hotspot", 
                "HD streaming included",
                "Disney+ bundle included",
                "International texting to 200+ countries",
                "Cloud storage included"
            ],
            url="https://www.verizon.com/plans/5g-get-more",
            provider="Verizon",
            additional_info={"contract": "No contract required", "autopay_discount": "$10"}
        ),
        PlanData(
            name="5G Play More",
            price="$80/month",
            data="Unlimited",
            features=[
                "5G Ultra Wideband access", 
                "Premium unlimited data",
                "15GB premium mobile hotspot", 
                "HD streaming included",
                "Disney+ bundle included",
                "International texting to 200+ countries"
            ],
            url="https://www.verizon.com/plans/5g-play-more",
            provider="Verizon",
            additional_info={"contract": "No contract required", "autopay_discount": "$10"}
        )
    ]

# Initialize components
@st.cache_resource
def initialize_components():
    """Initialize and cache the components for the application"""
    try:
        # Set up knowledge base with explicit API key
        embedder = PlanEmbedder(api_key=openai_api_key)
        
        # Initialize vector store with embedding function
        vector_store = VectorStore(
            embedding_function=embedder,
            persist_directory="./chroma_db",
            collection_name="telecom_plans"
        )
        
        # Set up agent components
        query_parser = QueryParser(api_key=groq_api_key)
        planner = SimplePlanner(vector_store=vector_store, api_key=groq_api_key)
        generator = ResponseGenerator(api_key=groq_api_key)
        
        return embedder, vector_store, query_parser, planner, generator
    
    except Exception as e:
        st.error(f"Error initializing components: {str(e)}")
        logger.error(f"Error initializing components: {str(e)}", exc_info=True)
        raise e

def load_and_process_data(data_source, provider_name, embedder, vector_store):
    """Load and process data based on the selected source"""
    processor = DataProcessor()
    
    # Handle cache clearing
    if hasattr(st.session_state, 'clear_cache') and st.session_state.clear_cache:
        try:
            vector_store.clear_collection()
            st.success("Cache cleared successfully!")
        except Exception as e:
            st.error(f"Error clearing cache: {str(e)}")
        finally:
            del st.session_state.clear_cache
    
    if data_source == "Sample Data":
        # Use sample data
        sample_plans = get_sample_plans()
        processed_plans = processor.process_plans(sample_plans)
        
        # Create documents and add to vector store
        documents = embedder.prepare_plan_documents(processed_plans)
        
        # Check if we need to add documents (avoid duplicates)
        current_stats = vector_store.get_collection_stats()
        if current_stats.get('total_documents', 0) == 0:
            vector_store.add_documents(documents)
            st.info(f"Loaded {len(processed_plans)} sample plans into knowledge base")
        
        return processed_plans
    
    elif data_source == "Live Scraping":
        # Force refresh or check if we need to scrape
        force_refresh = hasattr(st.session_state, 'force_refresh') and st.session_state.force_refresh
        
        with st.spinner(f"Scraping fresh data from {provider_name}..."):
            processed_plans = processor.get_provider_data(provider_name, force_refresh=True)
        
        if processed_plans:
            # Create documents and update vector store
            documents = embedder.prepare_plan_documents(processed_plans)
            vector_store.update_documents(documents, provider_name)
            st.success(f"Successfully scraped {len(processed_plans)} plans from {provider_name}!")
        else:
            st.warning(f"No plans found for {provider_name}. Check the logs for details.")
            processed_plans = []
        
        # Clear force refresh flag
        if hasattr(st.session_state, 'force_refresh'):
            del st.session_state.force_refresh
        
        return processed_plans
    
    else:  # Cached Scraping
        # Try to load cached data first
        processed_plans = processor.load_scraped_data(provider_name)
        
        if not processed_plans:
            # No cached data, try to scrape
            with st.spinner(f"No cached data found. Scraping {provider_name}..."):
                processed_plans = processor.get_provider_data(provider_name, force_refresh=False)
        
        if processed_plans:
            # Create documents and update vector store
            documents = embedder.prepare_plan_documents(processed_plans)
            vector_store.update_documents(documents, provider_name)
            st.info(f"Loaded {len(processed_plans)} plans for {provider_name}")
        else:
            st.warning(f"No data available for {provider_name}. Falling back to sample data.")
            # Fallback to sample data
            sample_plans = get_sample_plans()
            processed_plans = processor.process_plans(sample_plans)
            documents = embedder.prepare_plan_documents(processed_plans)
            vector_store.add_documents(documents)
        
        return processed_plans

# Main content
st.title("📱 Telecom Plan Advisor")
st.markdown("*AI-powered assistant to help you find the perfect mobile plan*")

# Initialize components
try:
    embedder, vector_store, query_parser, planner, generator = initialize_components()
    
    # Show collection stats if requested
    if hasattr(st.session_state, 'show_stats') and st.session_state.show_stats:
        stats = vector_store.get_collection_stats()
        st.sidebar.json(stats)
        del st.session_state.show_stats
    
    # Load and process data
    processed_plans = load_and_process_data(data_source, provider_name, embedder, vector_store)
    
    # Display data source info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Data Source", data_source)
    with col2:
        st.metric("Provider", provider_name)
    with col3:
        st.metric("Plans Loaded", len(processed_plans))
    
    # Text input for user query
    st.markdown("### Ask About Plans")
    query = st.text_input(
        "What would you like to know about mobile plans?",
        placeholder="e.g., I need unlimited data with good hotspot for my family",
        help="Ask about plan features, pricing, comparisons, or get recommendations"
    )
    
    # Process query when submitted
    if query:
        with st.spinner("🤔 Analyzing your query and finding the best recommendations..."):
            try:
                # Parse query
                parsed_query = query_parser.parse(query)
                
                # Get recommendations
                recommendations = planner.get_recommendations(parsed_query)
                
                # Generate response
                response = generator.generate_response(query, recommendations)
                
                # Display response
                st.markdown("### 🎯 Recommendation")
                st.markdown(response)
                
                # Display found plans
                if recommendations.get("retrieved_docs"):
                    st.markdown("### 📋 Relevant Plans")
                    
                    for i, doc in enumerate(recommendations["retrieved_docs"][:3]):
                        with st.expander(f"📱 Plan {i+1}: {doc.metadata.get('name', 'Unknown Plan')}"):
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                st.markdown(doc.page_content)
                            
                            with col2:
                                if doc.metadata:
                                    st.markdown("**Plan Details:**")
                                    for key, value in doc.metadata.items():
                                        if key not in ['source']:
                                            st.markdown(f"**{key.title()}:** {value}")
                
                # Show parsed query details in expander
                with st.expander("🔍 Query Analysis Details"):
                    st.json(parsed_query)
                    
            except Exception as e:
                st.error(f"Error processing query: {str(e)}")
                logger.error(f"Query processing error: {str(e)}", exc_info=True)
    
    # Display sample queries if no query entered
    if not query:
        st.markdown("### 💡 Try These Sample Queries")
        
        sample_queries = [
            "I need unlimited data with the best 5G coverage",
            f"What's the cheapest {provider_name} plan with hotspot?",
            "Compare plans for a family of 4 with heavy streaming",
            f"Which {provider_name} plan includes Disney+ or Netflix?",
            "I travel internationally - which plan has the best roaming?",
            "Best plan for gaming and streaming under $85/month"
        ]
        
        # Create buttons for sample queries
        cols = st.columns(2)
        for i, sample in enumerate(sample_queries):
            col = cols[i % 2]
            if col.button(sample, key=f"sample_{i}"):
                st.session_state.selected_query = sample
                st.rerun()
    
    # Footer with additional info
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🔧 Features:**")
        st.markdown("• Live web scraping\n• AI-powered recommendations\n• Multi-provider support")
    
    with col2:
        st.markdown("**📊 Data Sources:**")
        st.markdown("• Real-time provider websites\n• Cached scraped data\n• Sample demonstration data")
    
    with col3:
        st.markdown("**🤖 AI Models:**")
        st.markdown("• OpenAI embeddings\n• Groq LLM processing\n• ChromaDB vector search")

except Exception as e:
    st.error(f"Application Error: {str(e)}")
    logger.error(f"Application error: {str(e)}", exc_info=True)
    
    st.markdown("### 🔧 Troubleshooting")
    st.markdown("""
    **Common Issues:**
    1. **API Keys:** Make sure OPENAI_API_KEY and GROQ_API_KEY are set in your .env file
    2. **Dependencies:** Run `pip install -r requirements.txt` to install all dependencies
    3. **Playwright:** Run `playwright install` to install browser dependencies
    4. **Permissions:** Ensure the app has permission to create directories and files
    """)
