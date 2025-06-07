import logging
import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import numpy as np
from datetime import datetime

from knowledge_base.embedder import Document

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(
        self, 
        embedding_function,
        persist_directory: str = "./chroma_db",
        collection_name: str = "telecom_plans"
    ):
        """
        Initialize the vector store with ChromaDB.
        
        Args:
            embedding_function: Function to generate embeddings
            persist_directory: Directory to persist the database
            collection_name: Name of the collection to store embeddings
        """
        self.embedding_function = embedding_function
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Create directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)
        
        try:
            # Initialize ChromaDB client with minimal settings
            self.client = chromadb.PersistentClient(
                path=persist_directory
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
            )
            
            # Store documents for retrieval
            self.documents = {}
            
            logger.info(f"Initialized VectorStore with collection '{collection_name}'")
            logger.info(f"Collection contains {self.collection.count()} documents")
            
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {str(e)}")
            # Fallback to in-memory client
            logger.info("Falling back to in-memory ChromaDB client")
            self.client = chromadb.Client()
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            self.documents = {}
    
    def add_documents(self, documents: List[Document]) -> None:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of Document objects to add
        """
        if not documents:
            logger.warning("No documents provided to add")
            return
        
        logger.info(f"Adding {len(documents)} documents to vector store")
        
        try:
            # Extract texts and metadata
            texts = [doc.page_content for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            
            # Generate unique IDs with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ids = [f"doc_{timestamp}_{i}" for i in range(len(documents))]
            
            # Generate embeddings
            logger.info("Generating embeddings...")
            embeddings = self.embedding_function.embed_documents(texts)
            
            # Add to collection in batches to avoid memory issues
            batch_size = 10
            for i in range(0, len(documents), batch_size):
                end_idx = min(i + batch_size, len(documents))
                
                batch_embeddings = embeddings[i:end_idx]
                batch_texts = texts[i:end_idx]
                batch_metadatas = metadatas[i:end_idx]
                batch_ids = ids[i:end_idx]
                
                self.collection.add(
                    embeddings=batch_embeddings,
                    documents=batch_texts,
                    metadatas=batch_metadatas,
                    ids=batch_ids
                )
                
                # Store documents for retrieval
                for j, doc in enumerate(documents[i:end_idx]):
                    self.documents[batch_ids[j]] = doc
            
            logger.info(f"Successfully added {len(documents)} documents")
            logger.info(f"Collection now contains {self.collection.count()} documents")
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            raise
    
    def update_documents(self, documents: List[Document], provider: str = None) -> None:
        """
        Update documents for a specific provider by removing old ones and adding new ones.
        
        Args:
            documents: List of new Document objects
            provider: Provider name to update (if None, adds without removing)
        """
        if provider:
            logger.info(f"Updating documents for provider: {provider}")
            self.remove_provider_documents(provider)
        
        self.add_documents(documents)
    
    def remove_provider_documents(self, provider: str) -> None:
        """
        Remove all documents for a specific provider.
        
        Args:
            provider: Provider name
        """
        logger.info(f"Removing existing documents for provider: {provider}")
        
        try:
            # Get all documents in the collection
            all_docs = self.collection.get()
            
            # Find IDs of documents from this provider
            ids_to_remove = []
            for i, metadata in enumerate(all_docs['metadatas']):
                if metadata and metadata.get('provider') == provider:
                    ids_to_remove.append(all_docs['ids'][i])
            
            if ids_to_remove:
                # Remove from collection
                self.collection.delete(ids=ids_to_remove)
                
                # Remove from local cache
                for doc_id in ids_to_remove:
                    if doc_id in self.documents:
                        del self.documents[doc_id]
                
                logger.info(f"Removed {len(ids_to_remove)} documents for {provider}")
            else:
                logger.info(f"No existing documents found for {provider}")
                
        except Exception as e:
            logger.error(f"Error removing documents for {provider}: {str(e)}")
    
    def similarity_search(self, query: str, k: int = 5, provider_filter: str = None) -> List[Document]:
        """
        Search for documents similar to the query.
        
        Args:
            query: Query string
            k: Number of results to return
            provider_filter: Optional provider name to filter results
            
        Returns:
            List of Document objects
        """
        logger.info(f"Searching for documents similar to: '{query}'")
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_function.embed_query(query)
            
            # Prepare where clause for filtering
            where_clause = None
            if provider_filter:
                where_clause = {"provider": provider_filter}
                logger.info(f"Filtering results by provider: {provider_filter}")
            
            # Search collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=where_clause
            )
            
            # Convert results to Documents
            documents = []
            if results["ids"] and len(results["ids"]) > 0:
                for i, doc_id in enumerate(results["ids"][0]):
                    if doc_id in self.documents:
                        documents.append(self.documents[doc_id])
                    else:
                        # Create a new Document if not found in cache
                        documents.append(Document(
                            page_content=results["documents"][0][i],
                            metadata=results["metadatas"][0][i] or {}
                        ))
            
            logger.info(f"Found {len(documents)} similar documents")
            return documents
            
        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection.
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            
            # Try to get all documents for detailed stats
            try:
                all_docs = self.collection.get()
                total_docs = len(all_docs['ids'])
                
                # Count documents by provider
                provider_counts = {}
                for metadata in all_docs['metadatas']:
                    if metadata and 'provider' in metadata:
                        provider = metadata['provider']
                        provider_counts[provider] = provider_counts.get(provider, 0) + 1
            except Exception:
                total_docs = count
                provider_counts = {}
            
            stats = {
                'total_documents': total_docs,
                'provider_counts': provider_counts,
                'collection_name': self.collection_name,
                'persist_directory': self.persist_directory
            }
            
            logger.info(f"Collection stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {'total_documents': 0, 'provider_counts': {}, 'collection_name': self.collection_name}
    
    def clear_collection(self) -> None:
        """
        Clear all documents from the collection.
        """
        logger.warning("Clearing all documents from collection")
        
        try:
            # Delete the collection
            self.client.delete_collection(self.collection_name)
            
            # Recreate the collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            # Clear local cache
            self.documents.clear()
            
            logger.info("Collection cleared successfully")
            
        except Exception as e:
            logger.error(f"Error clearing collection: {str(e)}")
    
    def search_by_provider(self, provider: str, limit: int = 10) -> List[Document]:
        """
        Get all documents for a specific provider.
        
        Args:
            provider: Provider name
            limit: Maximum number of documents to return
            
        Returns:
            List of Document objects
        """
        logger.info(f"Getting documents for provider: {provider}")
        
        try:
            results = self.collection.get(
                where={"provider": provider},
                limit=limit
            )
            
            documents = []
            for i, doc_id in enumerate(results["ids"]):
                if doc_id in self.documents:
                    documents.append(self.documents[doc_id])
                else:
                    documents.append(Document(
                        page_content=results["documents"][i],
                        metadata=results["metadatas"][i] or {}
                    ))
            
            logger.info(f"Found {len(documents)} documents for {provider}")
            return documents
            
        except Exception as e:
            logger.error(f"Error searching by provider {provider}: {str(e)}")
            return []
    
    def rebuild_index(self, documents: List[Document]) -> None:
        """
        Rebuild the entire index with new documents.
        
        Args:
            documents: List of Document objects to rebuild with
        """
        logger.info(f"Rebuilding index with {len(documents)} documents")
        
        # Clear existing collection
        self.clear_collection()
        
        # Add new documents
        self.add_documents(documents)


