import logging
from typing import Dict, List, Any, Tuple
from config import Config

logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self):
        self.max_chunk_size = Config.MAX_CHUNK_SIZE
        self.chunk_overlap = Config.CHUNK_OVERLAP
    
    def process_feedback_data(self, feedback_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process feedback data into chunks suitable for embedding"""
        try:
            logger.info(f"Processing {len(feedback_entries)} feedback entries...")
            
            processed_chunks = []
            
            for entry in feedback_entries:
                try:
                    chunks = self._create_chunks_from_entry(entry)
                    processed_chunks.extend(chunks)
                except Exception as e:
                    logger.error(f"Error processing entry {entry.get('feedback_id', 'unknown')}: {str(e)}")
                    continue
            
            logger.info(f"Created {len(processed_chunks)} chunks from feedback data")
            return processed_chunks
            
        except Exception as e:
            logger.error(f"Error processing feedback data: {str(e)}")
            raise
    
    def _create_chunks_from_entry(self, entry: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create text chunks from a single feedback entry"""
        chunks = []
        
        feedback_data = entry.get("TrainersFeedbackLog", {})
        feedback_id = entry.get("feedback_id", "")
        
        # Extract main content fields
        feedback_text = feedback_data.get("feedback", "")
        challenges_text = feedback_data.get("challenges", "")
        
        # Create metadata context
        metadata = self._create_metadata_context(entry)
        
        # Process feedback text
        if feedback_text and feedback_text.strip():
            feedback_chunks = self._split_text_into_chunks(feedback_text)
            for i, chunk in enumerate(feedback_chunks):
                chunks.append({
                    "chunk_id": f"{feedback_id}_feedback_{i}",
                    "text": chunk,
                    "content_type": "feedback",
                    "metadata": metadata,
                    "original_feedback_id": feedback_id
                })
        
        # Process challenges text
        if challenges_text and challenges_text.strip():
            challenges_chunks = self._split_text_into_chunks(challenges_text)
            for i, chunk in enumerate(challenges_chunks):
                chunks.append({
                    "chunk_id": f"{feedback_id}_challenges_{i}",
                    "text": chunk,
                    "content_type": "challenges",
                    "metadata": metadata,
                    "original_feedback_id": feedback_id
                })
        
        # Process course plans
        course_plans = entry.get("CoursePlans", [])
        for cp_idx, course_plan in enumerate(course_plans):
            cp_details = course_plan.get("course_plan_details", "")
            if cp_details and cp_details.strip():
                cp_chunks = self._split_text_into_chunks(cp_details)
                for i, chunk in enumerate(cp_chunks):
                    chunks.append({
                        "chunk_id": f"{feedback_id}_courseplan_{cp_idx}_{i}",
                        "text": chunk,
                        "content_type": "course_plan",
                        "metadata": {**metadata, "course_plan_id": course_plan.get("course_plan_id", "")},
                        "original_feedback_id": feedback_id
                    })
        
        return chunks
    
    def _create_metadata_context(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive metadata context from entry"""
        metadata = {}
        
        # Feedback basic info
        feedback_data = entry.get("TrainersFeedbackLog", {})
        metadata.update({
            "feedback_date": feedback_data.get("feedback_date", ""),
            "total_hours_spent": feedback_data.get("Total_hours_Spent", ""),
            "loggedby": feedback_data.get("loggedby", ""),
            "bctm_id": feedback_data.get("bctm_id", "")
        })
        
        # Batch information
        batch_data = entry.get("Batch", {})
        if batch_data:
            metadata.update({
                "batch_id": batch_data.get("batch_id", ""),
                "batch_type": batch_data.get("batch_type", ""),
                "batch_status": batch_data.get("status", "")
            })
        
        # Centre information
        centre_data = entry.get("Centre", {})
        if centre_data:
            metadata.update({
                "centre_id": centre_data.get("centre_id", ""),
                "centre_name": centre_data.get("centre_name", ""),
                "district": centre_data.get("district", ""),
                "state": centre_data.get("state", ""),
                "village": centre_data.get("village", "")
            })
        
        # Course information
        course_data = entry.get("Course", {})
        if course_data:
            metadata.update({
                "course_id": course_data.get("course_id", ""),
                "course_name": course_data.get("course_name", ""),
                "course_description": course_data.get("course_description", "")
            })
        
        # Project information
        project_data = entry.get("Project", {})
        if project_data:
            metadata.update({
                "project_id": project_data.get("project_id", ""),
                "project_name": project_data.get("project_name", ""),
                "project_description": project_data.get("project_desc", "")
            })
        
        # User information (trainer from BatchCourse)
        user_data = entry.get("User", {})
        if user_data:
            metadata.update({
                "user_id": user_data.get("user_id", ""),
                "user_name": user_data.get("full_name", user_data.get("name", "")),
                "user_role": user_data.get("utype", user_data.get("role", ""))
            })
        
        # LoggedBy User information (who logged the feedback)
        loggedby_user_data = entry.get("LoggedByUser", {})
        if loggedby_user_data:
            metadata.update({
                "logged_by_user_id": loggedby_user_data.get("user_id", ""),
                "logged_by_user_name": loggedby_user_data.get("full_name", loggedby_user_data.get("name", "")),
                "logged_by_user_role": loggedby_user_data.get("utype", loggedby_user_data.get("role", ""))
            })
        
        return metadata
    
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """Split text into chunks with overlap"""
        if not text or len(text.strip()) == 0:
            return []
        
        # Simple chunking by character count
        text = text.strip()
        if len(text) <= self.max_chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.max_chunk_size
            
            # If we're not at the end, try to break at a word boundary
            if end < len(text):
                # Look for the last space before the max chunk size
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = max(start + 1, end - self.chunk_overlap)
            
            # Prevent infinite loop
            if start >= len(text):
                break
        
        return chunks