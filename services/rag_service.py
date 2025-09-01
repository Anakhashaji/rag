import logging
from typing import Dict, List, Any
from services.firebase_service import FirebaseService
from services.data_processor import DataProcessor
from services.embedding_service import EmbeddingService
from services.vector_store import VectorStore
from services.query_processor import QueryProcessor
from services.llm_service import LLMService

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        """Initialize RAG service with all components"""
        self.firebase_service = FirebaseService()
        self.data_processor = DataProcessor()
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.query_processor = QueryProcessor(self.embedding_service, self.vector_store)
        self.llm_service = LLMService()
        
        self.is_initialized = False
        
    def initialize(self) -> Dict[str, Any]:
        """Initialize the RAG system by processing Firebase data"""
        try:
            logger.info("Starting RAG system initialization...")
            
            # Step 1: Fetch data from Firebase
            logger.info("Fetching data from Firebase...")
            feedback_entries = self.firebase_service.get_all_feedback_with_metadata()
            
            if not feedback_entries:
                raise Exception("No feedback data found in Firebase")
            
            # Step 2: Process data into chunks
            logger.info("Processing data into chunks...")
            chunks = self.data_processor.process_feedback_data(feedback_entries)
            
            if not chunks:
                raise Exception("No text chunks were created from the data")
            
            # Step 3: Generate embeddings
            logger.info("Generating embeddings...")
            texts = [chunk["text"] for chunk in chunks]
            embeddings = self.embedding_service.generate_embeddings(texts)
            
            # Step 4: Store in vector database
            logger.info("Storing embeddings in vector database...")
            
            # Clear existing data first
            self.vector_store.clear_collection()
            
            # Add new data
            self.vector_store.add_chunks(chunks, embeddings)
            
            # Get final stats
            stats = self.vector_store.get_collection_stats()
            
            self.is_initialized = True
            
            result = {
                "status": "success",
                "total_feedback_entries": len(feedback_entries),
                "total_chunks": len(chunks),
                "embeddings_generated": len(embeddings),
                "vector_store_stats": stats
            }
            
            logger.info(f"RAG system initialization completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error during RAG initialization: {str(e)}")
            self.is_initialized = False
            raise
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a user query through the RAG pipeline"""
        try:
            if not self.is_initialized:
                # Try to auto-initialize
                logger.info("RAG system not initialized, attempting auto-initialization...")
                self.initialize()
            
            logger.info(f"Processing query through RAG pipeline: {query}")
            
            # Step 1: Process query and retrieve relevant context
            query_results = self.query_processor.process_query(query)
            
            if not query_results["results"]:
                return {
                    "answer": "I couldn't find any relevant trainer feedback or challenges related to your query. Please try rephrasing your question or asking about different topics.",
                    "sources": [],
                    "metadata": {
                        "total_found": 0,
                        "relevant_count": 0,
                        "query_processed": True
                    }
                }
            
            # Step 2: Generate response using LLM
            llm_response = self.llm_service.generate_response(query, query_results["results"])
            
            # Step 3: Format sources and metadata
            sources = self._format_sources(query_results["results"])
            metadata = {
                "total_found": query_results["total_found"],
                "relevant_count": query_results["relevant_count"],
                "filters_applied": query_results["filters_applied"],
                "query_processed": True
            }
            
            return {
                "answer": llm_response,
                "sources": sources,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "answer": "I apologize, but I encountered an error while processing your query. Please try again or contact support if the issue persists.",
                "sources": [],
                "metadata": {
                    "error": str(e),
                    "query_processed": False
                }
            }
    
    def _format_sources(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format retrieval results as sources for the response"""
        sources = []
        
        for result in results:
            metadata = result.get("metadata", {})
            
            source = {
                "feedback_id": metadata.get("logged_by_user_name", result.get("feedback_id", "unknown")),
                "project": metadata.get("project_name", ""),
                "course": metadata.get("course_name", ""),
                "centre": metadata.get("centre_name", ""),
                "batch": metadata.get("batch_id", ""),
                "date": metadata.get("feedback_date", ""),
                "trainer": metadata.get("user_name", ""),
                "logged_by": metadata.get("logged_by_user_name", ""),
                "content_types": list(result.get("content_types", {}).keys()),
                "relevance_score": result.get("max_similarity", 0)
            }
            
            sources.append(source)
        
        return sources
    
    def get_status(self) -> Dict[str, Any]:
        """Get current system status"""
        try:
            vector_stats = self.vector_store.get_collection_stats()
            
            return {
                "initialized": self.is_initialized,
                "vector_store": vector_stats,
                "services": {
                    "firebase": "connected",
                    "embedding": "ready",
                    "llm": "ready",
                    "vector_store": "ready"
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting status: {str(e)}")
            return {
                "initialized": False,
                "error": str(e),
                "services": {
                    "firebase": "error",
                    "embedding": "error", 
                    "llm": "error",
                    "vector_store": "error"
                }
            }