"""
Content generator service using Meta AI to create unique content from news
"""

import os
import random
from typing import Dict, Any, List
from meta_ai_api import MetaAI
from dotenv import load_dotenv

load_dotenv()

class ContentGenerator:
    def __init__(self):
        self.ai = MetaAI()
        
        # Content templates for variety - concise Facebook posts with critical analysis
        self.templates = [
            """Create a concise Facebook post about this news: {title}

IMPORTANT: Keep it under 800 characters total.

Format:
🔥 Brief headline with emoji
📰 2 sentences max explaining key points
🤔 Critical analysis (1-2 sentences):
- Congress news: Critique their approach
- Bangladesh/Pakistan: Constructive criticism
💭 One engaging question
#hashtags (max 3)

Keep it punchy and engaging!""",

            """Write a short Facebook post for: {title}

LIMIT: 800 characters maximum.

Structure:
🚨 Catchy opener
📝 Brief summary (1-2 sentences)
🔍 Quick critical take:
- Congress: Point out policy issues
- Bangladesh/Pakistan: Critique situation
🤔 Engaging question
#hashtags

Make every word count!""",

            """Transform this into a concise Facebook post: {title}

MAX LENGTH: 800 characters.

Format:
- Relevant emoji + headline
- Key points (2 sentences max)
- Critical analysis (1 sentence)
- Question for engagement
- 2-3 hashtags

Be direct and impactful!""",

            """Create a short, engaging Facebook post: {title}

STRICT LIMIT: 800 characters.

Include:
🔥 Eye-catching start
📰 Essential details only
🤔 Critical perspective (brief)
💭 One question
#hashtags

Quality over quantity!""",

            """Write a punchy Facebook post for: {title}

MAXIMUM: 800 characters total.

Structure:
- Emoji + headline
- Core message (concise)
- Critical angle (short)
- Engagement question
- Hashtags

Make it memorable and shareable!"""
        ]
        
        # Hashtag categories
        self.hashtags = {
            'general': ['#BreakingNews', '#India', '#News', '#Update', '#Today'],
            'politics': ['#Politics', '#Government', '#Policy', '#Democracy'],
            'business': ['#Business', '#Economy', '#Finance', '#Market'],
            'technology': ['#Technology', '#Tech', '#Innovation', '#Digital'],
            'sports': ['#Sports', '#Cricket', '#Football', '#Olympics'],
            'entertainment': ['#Entertainment', '#Bollywood', '#Movies', '#Celebrity'],
            'health': ['#Health', '#Healthcare', '#Medical', '#Wellness'],
            'education': ['#Education', '#Students', '#Learning', '#Schools']
        }
    
    def generate_content_from_news(self, article: Dict[str, Any]) -> str:
        """Generate unique content from a news article using Meta AI"""
        try:
            title = article.get('title', '')
            description = article.get('description', '')
            category = article.get('category', ['general'])
            country = article.get('country', [''])
            
            # Select a random template
            template = random.choice(self.templates)
            
            # Create the prompt
            prompt = template.format(title=title)
            
            # Add context if description is available
            if description:
                prompt += f" Context: {description[:200]}..."
            
            # Add country-specific critical analysis instructions
            if any('bangladesh' in str(c).lower() for c in country):
                prompt += "\n\nSPECIAL INSTRUCTION: This is news from Bangladesh. Please include constructive criticism of the political/social situation in Bangladesh, highlighting issues like governance, human rights, or economic challenges."
            elif any('pakistan' in str(c).lower() for c in country):
                prompt += "\n\nSPECIAL INSTRUCTION: This is news from Pakistan. Please include constructive criticism of the situation in Pakistan, focusing on governance issues, economic challenges, or social problems."
            elif 'congress' in title.lower() or 'congress' in description.lower():
                prompt += "\n\nSPECIAL INSTRUCTION: This involves the Congress party in India. Please provide logical criticism of their policies, decisions, or actions. Point out flaws in their approach and suggest better alternatives."
            
            # Generate content using Meta AI
            print(f"🤖 Generating content for: {title[:50]}...")
            response = self.ai.prompt(message=prompt)
            
            # Extract the generated text
            generated_content = response.get('message', '') if isinstance(response, dict) else str(response)
            
            # Add relevant hashtags
            hashtags = self._get_relevant_hashtags(category, title.lower())
            
            # Combine content with hashtags
            final_content = f"{generated_content}\n\n{' '.join(hashtags)}"
            
            print(f"✅ Generated content: {final_content[:100]}...")
            return final_content
            
        except Exception as e:
            print(f"❌ Error generating content: {e}")
            # Fallback to simple content
            return self._create_fallback_content(article)
    
    def _get_relevant_hashtags(self, categories: List[str], title_text: str) -> List[str]:
        """Get relevant hashtags based on article category and content"""
        selected_hashtags = []
        
        # Always add general hashtags
        selected_hashtags.extend(random.sample(self.hashtags['general'], 2))
        
        # Add category-specific hashtags
        for category in categories:
            if category.lower() in self.hashtags:
                selected_hashtags.extend(random.sample(self.hashtags[category.lower()], 1))
        
        # Add hashtags based on keywords in title
        keyword_mapping = {
            'cricket': ['#Cricket', '#Sports'],
            'bollywood': ['#Bollywood', '#Entertainment'],
            'election': ['#Election', '#Politics'],
            'covid': ['#COVID19', '#Health'],
            'economy': ['#Economy', '#Business'],
            'technology': ['#Technology', '#Innovation'],
            'education': ['#Education', '#Students']
        }
        
        for keyword, tags in keyword_mapping.items():
            if keyword in title_text:
                selected_hashtags.extend(random.sample(tags, 1))
        
        # Remove duplicates and limit to 5 hashtags
        unique_hashtags = list(dict.fromkeys(selected_hashtags))[:5]
        return unique_hashtags
    
    def _create_fallback_content(self, article: Dict[str, Any]) -> str:
        """Create structured fallback content when AI generation fails"""
        title = article.get('title', 'Breaking News')
        description = article.get('description', '')
        
        # Structured fallback templates with proper formatting
        fallback_templates = [
            f"📰 BREAKING NEWS\n\n{title}\n\n💭 What are your thoughts on this development?\n\nStay informed with the latest updates!",
            
            f"🔥 LATEST UPDATE\n\n{title}\n\n📝 Key points:\n• Important news development\n• Stay tuned for more updates\n\n💬 Share your views in the comments!",
            
            f"📢 NEWS ALERT\n\n{title}\n\n🌍 This story is developing...\n\n❓ What do you think about this?",
            
            f"⚡ JUST IN\n\n{title}\n\n📊 Quick Summary:\n→ Breaking news story\n→ More details to follow\n\n🗣️ Let us know your opinion!"
        ]
        
        content = random.choice(fallback_templates)
        
        # Add basic hashtags with proper spacing
        basic_hashtags = ['#News', '#BreakingNews', '#Update', '#Latest']
        content += f"\n\n{' '.join(random.sample(basic_hashtags, 3))}"
        
        return content
    
    def enhance_content_with_context(self, content: str, article: Dict[str, Any]) -> str:
        """Enhance generated content with additional context"""
        try:
            state = article.get('target_state', '')
            source = article.get('source_id', '')
            
            enhancement_prompt = f"""
            Enhance this social media post to make it more engaging and add local context for {state}:
            
            Original post: {content}
            
            Make it more compelling while keeping it under 250 characters.
            """
            
            response = self.ai.prompt(message=enhancement_prompt)
            enhanced_content = response.get('message', content) if isinstance(response, dict) else str(response)
            
            return enhanced_content
            
        except Exception as e:
            print(f"⚠️ Could not enhance content: {e}")
            return content
    
    def generate_multiple_variants(self, article: Dict[str, Any], count: int = 3) -> List[str]:
        """Generate multiple content variants for A/B testing"""
        variants = []
        
        for i in range(count):
            try:
                content = self.generate_content_from_news(article)
                variants.append(content)
            except Exception as e:
                print(f"⚠️ Failed to generate variant {i+1}: {e}")
                continue
        
        return variants if variants else [self._create_fallback_content(article)]
