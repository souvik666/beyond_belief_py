"""
Comprehensive logging service for Facebook News Automation
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

class AutomationLogger:
    def __init__(self):
        # Create db folder structure
        self.db_folder = Path("db")
        self.db_folder.mkdir(exist_ok=True)
        
        # Create subfolders
        (self.db_folder / "posts").mkdir(exist_ok=True)
        (self.db_folder / "logs").mkdir(exist_ok=True)
        (self.db_folder / "cache").mkdir(exist_ok=True)
        (self.db_folder / "errors").mkdir(exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # Posts database file
        self.posts_db_file = self.db_folder / "posts" / "posted_articles.json"
        self.session_log_file = self.db_folder / "logs" / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Initialize session log
        self.session_data = {
            'session_start': datetime.now().isoformat(),
            'steps': [],
            'posts': [],
            'errors': [],
            'statistics': {
                'total_steps': 0,
                'successful_posts': 0,
                'failed_posts': 0,
                'api_calls': 0
            }
        }
    
    def setup_logging(self):
        """Setup Python logging"""
        log_file = self.db_folder / "logs" / f"automation_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def log_step(self, step_name: str, details: Dict[str, Any] = None, status: str = "info"):
        """Log each step of the automation process"""
        step_data = {
            'timestamp': datetime.now().isoformat(),
            'step_name': step_name,
            'status': status,
            'details': details or {}
        }
        
        self.session_data['steps'].append(step_data)
        self.session_data['statistics']['total_steps'] += 1
        
        # Log to file and console
        log_message = f"STEP: {step_name} - Status: {status.upper()}"
        if details:
            log_message += f" - Details: {json.dumps(details, indent=2)}"
        
        if status == "error":
            self.logger.error(log_message)
            self.session_data['errors'].append(step_data)
        elif status == "warning":
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        # Save session data
        self._save_session_data()
        
        print(f"📝 {step_name} - {status.upper()}")
        if details:
            for key, value in details.items():
                print(f"   {key}: {value}")
    
    def log_api_call(self, url: str, query: str, country: str, response_status: int, articles_count: int = 0):
        """Log API calls"""
        api_data = {
            'timestamp': datetime.now().isoformat(),
            'url': url,
            'query': query,
            'country': country,
            'response_status': response_status,
            'articles_received': articles_count
        }
        
        self.session_data['statistics']['api_calls'] += 1
        
        self.log_step("API_CALL", api_data, "success" if response_status == 200 else "error")
    
    def log_post(self, article: Dict[str, Any], content: str, facebook_response: Dict[str, Any], success: bool = True):
        """Log successful Facebook posts"""
        post_data = {
            'timestamp': datetime.now().isoformat(),
            'article_title': article.get('title', ''),
            'article_url': article.get('link', ''),
            'query_used': article.get('query_used', ''),
            'country': article.get('location', ''),
            'generated_content': content,
            'facebook_post_id': facebook_response.get('id', ''),
            'facebook_response': facebook_response,
            'success': success,
            'image_url': article.get('image_url', ''),
            'has_image': bool(article.get('image_url'))
        }
        
        # Add to session posts
        self.session_data['posts'].append(post_data)
        
        if success:
            self.session_data['statistics']['successful_posts'] += 1
            # Save to posts database
            self._save_to_posts_db(post_data)
            self.log_step("FACEBOOK_POST_SUCCESS", {
                'post_id': facebook_response.get('id', ''),
                'title': article.get('title', '')[:50] + '...'
            }, "success")
        else:
            self.session_data['statistics']['failed_posts'] += 1
            self.log_step("FACEBOOK_POST_FAILED", {
                'title': article.get('title', '')[:50] + '...',
                'error': str(facebook_response)
            }, "error")
    
    def log_content_generation(self, article: Dict[str, Any], generated_content: str, success: bool = True):
        """Log AI content generation"""
        content_data = {
            'article_title': article.get('title', ''),
            'generated_content': generated_content,
            'content_length': len(generated_content),
            'query_used': article.get('query_used', ''),
            'success': success
        }
        
        self.log_step("AI_CONTENT_GENERATION", content_data, "success" if success else "error")
    
    def log_cache_operation(self, operation: str, details: Dict[str, Any]):
        """Log cache operations"""
        cache_data = {
            'operation': operation,
            'details': details
        }
        
        self.log_step(f"CACHE_{operation.upper()}", cache_data)
    
    def log_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """Log errors with context"""
        error_data = {
            'error_type': error_type,
            'error_message': str(error_message),
            'context': context or {}
        }
        
        # Save detailed error to separate file
        error_file = self.db_folder / "errors" / f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(error_file, 'w', encoding='utf-8') as f:
            json.dump(error_data, f, indent=2, ensure_ascii=False)
        
        self.log_step("ERROR", error_data, "error")
    
    def _save_to_posts_db(self, post_data: Dict[str, Any]):
        """Save post to posts database"""
        try:
            # Load existing posts
            if self.posts_db_file.exists():
                with open(self.posts_db_file, 'r', encoding='utf-8') as f:
                    posts_db = json.load(f)
            else:
                posts_db = []
            
            # Add new post
            posts_db.append(post_data)
            
            # Save updated database
            with open(self.posts_db_file, 'w', encoding='utf-8') as f:
                json.dump(posts_db, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.log_error("DATABASE_SAVE_ERROR", str(e), {'post_data': post_data})
    
    def _save_session_data(self):
        """Save current session data"""
        try:
            with open(self.session_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save session data: {e}")
    
    def get_posts_statistics(self) -> Dict[str, Any]:
        """Get statistics from posts database"""
        try:
            if not self.posts_db_file.exists():
                return {'total_posts': 0, 'posts_today': 0}
            
            with open(self.posts_db_file, 'r', encoding='utf-8') as f:
                posts_db = json.load(f)
            
            today = datetime.now().date()
            posts_today = sum(1 for post in posts_db 
                            if datetime.fromisoformat(post['timestamp']).date() == today)
            
            return {
                'total_posts': len(posts_db),
                'posts_today': posts_today,
                'last_post': posts_db[-1]['timestamp'] if posts_db else None
            }
            
        except Exception as e:
            self.log_error("STATS_ERROR", str(e))
            return {'total_posts': 0, 'posts_today': 0}
    
    def finalize_session(self):
        """Finalize the current session"""
        self.session_data['session_end'] = datetime.now().isoformat()
        self.session_data['session_duration'] = str(
            datetime.fromisoformat(self.session_data['session_end']) - 
            datetime.fromisoformat(self.session_data['session_start'])
        )
        
        self._save_session_data()
        
        # Print session summary
        stats = self.session_data['statistics']
        print(f"\n📊 Session Summary:")
        print(f"   Duration: {self.session_data['session_duration']}")
        print(f"   Total steps: {stats['total_steps']}")
        print(f"   API calls: {stats['api_calls']}")
        print(f"   Successful posts: {stats['successful_posts']}")
        print(f"   Failed posts: {stats['failed_posts']}")
        print(f"   Errors: {len(self.session_data['errors'])}")
        print(f"   Session log: {self.session_log_file}")
