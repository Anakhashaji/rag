import pyrebase
import logging
from typing import Dict, List, Optional, Any
from config import Config

logger = logging.getLogger(__name__)

class FirebaseService:
    def __init__(self):
        """Initialize Firebase connection"""
        try:
            self.firebase = pyrebase.initialize_app(Config.FIREBASE_CONFIG)
            self.db = self.firebase.database()
            logger.info("Firebase connection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {str(e)}")
            raise
    
    def get_all_feedback_with_metadata(self) -> List[Dict[str, Any]]:
        """Fetch all feedback entries with their complete metadata"""
        try:
            logger.info("Fetching all feedback data with metadata...")
            
            feedback_entries = []
            
            # Get all feedback entries
            feedback_logs = self.db.child("TrainersFeedbackLog").get().val()
            if not feedback_logs:
                logger.warning("No feedback logs found")
                return []
            
            # Handle both dict and list responses
            if isinstance(feedback_logs, list):
                for i, feedback_data in enumerate(feedback_logs):
                    if feedback_data:
                        try:
                            complete_feedback = self._get_complete_feedback_data(str(i), feedback_data)
                            if complete_feedback:
                                feedback_entries.append(complete_feedback)
                        except Exception as e:
                            logger.error(f"Error processing feedback {i}: {str(e)}")
                            continue
            elif isinstance(feedback_logs, dict):
                for feedback_id, feedback_data in feedback_logs.items():
                    try:
                        complete_feedback = self._get_complete_feedback_data(feedback_id, feedback_data)
                        if complete_feedback:
                            feedback_entries.append(complete_feedback)
                    except Exception as e:
                        logger.error(f"Error processing feedback {feedback_id}: {str(e)}")
                        continue
            
            logger.info(f"Successfully fetched {len(feedback_entries)} feedback entries")
            return feedback_entries
            
        except Exception as e:
            logger.error(f"Error fetching feedback data: {str(e)}")
            raise
    
    def _get_complete_feedback_data(self, feedback_id: str, feedback_data: Dict) -> Optional[Dict[str, Any]]:
        """Get complete feedback data with all related metadata"""
        try:
            result = {
                "feedback_id": feedback_id,
                "TrainersFeedbackLog": feedback_data
            }
            
            # Get BatchCourse data
            bctm_id = feedback_data.get("bctm_id")
            if bctm_id:
                batch_course = self._find_batch_course_by_bctm_id(bctm_id)
                result["BatchCourse"] = batch_course
                
                if batch_course:
                    # Get Batch data
                    batch_id = batch_course.get("batch_id")
                    if batch_id:
                        batch = self._find_batch_by_id(batch_id)
                        result["Batch"] = batch
                        
                        # Get Centre data
                        if batch and batch.get("centre_id"):
                            centre = self._find_centre_by_id(batch["centre_id"])
                            result["Centre"] = centre
                    
                    # Get Course data
                    course_id = batch_course.get("course_id")
                    if course_id:
                        course = self._find_course_by_id(course_id)
                        result["Course"] = course
                    
                    # Get Project data
                    project_id = batch_course.get("project_id")
                    if project_id:
                        project = self._find_project_by_id(project_id)
                        result["Project"] = project
                    
                    # Get User data (trainer user from BatchCourse)
                    user_id = batch_course.get("user_id")
                    if user_id:
                        user = self._find_user_by_id(user_id)
                        result["User"] = user
            
            # Get LoggedBy User data (who logged the feedback)
            loggedby_user_id = feedback_data.get("loggedby")
            if loggedby_user_id:
                loggedby_user = self._find_user_by_id(loggedby_user_id)
                result["LoggedByUser"] = loggedby_user
            
            # Get CoursePlans data
            course_plan_ids = feedback_data.get("course_plan_id", [])
            if course_plan_ids:
                course_plans = self._get_course_plans_by_ids(course_plan_ids)
                result["CoursePlans"] = course_plans
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting complete feedback data for {feedback_id}: {str(e)}")
            return None
    
    def _find_batch_course_by_bctm_id(self, bctm_id: str) -> Optional[Dict]:
        """Find BatchCourse by bctm_id"""
        try:
            batch_courses = self.db.child("BatchCourse").get().val()
            if batch_courses:
                if isinstance(batch_courses, list):
                    for bc in batch_courses:
                        if bc and bc.get("bctm_id") == bctm_id:
                            return bc
                elif isinstance(batch_courses, dict):
                    for _, bc in batch_courses.items():
                        if bc.get("bctm_id") == bctm_id:
                            return bc
        except Exception as e:
            logger.error(f"Error finding BatchCourse by bctm_id {bctm_id}: {str(e)}")
        return None
    
    def _find_batch_by_id(self, batch_id: str) -> Optional[Dict]:
        """Find Batch by batch_id"""
        try:
            batches = self.db.child("Batch").get().val()
            if batches:
                if isinstance(batches, list):
                    for batch in batches:
                        if batch and batch.get("batch_id") == batch_id:
                            return batch
                elif isinstance(batches, dict):
                    for _, batch in batches.items():
                        if batch.get("batch_id") == batch_id:
                            return batch
        except Exception as e:
            logger.error(f"Error finding Batch by id {batch_id}: {str(e)}")
        return None
    
    def _find_centre_by_id(self, centre_id: str) -> Optional[Dict]:
        """Find Centre by centre_id"""
        try:
            centres = self.db.child("Centre").get().val()
            if centres:
                if isinstance(centres, list):
                    for centre in centres:
                        if centre and centre.get("centre_id") == centre_id:
                            return centre
                elif isinstance(centres, dict):
                    for _, centre in centres.items():
                        if centre.get("centre_id") == centre_id:
                            return centre
        except Exception as e:
            logger.error(f"Error finding Centre by id {centre_id}: {str(e)}")
        return None
    
    def _find_course_by_id(self, course_id: str) -> Optional[Dict]:
        """Find Course by course_id"""
        try:
            courses = self.db.child("Course").get().val()
            if courses:
                if isinstance(courses, list):
                    for course in courses:
                        if course and course.get("course_id") == course_id:
                            return course
                elif isinstance(courses, dict):
                    for _, course in courses.items():
                        if course.get("course_id") == course_id:
                            return course
        except Exception as e:
            logger.error(f"Error finding Course by id {course_id}: {str(e)}")
        return None
    
    def _find_project_by_id(self, project_id: str) -> Optional[Dict]:
        """Find Project by project_id"""
        try:
            projects = self.db.child("Project").get().val()
            if projects:
                if isinstance(projects, list):
                    for project in projects:
                        if project and project.get("project_id") == project_id:
                            return project
                elif isinstance(projects, dict):
                    for _, project in projects.items():
                        if project.get("project_id") == project_id:
                            return project
        except Exception as e:
            logger.error(f"Error finding Project by id {project_id}: {str(e)}")
        return None
    
    def _find_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Find User by user_id"""
        try:
            users = self.db.child("User").get().val()
            if users:
                if isinstance(users, list):
                    for user in users:
                        if user and user.get("user_id") == user_id:
                            return user
                elif isinstance(users, dict):
                    for _, user in users.items():
                        if user.get("user_id") == user_id:
                            return user
        except Exception as e:
            logger.error(f"Error finding User by id {user_id}: {str(e)}")
        return None
    
    def _get_course_plans_by_ids(self, course_plan_ids: List[str]) -> List[Dict]:
        """Get CoursePlans by list of course_plan_ids"""
        try:
            course_plans = []
            all_plans = self.db.child("CoursePlan").get().val()
            if all_plans:
                if isinstance(all_plans, list):
                    for plan in all_plans:
                        if plan and plan.get("course_plan_id") in course_plan_ids:
                            course_plans.append(plan)
                elif isinstance(all_plans, dict):
                    for cp_id in course_plan_ids:
                        for _, plan in all_plans.items():
                            if plan.get("course_plan_id") == cp_id:
                                course_plans.append(plan)
                                break
            return course_plans
        except Exception as e:
            logger.error(f"Error getting CoursePlans by ids {course_plan_ids}: {str(e)}")
            return []