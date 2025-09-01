import requests
import numpy as np
import logging
from typing import List, Dict, Any
from config import Config
import time

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.api_url = Config.EMBEDDING_API_URL
        self.api_token = Config.HUGGINGFACE_API_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
    def generate_embeddings(self, texts: List[str], max_retries: int = 3) -> List[List[float]]:
        """Generate embeddings for a list of texts"""
        try:
            logger.info(f"Generating embeddings for {len(texts)} texts...")
            
            embeddings = []
            
            for i, text in enumerate(texts):
                if i % 10 == 0:
                    logger.info(f"Processing embedding {i}/{len(texts)}")
                
                embedding = self._generate_single_embedding(text, max_retries)
                if embedding is not None:
                    embeddings.append(embedding)
                else:
                    logger.warning(f"Failed to generate embedding for text {i}, using zero vector")
                    # Use a zero vector as fallback
                    embeddings.append([0.0] * 384)  # BAAI/bge-small-en-v1.5 has 384 dimensions
                
                # Small delay to avoid rate limiting
                time.sleep(0.1)
            
            logger.info(f"Successfully generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    def _generate_single_embedding(self, text: str, max_retries: int = 3) -> List[float]:
        """Generate embedding for a single text with retry logic"""
        for attempt in range(max_retries):
            try:
                payload = {
                    "inputs": text,
                    "options": {
                        "wait_for_model": True
                    }
                }
                
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # Handle different response formats
                    if isinstance(result, list) and len(result) > 0:
                        # Handle the case where result is a list of numbers (direct embedding)
                        if isinstance(result[0], (int, float)):
                            return result  # Direct embedding vector
                        elif isinstance(result[0], list):
                            return result[0]  # Nested list format
                        elif isinstance(result[0], dict) and 'embedding' in result[0]:
                            return result[0]['embedding']
                    elif isinstance(result, dict) and 'embedding' in result:
                        return result['embedding']
                    
                    logger.error(f"Unexpected embedding response format: {type(result)}, content: {result}")
                    
                elif response.status_code == 503:
                    # Model loading, wait and retry
                    wait_time = min(2 ** attempt, 10)
                    logger.info(f"Model loading, waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                    
                else:
                    logger.error(f"Embedding API error: {response.status_code} - {response.text}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1}, retrying...")
                time.sleep(1)
                continue
                
            except Exception as e:
                logger.error(f"Error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                
        logger.error(f"Failed to generate embedding after {max_retries} attempts")
        return [0.0] * 384  # Return zero vector fallback instead of None
    
    def generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for a query text"""
        try:
            logger.debug(f"Generating query embedding for: {query[:100]}...")
            
            embedding = self._generate_single_embedding(query)
            if embedding is None or all(x == 0.0 for x in embedding):
                raise Exception("Failed to generate query embedding")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            raise