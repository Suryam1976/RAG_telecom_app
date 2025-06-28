
FASTMCP_URL = os.getenv("FASTMCP_URL", "http://localhost:8000")
FASTMCP_API_KEY = os.getenv("FASTMCP_API_KEY")

# Configure page
st.set_page_config(
    page_title="FASTMCP Admin Dashboard",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar navigation
st.sidebar.title("FASTMCP Admin")
nav_option = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Extractions", "Plans", "Vector Store", "Settings"]
)

# Dashboard view
if nav_option == "Dashboard":
    st.title("FASTMCP Admin Dashboard")
    
    # Summary metrics
    st.markdown("### System Summary")
    
    # Get system stats
    system_stats = api_get("/api/v1/admin/stats")
    
    if system_stats:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Plans", system_stats["plan_count"])
        
        with col2:
            st.metric("Providers", system_stats["provider_count"])
        
        with col3:
            st.metric("Extraction Jobs", system_stats["extraction_job_count"])
        
        with col4:
            st.metric("Vector Chunks", system_stats["vector_chunk_count"])
```

## 10. Performance Optimization

### 10.1 Caching Strategy

```python
# app/core/cache.py
import redis
import json
import logging
from typing import Any, Optional
import hashlib
from datetime import timedelta
from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisCache:
    """Redis-based caching for FASTMCP Server"""
    
    def __init__(self):
        """Initialize Redis connection"""
        self.redis_url = settings.REDIS_URL
        self.default_ttl = 3600  # 1 hour default TTL
        self.enabled = settings.CACHE_ENABLED
        
        try:
            self.client = redis.from_url(self.redis_url)
            self.available = True
            logger.info(f"Connected to Redis cache at {self.redis_url}")
        except Exception as e:
            self.available = False
            logger.warning(f"Redis cache not available: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled or not self.available:
            return None
        
        try:
            # Generate hash key
            hashed_key = self._hash_key(key)
            
            # Get from Redis
            data = self.client.get(hashed_key)
            if data:
                logger.debug(f"Cache hit for key: {key}")
                return json.loads(data)
            else:
                logger.debug(f"Cache miss for key: {key}")
                return None
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None
```

### 10.2 Background Tasks with Celery

```python
# app/worker.py
import os
from celery import Celery
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "fastmcp",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Configure Celery
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.task_track_started = True
celery_app.conf.worker_hijack_root_logger = False

@celery_app.task(bind=True, name="extract_provider")
def extract_provider(self, provider_name: str, force_refresh: bool = False):
    """
    Background task to extract plans from a provider.
    
    Args:
        provider_name: Name of the provider to extract
        force_refresh: Whether to force a fresh extraction
    
    Returns:
        Dictionary with extraction results
    """
    from app.extractors.factory import ExtractorFactory
    import asyncio
    
    logger.info(f"Starting extraction task for {provider_name}")
    
    try:
        # Get extractor
        extractor_factory = ExtractorFactory()
        extractor = extractor_factory.get_extractor(provider_name)
        
        if not extractor:
            logger.error(f"Unsupported provider: {provider_name}")
            return {
                "status": "failed",
                "error": f"Unsupported provider: {provider_name}"
            }
        
        # Run extraction
        result = asyncio.run(extractor.run_extraction())
        
        # Store in database
        if result.status == "completed" and result.plans:
            from app.db.plans import store_plans
            store_plans(provider_name, result.plans)
        
        # Update task state
        self.update_state(
            state="PROGRESS",
            meta={
                "provider": provider_name,
                "status": result.status,
                "plan_count": len(result.plans) if result.plans else 0
            }
        )
        
        logger.info(f"Extraction completed for {provider_name}: {len(result.plans) if result.plans else 0} plans")
        
        return {
            "provider": provider_name,
            "status": result.status,
            "plan_count": len(result.plans) if result.plans else 0,
            "extraction_time": result.extraction_time.isoformat(),
            "error": result.error_message
        }
        
    except Exception as e:
        logger.error(f"Error in extraction task: {e}")
        return {
            "provider": provider_name,
            "status": "failed",
            "error": str(e)
        }
```

## 11. Monitoring and Observability

### 11.1 Prometheus Metrics

```python
# app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Summary
import time

# Define metrics
EXTRACTION_TOTAL = Counter(
    'fastmcp_extraction_total',
    'Total number of extraction jobs',
    ['provider', 'status']
)

EXTRACTION_DURATION = Histogram(
    'fastmcp_extraction_duration_seconds',
    'Time spent on extraction jobs',
    ['provider']
)

PLAN_COUNT = Gauge(
    'fastmcp_plan_count',
    'Number of plans in the database',
    ['provider']
)

VECTOR_SEARCH_TOTAL = Counter(
    'fastmcp_vector_search_total',
    'Total number of vector searches',
    ['status']
)

VECTOR_SEARCH_DURATION = Histogram(
    'fastmcp_vector_search_duration_seconds',
    'Time spent on vector searches'
)

API_REQUESTS = Counter(
    'fastmcp_api_requests_total',
    'Total number of API requests',
    ['endpoint', 'method', 'status']
)

API_RESPONSE_TIME = Histogram(
    'fastmcp_api_response_time_seconds',
    'API response time in seconds',
    ['endpoint']
)

# Helper functions
def track_extraction_job(provider, status, duration):
    """Track extraction job metrics"""
    EXTRACTION_TOTAL.labels(provider=provider, status=status).inc()
    EXTRACTION_DURATION.labels(provider=provider).observe(duration)

def update_plan_count(provider, count):
    """Update plan count gauge"""
    PLAN_COUNT.labels(provider=provider).set(count)

def track_vector_search(status, duration):
    """Track vector search metrics"""
    VECTOR_SEARCH_TOTAL.labels(status=status).inc()
    VECTOR_SEARCH_DURATION.observe(duration)
```

### 11.2 Logging Configuration

```python
# app/core/logging.py
import logging
import os
import json
from datetime import datetime
from logging.handlers import RotatingFileHandler
from app.core.config import settings

# Create logs directory if it doesn't exist
os.makedirs(settings.LOG_DIR, exist_ok=True)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(settings.LOG_LEVEL)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(settings.LOG_LEVEL)

# File handler for all logs
file_handler = RotatingFileHandler(
    os.path.join(settings.LOG_DIR, "fastmcp.log"),
    maxBytes=10485760,  # 10MB
    backupCount=10
)
file_handler.setLevel(settings.LOG_LEVEL)

# Error file handler
error_file_handler = RotatingFileHandler(
    os.path.join(settings.LOG_DIR, "error.log"),
    maxBytes=10485760,  # 10MB
    backupCount=10
)
error_file_handler.setLevel(logging.ERROR)

# JSON formatter for structured logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process
        }
        
        # Add exception info if available
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_record)
```

## 12. Testing Strategy

### 12.1 Unit Testing

```python
# tests/unit/test_standardization.py
import pytest
from app.standardization.engine import StandardizationEngine

def test_standardize_plan_basic():
    """Test basic plan standardization"""
    engine = StandardizationEngine()
    
    # Sample raw plan
    raw_plan = {
        "name": "5G Get More",
        "price": "$90/month",
        "data": "Unlimited",
        "features": [
            "5G Ultra Wideband access",
            "Premium unlimited data",
            "30GB premium mobile hotspot"
        ],
        "url": "https://www.verizon.com/plans/5g-get-more",
        "provider": "Verizon",
        "additional_info": {
            "contract": "No contract required",
            "autopay_discount": "$10"
        }
    }
    
    # Standardize plan
    standardized = engine.standardize_plan(raw_plan)
    
    # Verify basic structure
    assert standardized["schema_version"] == engine.schema_version
    assert standardized["provider"]["name"] == "Verizon"
    assert standardized["plan"]["name"] == "5G Get More"
    
    # Verify pricing
    assert standardized["pricing"]["base_price"]["amount"] == 80  # 90 - 10 autopay discount
    assert standardized["pricing"]["base_price"]["currency"] == "USD"
    
    # Verify data
    assert standardized["data"]["amount"] == "unlimited"
    assert standardized["data"]["priority"] == "premium"
    
    # Verify features
    features = standardized["features"]
    assert len(features) == 3
    assert any(f["name"] == "5G Ultra Wideband access" for f in features)
    
    # Verify contract
    assert standardized["contract"]["required"] == False
```

### 12.2 Integration Testing

```python
# tests/integration/test_extraction_pipeline.py
import pytest
import asyncio
from app.extractors.verizon import VerizonExtractor
from app.standardization.engine import StandardizationEngine
from app.vectors.processor import VectorProcessor

@pytest.mark.asyncio
async def test_extraction_to_indexing_pipeline():
    """Test the complete extraction to indexing pipeline"""
    # 1. Extract plans
    extractor = VerizonExtractor()
    result = await extractor.run_extraction()
    
    # Check extraction success
    assert result.status == "completed"
    assert len(result.plans) > 0
    
    # 2. Standardize a plan
    engine = StandardizationEngine()
    standardized_plan = engine.standardize_plan(result.plans[0])
    
    # Check standardization
    assert standardized_plan["schema_version"] is not None
    assert standardized_plan["provider"]["name"] == "Verizon"
    
    # 3. Index the plan
    processor = VectorProcessor()
    index_result = processor.index_plan(standardized_plan)
    
    # Check indexing
    assert index_result["status"] == "success"
    assert index_result["chunks_indexed"] > 0
```

## 13. Production Deployment 

### 13.1 Environment Configuration

```dotenv
# .env.example
# API Keys
OPENAI_API_KEY=your_openai_api_key
GROQ_API_KEY=your_groq_api_key
FASTMCP_API_KEY=your_fastmcp_api_key
ADMIN_PASSWORD=your_admin_password

# Database
POSTGRES_USER=fastmcp
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_DB=fastmcp
DATABASE_URL=postgresql://fastmcp:your_postgres_password@postgres:5432/fastmcp

# Redis
REDIS_URL=redis://redis:6379/0

# Server settings
LOG_LEVEL=INFO
VECTOR_DB_PATH=/app/data/chroma_db
CACHE_ENABLED=true
HEADLESS_BROWSER=true
EXTRACTION_TIMEOUT=30
VECTOR_SEARCH_LIMIT=10
RATE_LIMIT=100

# CORS settings
CORS_ORIGINS=http://localhost:8501,http://127.0.0.1:8501,http://localhost:8050
```

### 13.2 Production Deployment Script

```bash
#!/bin/bash
# deploy.sh - Production deployment script for FASTMCP Server

set -e

# Configuration
APP_DIR="/opt/fastmcp"
BACKUP_DIR="/opt/fastmcp/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create directories if they don't exist
mkdir -p "$APP_DIR"
mkdir -p "$BACKUP_DIR"
mkdir -p "$APP_DIR/data"
mkdir -p "$APP_DIR/logs"

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null || ! command -v docker-compose &> /dev/null; then
    echo "Docker and/or Docker Compose not found. Installing..."
    apt-get update
    apt-get install -y docker.io docker-compose
fi

# Backup existing data
if [ -d "$APP_DIR/data" ]; then
    echo "Backing up existing data..."
    tar -czf "$BACKUP_DIR/data_$TIMESTAMP.tar.gz" -C "$APP_DIR" data
fi

# Pull the latest code
echo "Pulling latest code..."
cd "$APP_DIR"
git pull

# Check if .env file exists
if [ ! -f "$APP_DIR/.env" ]; then
    echo "Creating .env file from example..."
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    echo "Please edit .env file with your configuration values."
    exit 1
fi

# Pull the latest Docker images
echo "Pulling latest Docker images..."
docker-compose pull

# Stop and remove existing containers
echo "Stopping existing containers..."
docker-compose down

# Start new containers
echo "Starting new containers..."
docker-compose up -d

# Wait for the application to start
echo "Waiting for the application to start..."
sleep 10

# Check if the application is running
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "Deployment successful!"
else
    echo "Deployment failed. Application is not responding."
    exit 1
fi

# Print status
echo "Deployment completed at $(date)"
docker-compose ps
```

## 14. Integration with RAG Telecom App

The integration with the existing RAG Telecom App will be done through a client interface that connects to the FASTMCP server API. This will allow the RAG app to leverage the enhanced extraction and standardization capabilities without major changes to its core functionality.

### 14.1 Client Implementation

```python
# In RAG Telecom App's app.py

# Initialize FASTMCP client
@st.cache_resource
def initialize_fastmcp():
    """Initialize and cache the FASTMCP client"""
    try:
        return FASTMCPClient(base_url=fastmcp_url, api_key=fastmcp_api_key)
    except Exception as e:
        st.error(f"Error initializing FASTMCP client: {str(e)}")
        logger.error(f"Error initializing FASTMCP client: {str(e)}", exc_info=True)
        return None

# When processing a user query
if query:
    with st.spinner("🤔 Analyzing your query and finding the best recommendations..."):
        try:
            # Parse query
            parsed_query = query_parser.parse(query)
            
            # Get recommendations from FASTMCP
            if fastmcp_client:
                # Convert parsed query to filters
                filters = {}
                if parsed_query.get("budget"):
                    # Extract numeric value from budget
                    import re
                    budget_match = re.search(r'(\d+)', parsed_query["budget"])
                    if budget_match:
                        filters["price_max"] = float(budget_match.group(1))
                
                if parsed_query.get("data_needs") and "unlimited" in parsed_query["data_needs"].lower():
                    filters["data_amount"] = "unlimited"
                
                if provider_name != "All":
                    filters["provider"] = provider_name
                
                # Search for plans
                search_query = query if not parsed_query else f"{query} {parsed_query.get('primary_concern', '')}"
                search_results = fastmcp_client.search_plans(search_query, filters)
                
                # Format as recommendations
                recommendations = {
                    "query": parsed_query,
                    "search_query": search_query,
                    "retrieved_docs": search_results,
                    "ranked_plans": []
                }
                
                # Generate response
                response = generator.generate_response(query, recommendations)
```

## 15. Acceptance Criteria

### 15.1 MVP Acceptance Criteria

1. **Extraction System**
   - Successfully extracts plan data from Verizon website
   - Handles basic error scenarios gracefully
   - Provides extraction status and logs

2. **Standardization Engine**
   - Correctly standardizes raw plan data
   - Applies provider-specific adjustments
   - Validates against schema

3. **Vector Store**
   - Properly indexes plan chunks
   - Supports basic search functionality
   - Implements filtering capabilities

4. **API Interface**
   - Provides all required endpoints
   - Handles authentication and authorization
   - Returns appropriate status codes and error messages

5. **Admin Dashboard**
   - Displays system statistics
   - Provides extraction management
   - Supports basic configuration

6. **RAG Integration**
   - Integrates with RAG Telecom App
   - Provides standardized responses
   - Maintains compatibility with existing features

## 16. Project Timeline

| Phase | Week | Key Deliverables |
|-------|------|------------------|
| Planning | 0 | Architecture design, tech stack selection, schema design |
| Core Setup | 1-2 | FastAPI server, base extractors, initial API endpoints |
| Standardization | 3-4 | Schema implementation, standardization engine, validation system |
| Vector Integration | 5-6 | Chunking strategies, embedding generation, retrieval standardization |
| Integration | 7-8 | RAG app integration, performance optimization, admin dashboard |

## 17. Resource Requirements

### 17.1 Development Resources

- 1 Senior Backend Developer
- 1 Data Engineer
- 1 Frontend Developer (part-time for admin dashboard)
- 1 DevOps Engineer (part-time for deployment)

### 17.2 Infrastructure Resources

- Development environment: 4 CPU cores, 16GB RAM
- Staging environment: 4 CPU cores, 16GB RAM
- Production environment: 8 CPU cores, 32GB RAM, 100GB SSD
- Database: PostgreSQL instance with 50GB storage
- Cache: Redis instance with 10GB memory
- Vector store: ChromaDB with 20GB storage

## 18. Conclusion

The FASTMCP server implementation will significantly enhance the RAG Telecom App's capabilities by providing:

1. **Improved data extraction** through specialized extractors for each telecom provider
2. **Standardized plan data** with a consistent schema across providers
3. **Enhanced vector search** with better chunking and relevance ranking
4. **Comprehensive monitoring** through Prometheus metrics and structured logging
5. **Administrative control** via a dedicated dashboard

This will result in better plan recommendations, more consistent user experience, and easier maintenance of the system as new providers and plan types are added.

The modular architecture ensures that components can be developed and tested independently, while the comprehensive test suite guarantees reliability and correctness of the system.

By following this implementation plan, the development team can deliver a production-ready FASTMCP server that integrates seamlessly with the existing RAG Telecom App, providing significant value to end users through improved plan recommendations and insights.
