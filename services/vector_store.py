import chromadb
import logging
import os
from typing import List, Dict, Any, Optional
from config import Config
import json

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.persist_directory = Config.CHROMA_PERSIST_DIRECTORY
        self.collection_name = Config.CHROMA_COLLECTION_NAME
        
        # Create directory if it doesn't exist
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Loaded existing collection: {self.collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Trainer feedback and challenges embeddings"}
            )
            logger.info(f"Created new collection: {self.collection_name}")
    
    def add_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        """Add text chunks with their embeddings to the vector store"""
        try:
            logger.info(f"Adding {len(chunks)} chunks to vector store...")
            
            if len(chunks) != len(embeddings):
                raise ValueError(f"Chunks count ({len(chunks)}) doesn't match embeddings count ({len(embeddings)})")
            
            # Prepare data for ChromaDB
            ids = [chunk["chunk_id"] for chunk in chunks]
            documents = [chunk["text"] for chunk in chunks]
            metadatas = []
            
            for chunk in chunks:
                # Convert metadata to strings for ChromaDB compatibility
                metadata = {}
                for key, value in chunk["metadata"].items():
                    metadata[key] = str(value) if value is not None else ""
                
                # Add additional chunk information
                metadata["content_type"] = chunk["content_type"]
                metadata["original_feedback_id"] = chunk["original_feedback_id"]
                
                metadatas.append(metadata)
            
            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"Successfully added {len(chunks)} chunks to vector store")
            
        except Exception as e:
            logger.error(f"Error adding chunks to vector store: {str(e)}")
            raise
    
    def search(self, query_embedding: List[float], top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search for similar chunks using query embedding"""
        try:
            if top_k is None:
                top_k = Config.TOP_K_RESULTS
            
            logger.debug(f"Searching for top {top_k} similar chunks...")
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            
            if results and results["documents"] and len(results["documents"]) > 0:
                documents = results["documents"][0] or []
                metadatas = results["metadatas"][0] or []
                distances = results["distances"][0] or []
                
                for i in range(len(documents)):
                    formatted_results.append({
                        "text": documents[i],
                        "metadata": metadatas[i],
                        "distance": distances[i],
                        "similarity_score": 1 - distances[i]  # Convert distance to similarity
                    })
            
            logger.debug(f"Found {len(formatted_results)} similar chunks")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        try:
            count = self.collection.count()
            return {
                "total_chunks": count,
                "collection_name": self.collection_name,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {}
    
    def clear_collection(self):
        """Clear all data from the collection"""
        try:
            logger.info("Clearing vector store collection...")
            
            # Delete the collection and recreate it
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Trainer feedback and challenges embeddings"}
            )
            
            logger.info("Vector store collection cleared successfully")
            
        except Exception as e:
            logger.error(f"Error clearing collection: {str(e)}")
            raise
    
    def search_with_filter(self, query_embedding: List[float], filters: Dict[str, str], top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search with metadata filters"""
        try:
            if top_k is None:
                top_k = Config.TOP_K_RESULTS
            
            logger.debug(f"Searching with filters: {filters}")
            
            # Convert filters to ChromaDB format
            filter_conditions = []
            for key, value in filters.items():
                if value:  # Only add non-empty filters
                    filter_conditions.append({key: {"$eq": str(value)}})
            
            # Handle multiple filters with $and operator
            if len(filter_conditions) > 1:
                where_clause = {"$and": filter_conditions}
            elif len(filter_conditions) == 1:
                where_clause = filter_conditions[0]
            else:
                where_clause = None
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_clause,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            
            if results and results["documents"] and len(results["documents"]) > 0:
                documents = results["documents"][0] or []
                metadatas = results["metadatas"][0] or []
                distances = results["distances"][0] or []
                
                for i in range(len(documents)):
                    formatted_results.append({
                        "text": documents[i],
                        "metadata": metadatas[i],
                        "distance": distances[i],
                        "similarity_score": 1 - distances[i]
                    })
            
            logger.debug(f"Found {len(formatted_results)} filtered chunks")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching with filters: {str(e)}")
            raise
        