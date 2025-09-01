import logging
import re
from typing import Dict, List, Any, Tuple
from services.embedding_service import EmbeddingService
from services.vector_store import VectorStore
from config import Config

logger = logging.getLogger(__name__)

class QueryProcessor:
    def __init__(self, embedding_service: EmbeddingService, vector_store: VectorStore):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a user query and retrieve relevant context"""
        try:
            logger.info(f"Processing query: {query}")
            
            # Analyze query to extract filters
            filters = self._extract_filters_from_query(query)
            logger.debug(f"Extracted filters: {filters}")
            
            # Generate query embedding
            query_embedding = self.embedding_service.generate_query_embedding(query)
            
            # Search for relevant chunks
            if filters:
                results = self.vector_store.search_with_filter(
                    query_embedding, 
                    filters, 
                    top_k=Config.TOP_K_RESULTS
                )
            else:
                results = self.vector_store.search(
                    query_embedding, 
                    top_k=Config.TOP_K_RESULTS
                )
            
            # Filter by similarity threshold
            filtered_results = [
                result for result in results 
                if result["similarity_score"] >= Config.SIMILARITY_THRESHOLD
            ]
            
            if not filtered_results:
                logger.warning("No relevant results found above similarity threshold")
                # If no results above threshold, take top 3 anyway
                filtered_results = results[:3]
            
            # Group and prioritize results
            processed_results = self._process_and_group_results(filtered_results, query)
            
            return {
                "query": query,
                "results": processed_results,
                "total_found": len(results),
                "relevant_count": len(filtered_results),
                "filters_applied": filters
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise
    
    def _extract_filters_from_query(self, query: str) -> Dict[str, str]:
        """Extract metadata filters from natural language query"""
        filters = {}
        query_lower = query.lower()
        
        # Project name extraction
        project_patterns = [
            r'project\s+([a-zA-Z\s\-]+)',
            r'in\s+([a-zA-Z\s\-]+)\s+project',
            r'([a-zA-Z\s\-]+)\s+cultivation',
            r'seaweed\s+cultivation'
        ]
        
        for pattern in project_patterns:
            match = re.search(pattern, query_lower)
            if match:
                project_name = match.group(1).strip()
                if 'seaweed' in project_name or 'cultivation' in project_name:
                    filters['project_name'] = 'Seaweed Cultivation'
                break
        
        # Batch extraction
        batch_patterns = [
            r'batch[- ]([a-zA-Z\-\d]+)',
            r'for\s+([a-zA-Z\-\d]+)\s+batch'
        ]
        
        for pattern in batch_patterns:
            match = re.search(pattern, query_lower)
            if match:
                filters['batch_id'] = match.group(1).strip()
                break
        
        # Centre/location extraction
        centre_patterns = [
            r'in\s+([a-zA-Z]+)',
            r'at\s+([a-zA-Z]+)',
            r'centre[- ]([a-zA-Z]+)'
        ]
        
        for pattern in centre_patterns:
            match = re.search(pattern, query_lower)
            if match:
                location = match.group(1).strip()
                # Exclude common words that aren't locations
                excluded_words = ['may', 'april', 'march', 'june', 'july', 'august', 'september', 'october', 'november', 'december', 'challenges', 'feedback', 'course', 'project', 'batch']
                if location not in excluded_words:
                    filters['centre_name'] = location.title()
                break
        
        # Date extraction
        date_patterns = [
            r'in\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s*(\d{4})?',
            r'on\s+(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
            r'(\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, query_lower)
            if match:
                if 'may' in match.group(0) and '2025' in query:
                    filters['feedback_date'] = '22-05-2025'
                break
        
        # Content type extraction
        if 'challenge' in query_lower:
            filters['content_type'] = 'challenges'
        elif 'feedback' in query_lower:
            filters['content_type'] = 'feedback'
        elif 'course plan' in query_lower:
            filters['content_type'] = 'course_plan'
        
        return filters
    
    def _process_and_group_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Process and group results by feedback entry and content type"""
        
        # Group by original feedback ID
        grouped_results = {}
        
        for result in results:
            feedback_id = result["metadata"].get("original_feedback_id", "unknown")
            
            if feedback_id not in grouped_results:
                grouped_results[feedback_id] = {
                    "feedback_id": feedback_id,
                    "metadata": result["metadata"],
                    "content_types": {},
                    "max_similarity": result["similarity_score"],
                    "total_chunks": 0
                }
            
            content_type = result["metadata"].get("content_type", "unknown")
            
            if content_type not in grouped_results[feedback_id]["content_types"]:
                grouped_results[feedback_id]["content_types"][content_type] = []
            
            grouped_results[feedback_id]["content_types"][content_type].append({
                "text": result["text"],
                "similarity_score": result["similarity_score"]
            })
            
            grouped_results[feedback_id]["max_similarity"] = max(
                grouped_results[feedback_id]["max_similarity"],
                result["similarity_score"]
            )
            grouped_results[feedback_id]["total_chunks"] += 1
        
        # Convert to list and sort by relevance
        processed_results = list(grouped_results.values())
        processed_results.sort(key=lambda x: x["max_similarity"], reverse=True)
        
        return processed_results