import requests
import logging
from typing import Dict, List, Any
from config import Config
import json

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.api_url = Config.LLM_API_URL
        self.model_name = Config.LLM_MODEL_NAME
        self.api_token = Config.HUGGINGFACE_API_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
    
    def generate_response(self, query: str, retrieved_context: List[Dict[str, Any]]) -> str:
        """Generate response using LLM with retrieved context"""
        try:
            logger.info("Generating LLM response...")
            
            # Create context from retrieved results
            context = self._format_context(retrieved_context)
            
            # Create system prompt
            system_prompt = self._create_system_prompt()
            
            # Create user prompt with context
            user_prompt = self._create_user_prompt(query, context)
            
            # Call LLM API
            response = self._call_llm_api(system_prompt, user_prompt)
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            raise
    
    def _format_context(self, retrieved_context: List[Dict[str, Any]]) -> str:
        """Format retrieved context for LLM prompt"""
        context_parts = []
        
        for i, result in enumerate(retrieved_context, 1):
            feedback_id = result.get("feedback_id", "unknown")
            metadata = result.get("metadata", {})
            content_types = result.get("content_types", {})
            
            # Create context block for this feedback entry
            logged_by_name = metadata.get("logged_by_user_name", feedback_id)
            context_block = f"\n--- Feedback Entry {i} (By: {logged_by_name}) ---\n"
            
            # Add metadata context
            if metadata:
                context_block += "Context Information:\n"
                
                # Project and course info
                if metadata.get("project_name"):
                    context_block += f"• Project: {metadata['project_name']}\n"
                if metadata.get("course_name"):
                    context_block += f"• Course: {metadata['course_name']}\n"
                
                # Location info
                if metadata.get("centre_name"):
                    context_block += f"• Centre: {metadata['centre_name']}"
                    if metadata.get("district"):
                        context_block += f", {metadata['district']}"
                    if metadata.get("state"):
                        context_block += f", {metadata['state']}"
                    context_block += "\n"
                
                # Batch info
                if metadata.get("batch_id"):
                    context_block += f"• Batch: {metadata['batch_id']}"
                    if metadata.get("batch_type"):
                        context_block += f" ({metadata['batch_type']})"
                    context_block += "\n"
                
                # Date and trainer info
                if metadata.get("feedback_date"):
                    context_block += f"• Date: {metadata['feedback_date']}\n"
                if metadata.get("user_name"):
                    context_block += f"• Trainer: {metadata['user_name']}\n"
                if metadata.get("logged_by_user_name"):
                    context_block += f"• Logged by: {metadata['logged_by_user_name']}\n"
                if metadata.get("total_hours_spent"):
                    context_block += f"• Hours Spent: {metadata['total_hours_spent']}\n"
            
            # Add content by type
            for content_type, chunks in content_types.items():
                if chunks:
                    context_block += f"\n{content_type.title()}:\n"
                    for chunk in chunks:
                        context_block += f"• {chunk['text']}\n"
            
            context_parts.append(context_block)
        
        return "\n".join(context_parts)
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for the LLM"""
        return """You are an intelligent assistant that analyzes trainer feedback and challenges from educational training programs. Your role is to provide comprehensive, accurate, and helpful responses based on the provided context.

Guidelines:
1. Base your responses strictly on the provided context from trainer feedback data
2. Provide specific details including dates, locations, projects, batches, and trainer information when available
3. Distinguish between feedback and challenges clearly
4. Summarize key themes and patterns when multiple entries are relevant
5. If the context doesn't contain enough information to fully answer the question, clearly state what information is missing
6. Use a professional, informative tone
7. Organize your response clearly with appropriate structure
8. Include relevant metadata (project names, locations, dates, etc.) to provide context

Remember: Only use information from the provided context. Do not make assumptions or add information not present in the context."""
    
    def _create_user_prompt(self, query: str, context: str) -> str:
        """Create user prompt with query and context"""
        return f"""Based on the following trainer feedback and challenge data, please answer this question:

Question: {query}

Context from Trainer Feedback Database:
{context}

Please provide a comprehensive answer based on the above context."""
    
    def _call_llm_api(self, system_prompt: str, user_prompt: str, max_retries: int = 3) -> str:
        """Call the Hugging Face LLM API"""
        
        for attempt in range(max_retries):
            try:
                payload = {
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
                
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if "choices" in result and len(result["choices"]) > 0:
                        return result["choices"][0]["message"]["content"].strip()
                    else:
                        logger.error(f"Unexpected LLM response format: {result}")
                        return "I apologize, but I received an unexpected response format from the language model."
                
                elif response.status_code == 503:
                    logger.warning(f"LLM service unavailable, attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                
                else:
                    logger.error(f"LLM API error: {response.status_code} - {response.text}")
                    return f"I apologize, but I encountered an error while processing your request (Status: {response.status_code})."
                
            except requests.exceptions.Timeout:
                logger.warning(f"LLM API timeout, attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    continue
                    
            except Exception as e:
                logger.error(f"Error calling LLM API on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    continue
        
        return "I apologize, but I'm currently unable to process your request due to technical difficulties. Please try again later."