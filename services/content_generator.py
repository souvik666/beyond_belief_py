"""
Content generator service using Meta AI to create unique content from news and Reddit posts
"""

import os
import random
from typing import Dict, Any, List
from meta_ai_api import MetaAI
from dotenv import load_dotenv
from .reddit_service import RedditService
load_dotenv()

class ContentGenerator:
    def __init__(self):
        self.ai = MetaAI()
        
        # Initialize Reddit service for fetching posts
        try:
            self.reddit_service = RedditService()
            print("✅ Reddit service initialized in ContentGenerator")
        except Exception as e:
            print(f"⚠️ Reddit service not available in ContentGenerator: {e}")
            self.reddit_service = None
        
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
    
    def generate_content_from_news(self, article: Dict[str, Any], platform: str = "facebook") -> str:
        """Generate unique content from a news article using Meta AI for specific platform"""
        try:
            title = article.get('title', '')
            description = article.get('description', '')
            category = article.get('category', ['general'])
            country = article.get('country', [''])
            
            # Platform-specific templates
            if platform.lower() == "twitter":
                template = self._get_twitter_template()
                char_limit = 280
                platform_name = "Twitter"
            else:
                template = random.choice(self.templates)
                char_limit = 800
                platform_name = "Facebook"
            
            # Create the prompt
            prompt = template.format(title=title)
            
            # Add platform-specific instructions
            if platform.lower() == "twitter":
                prompt += f"\n\nIMPORTANT: This is for {platform_name}. Keep it under {char_limit} characters including hashtags. Be concise and punchy."
            else:
                prompt += f"\n\nIMPORTANT: This is for {platform_name}. Keep it under {char_limit} characters total."
            
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
            
            # Generate content using Meta AI with delay
            print(f"🤖 Generating {platform_name} content for: {title[:50]}...")
            
            # Add delay before LLM call to prevent rate limiting
            import time
            time.sleep(2)  # 2 second delay before each LLM call
            
            response = self.ai.prompt(message=prompt)
            
            # Extract the generated text
            generated_content = response.get('message', '') if isinstance(response, dict) else str(response)
            
            # Let the AI decide hashtags - they should already be included in generated_content
            # No need to add separate hashtags since the prompt asks for hashtags
            final_content = generated_content
            
            # Ensure character limit compliance
            if len(final_content) > char_limit:
                print(f"⚠️ Content too long ({len(final_content)} chars), truncating for {platform_name}...")
                final_content = final_content[:char_limit-3] + "..."
            
            print(f"✅ Generated {platform_name} content ({len(final_content)} chars): {final_content[:100]}...")
            return final_content
            
        except Exception as e:
            print(f"❌ Error generating content: {e}")
            # Fallback to simple content
            return self._create_fallback_content(article, platform)

    def _get_twitter_template(self) -> str:
        """Get Twitter-specific template"""
        twitter_templates = [
            "Create a punchy Twitter post about: {title}\n\nMAX 280 chars including hashtags. Format:\n🔥 Brief headline\n📰 Key point (1 sentence)\n🤔 Critical take\n#hashtags",
            
            "Write a Twitter-ready post for: {title}\n\nMAX 280 chars total. Structure:\n⚡ Eye-catching opener\n📝 Main point\n💭 Question or critique\n#hashtags",
            
            "Create a concise tweet about: {title}\n\nSTRICT 280 char limit. Include:\n- Relevant emoji\n- Brief summary\n- Critical angle\n- 2-3 hashtags",
            
            "Transform into a Twitter post: {title}\n\nUnder 280 chars. Format:\n🚨 Attention grabber\n📊 Key fact\n🔍 Critical insight\n#hashtags"
        ]
        return random.choice(twitter_templates)

    def generate_dual_platform_content(self, article: Dict[str, Any]) -> Dict[str, str]:
        """Generate content for both Facebook and Twitter"""
        try:
            print(f"🔄 Generating dual platform content...")
            
            # Generate Facebook content
            facebook_content = self.generate_content_from_news(article, "facebook")
            
            # Wait longer between platform content generation for better quality
            import time
            print("⏳ Waiting 3 seconds before generating Twitter content...")
            time.sleep(3)  # 3 second delay between platform content generation
            
            # Generate Twitter content
            twitter_content = self.generate_content_from_news(article, "twitter")
            
            return {
                'facebook': facebook_content,
                'twitter': twitter_content
            }
            
        except Exception as e:
            print(f"❌ Error generating dual platform content: {e}")
            # Fallback
            fallback_fb = self._create_fallback_content(article, "facebook")
            fallback_tw = self._create_fallback_content(article, "twitter")
            return {
                'facebook': fallback_fb,
                'twitter': fallback_tw
            }
    
    def _get_relevant_hashtags(self, categories: List[str], title_text: str, platform: str = "facebook") -> List[str]:
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
        
        # Remove duplicates and limit to 2 hashtags for professional look
        unique_hashtags = list(dict.fromkeys(selected_hashtags))[:2]
        return unique_hashtags
    
    def _create_fallback_content(self, article: Dict[str, Any], platform: str = "facebook") -> str:
        """Create structured fallback content when AI generation fails"""
        title = article.get('title', 'Breaking News')
        description = article.get('description', '')
        
        # Platform-specific fallback content
        if platform.lower() == "twitter":
            # Twitter fallback (280 chars max)
            twitter_templates = [
                f"🚨 {title[:100]}...\n\n💭 Thoughts?\n\n#News #Breaking",
                f"📰 {title[:120]}...\n\n#Update #Latest",
                f"⚡ {title[:130]}...\n\n#News #Today"
            ]
            content = random.choice(twitter_templates)
            
            # Ensure Twitter character limit
            if len(content) > 280:
                content = content[:277] + "..."
                
        else:
            # Facebook fallback
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

    # ---------------------------
    # Reddit Content Generation
    # ---------------------------

    def generate_content_from_reddit(self, reddit_post: Dict[str, Any], platform: str = "facebook") -> str:
        """Generate unique content from a Reddit post using Meta AI for Facebook posting"""
        try:
            title = reddit_post.get('title', '')
            selftext = reddit_post.get('selftext', '')
            subreddit = reddit_post.get('subreddit', '')
            score = reddit_post.get('score', 0)
            
            # Reddit-specific templates for Facebook - Professional & SEO-friendly
            reddit_templates = [
                """Create a professional Facebook post based on this Reddit story: {title}

IMPORTANT: Keep it under 800 characters total. Make it Facebook SEO-friendly for maximum reach.

Format:
- Strong, keyword-rich headline (no emojis)
- Brief summary of the story (2-3 sentences)
- Your professional analysis or insight
- Engaging question to encourage comments and shares
- Only 1-2 relevant hashtags

Focus on creating viral, shareable content that drives engagement and helps build a following.""",

                """Transform this Reddit post into professional Facebook content: {title}

LIMIT: 800 characters maximum. Optimize for Facebook algorithm and engagement.

Structure:
- Compelling opener with keywords
- Key story points (clear and concise)
- Professional commentary or unique perspective
- Call-to-action question for audience engagement
- Maximum 2 hashtags

Create content that encourages likes, comments, and shares for maximum Facebook reach.""",

                """Create a Facebook post from this Reddit story: {title}

MAX LENGTH: 800 characters. Focus on Facebook SEO and viral potential.

Include:
- Attention-grabbing headline with relevant keywords
- Story summary (engaging but professional)
- Your expert take or analysis
- Question that drives discussion
- 1-2 strategic hashtags

Make it professional, shareable, and optimized for Facebook's algorithm.""",

                """Turn this Reddit story into viral Facebook content: {title}

STRICT LIMIT: 800 characters total. Optimize for Facebook fame and reach.

Format:
- Hook with trending keywords
- Story essence (professional tone)
- Your unique insight or perspective
- Engagement-driving question
- 1-2 powerful hashtags

Create content that gets shared, commented on, and helps build your Facebook presence.""",

                """Create professional Facebook content from this Reddit post: {title}

MAX 800 characters including hashtags. Focus on building your Facebook following.

Structure:
- Strong opener (no emojis, keyword-rich)
- Core story points (clear and engaging)
- Professional commentary
- Question that encourages interaction
- 1-2 relevant hashtags

Make it authoritative, shareable, and designed to grow your Facebook audience."""
            ]
            
            # Select template
            template = random.choice(reddit_templates)
            char_limit = 800
            
            # Create the prompt
            prompt = template.format(title=title)
            
            # Add context from selftext if available
            if selftext and len(selftext.strip()) > 0:
                prompt += f"\n\nStory context: {selftext[:300]}..."
            
            # Add subreddit context
            prompt += f"\n\nThis was posted in r/{subreddit} with {score} upvotes."
            prompt += f"\n\nIMPORTANT: This is for Facebook. Keep it under {char_limit} characters total. Create engaging content that highlights what makes this story interesting and worth sharing."
            
            # Generate content using Meta AI with delay
            print(f"🤖 Generating Facebook content for Reddit post: {title[:50]}...")
            
            # Add delay before LLM call to prevent rate limiting
            import time
            time.sleep(2)
            
            response = self.ai.prompt(message=prompt)
            
            # Extract the generated text
            generated_content = response.get('message', '') if isinstance(response, dict) else str(response)
            
            # Let the AI decide hashtags - they should already be included in generated_content
            # No need to add separate hashtags since the prompt asks for 1-2 hashtags
            final_content = generated_content
            
            # Ensure character limit compliance
            if len(final_content) > char_limit:
                print(f"⚠️ Content too long ({len(final_content)} chars), truncating...")
                final_content = final_content[:char_limit-3] + "..."
            
            print(f"✅ Generated Facebook Reddit content ({len(final_content)} chars): {final_content[:100]}...")
            return final_content
            
        except Exception as e:
            print(f"❌ Error generating Reddit content: {e}")
            return self._create_reddit_fallback_content(reddit_post)

    def fetch_and_cache_reddit_posts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch paranormal Reddit posts and cache them"""
        if not self.reddit_service:
            print("❌ Reddit service not available")
            return []
        
        try:
            print(f"🔍 Fetching {limit} paranormal Reddit posts...")
            
            # Get paranormal trending posts
            trending_posts = self.reddit_service.get_paranormal_trending(limit=limit//10)
            
            # Flatten the posts from all subreddits
            all_posts = []
            for subreddit, posts in trending_posts.items():
                for post in posts:
                    # Add source information
                    post['source'] = 'reddit'
                    post['source_subreddit'] = subreddit
                    post['content_type'] = 'reddit_post'
                    all_posts.append(post)
            
            # Sort by score (popularity)
            all_posts.sort(key=lambda x: x.get('score', 0), reverse=True)
            
            # Limit to requested number
            selected_posts = all_posts[:limit]
            
            print(f"✅ Fetched {len(selected_posts)} Reddit posts from {len(trending_posts)} subreddits")
            return selected_posts
            
        except Exception as e:
            print(f"❌ Error fetching Reddit posts: {e}")
            return []

    def _get_reddit_hashtags(self, subreddit: str, title_text: str) -> List[str]:
        """Get relevant hashtags for Reddit content - Enhanced with video-rich subreddits"""
        reddit_hashtags = {
            # Original paranormal subs
            'paranormal': ['#Paranormal', '#Ghost', '#Supernatural'],
            'ghosts': ['#Ghost', '#Haunted', '#Paranormal'],
            'ufos': ['#UFO', '#Aliens', '#Extraterrestrial'],
            'aliens': ['#Aliens', '#UFO', '#Space'],
            'cryptids': ['#Cryptids', '#Bigfoot', '#Mystery'],
            'truecreepy': ['#Creepy', '#Horror', '#Scary'],
            'highstrangeness': ['#Strange', '#Unexplained', '#Mystery'],
            'glitch_in_the_matrix': ['#GlitchInTheMatrix', '#Reality', '#Strange'],
            'nosleep': ['#Horror', '#Scary', '#Creepy'],
            'letsnotmeet': ['#TrueStory', '#Scary', '#RealLife'],
            
            # Video-rich paranormal subreddits
            'paranormalvideos': ['#ParanormalVideo', '#CaughtOnCamera', '#Supernatural'],
            'ghostvideos': ['#GhostVideo', '#Haunted', '#Paranormal'],
            'ufovideos': ['#UFOVideo', '#Aliens', '#Sighting'],
            'cryptidsightings': ['#CryptidSighting', '#Bigfoot', '#Mystery'],
            'securitycameras': ['#SecurityCam', '#CaughtOnCamera', '#Surveillance'],
            'caughtoncamera': ['#CaughtOnCamera', '#Video', '#Unexplained'],
            'unexplainedphotos': ['#Unexplained', '#Mystery', '#Evidence'],
            'trailcam': ['#TrailCam', '#Wildlife', '#Cryptids'],
            'dashcam': ['#DashCam', '#Video', '#Strange'],
            
            # More active paranormal communities
            'thetruthishere': ['#TrueStory', '#Paranormal', '#RealExperience'],
            'humanoidencounters': ['#Humanoid', '#Encounter', '#Strange'],
            'crawlersightings': ['#Crawler', '#Cryptids', '#Sighting'],
            'dogman': ['#Dogman', '#Cryptids', '#Sighting'],
            'bigfoot': ['#Bigfoot', '#Sasquatch', '#Cryptids'],
            'skinwalkers': ['#Skinwalker', '#Supernatural', '#Native'],
            'wendigo': ['#Wendigo', '#Cryptids', '#Horror'],
            'missing411': ['#Missing411', '#Mystery', '#Unexplained'],
            
            # Horror and creepy video content
            'creepyvideos': ['#CreepyVideo', '#Horror', '#Disturbing'],
            'disturbingmovies': ['#Disturbing', '#Horror', '#Video'],
            'unsolvedmysteries': ['#UnsolvedMystery', '#Mystery', '#Investigation'],
            'rbi': ['#Investigation', '#Mystery', '#Analysis'],
            'mystery': ['#Mystery', '#Unexplained', '#Investigation'],
            
            # Supernatural and occult
            'occult': ['#Occult', '#Supernatural', '#Ritual'],
            'witchcraft': ['#Witchcraft', '#Magic', '#Supernatural'],
            'demons': ['#Demon', '#Supernatural', '#Evil'],
            'possession': ['#Possession', '#Demon', '#Supernatural'],
            'exorcism': ['#Exorcism', '#Demon', '#Supernatural'],
            
            # Strange phenomena
            'timeslip': ['#TimeSlip', '#Time', '#Strange'],
            'dimensionaljumping': ['#DimensionalJumping', '#Reality', '#Strange'],
            'mandelaeffect': ['#MandelaEffect', '#Reality', '#Memory'],
            'retconned': ['#Retconned', '#Reality', '#Change'],
            'telepathy': ['#Telepathy', '#Psychic', '#Supernatural'],
            'precognition': ['#Precognition', '#Psychic', '#Future'],
            
            # Video-focused general subs
            'publicfreakout': ['#PublicFreakout', '#Video', '#Strange'],
            'abruptchaos': ['#Chaos', '#Video', '#Unexpected'],
            'unexpected': ['#Unexpected', '#Video', '#Surprise'],
            'blackmagicfuckery': ['#BlackMagic', '#Unexplained', '#Physics'],
            'damnthatsinteresting': ['#Interesting', '#Amazing', '#Video'],
            'interestingasfuck': ['#Interesting', '#Amazing', '#Fascinating'],
            'wtf': ['#WTF', '#Strange', '#Bizarre'],
            'creepy': ['#Creepy', '#Horror', '#Disturbing'],
            'oddlyterrifying': ['#OddlyTerrifying', '#Creepy', '#Unsettling'],
            'liminalspace': ['#LiminalSpace', '#Eerie', '#Unsettling'],
            
            # International paranormal
            'paranormaluk': ['#ParanormalUK', '#UK', '#Haunted'],
            'paranormalindia': ['#ParanormalIndia', '#India', '#Supernatural'],
            'japanesehorror': ['#JapaneseHorror', '#Japan', '#Horror'],
            'mexicanfolklore': ['#MexicanFolklore', '#Mexico', '#Folklore'],
            
            # Specific creature subs
            'mothman': ['#Mothman', '#Cryptids', '#WestVirginia'],
            'chupacabra': ['#Chupacabra', '#Cryptids', '#Mexico'],
            'jersey_devil': ['#JerseyDevil', '#Cryptids', '#NewJersey'],
            'thunderbird': ['#Thunderbird', '#Cryptids', '#Giant'],
            'lakemonsters': ['#LakeMonster', '#Cryptids', '#Water'],
            'seaserpents': ['#SeaSerpent', '#Cryptids', '#Ocean'],
            
            # Investigation and evidence subs
            'paranormalinvestigators': ['#ParanormalInvestigation', '#GhostHunting', '#Evidence'],
            'ghosthunting': ['#GhostHunting', '#Investigation', '#Paranormal'],
            'evp': ['#EVP', '#GhostVoice', '#Paranormal'],
            'spiritbox': ['#SpiritBox', '#EVP', '#Communication'],
            'ouija': ['#Ouija', '#SpiritBoard', '#Communication'],
            'seances': ['#Seance', '#Spirits', '#Communication']
        }
        
        selected_hashtags = []
        
        # Add subreddit-specific hashtags
        subreddit_lower = subreddit.lower()
        if subreddit_lower in reddit_hashtags:
            selected_hashtags.extend(reddit_hashtags[subreddit_lower])
        
        # Add general Reddit hashtags (not always paranormal)
        general_reddit = ['#Reddit', '#TrueStory', '#Interesting', '#Discussion', '#Story', '#Experience', '#Share']
        selected_hashtags.extend(random.sample(general_reddit, 2))
        
        # Add hashtags based on keywords in title
        keyword_mapping = {
            'ghost': ['#Ghost', '#Haunted', '#Spirit'],
            'ufo': ['#UFO', '#Aliens', '#Sighting'],
            'alien': ['#Aliens', '#Extraterrestrial', '#UFO'],
            'bigfoot': ['#Bigfoot', '#Sasquatch', '#Cryptids'],
            'demon': ['#Demon', '#Supernatural', '#Evil'],
            'shadow': ['#ShadowPeople', '#Paranormal', '#Dark'],
            'dream': ['#Dreams', '#Supernatural', '#Psychic'],
            'time': ['#TimeSlip', '#Strange', '#Time'],
            'video': ['#Video', '#CaughtOnCamera', '#Footage'],
            'camera': ['#Camera', '#Footage', '#Evidence'],
            'caught': ['#CaughtOnCamera', '#Evidence', '#Video'],
            'sighting': ['#Sighting', '#Encounter', '#Witness'],
            'encounter': ['#Encounter', '#Experience', '#Sighting'],
            'footage': ['#Footage', '#Video', '#Evidence'],
            'security': ['#SecurityCam', '#Surveillance', '#Camera'],
            'trail': ['#TrailCam', '#Wildlife', '#Camera'],
            'dash': ['#DashCam', '#Driving', '#Video'],
            'investigation': ['#Investigation', '#Evidence', '#Research'],
            'evidence': ['#Evidence', '#Proof', '#Investigation'],
            'ritual': ['#Ritual', '#Occult', '#Supernatural'],
            'possession': ['#Possession', '#Demon', '#Exorcism'],
            'haunted': ['#Haunted', '#Ghost', '#Paranormal'],
            'cryptid': ['#Cryptids', '#Monster', '#Unknown'],
            'monster': ['#Monster', '#Cryptids', '#Beast'],
            'creature': ['#Creature', '#Cryptids', '#Unknown'],
            'supernatural': ['#Supernatural', '#Paranormal', '#Unexplained'],
            'unexplained': ['#Unexplained', '#Mystery', '#Strange'],
            'mysterious': ['#Mysterious', '#Mystery', '#Strange'],
            'strange': ['#Strange', '#Weird', '#Unusual'],
            'weird': ['#Weird', '#Strange', '#Bizarre'],
            'scary': ['#Scary', '#Horror', '#Frightening'],
            'creepy': ['#Creepy', '#Disturbing', '#Unsettling'],
            'horror': ['#Horror', '#Scary', '#Terrifying'],
            'terrifying': ['#Terrifying', '#Horror', '#Scary']
        }
        
        for keyword, tags in keyword_mapping.items():
            if keyword in title_text:
                selected_hashtags.extend(tags)
        
        # Remove duplicates and limit to 2 hashtags for professional look
        unique_hashtags = list(dict.fromkeys(selected_hashtags))[:2]
        return unique_hashtags

    def _create_reddit_fallback_content(self, reddit_post: Dict[str, Any]) -> str:
        """Create structured fallback content for Reddit posts when AI generation fails"""
        title = reddit_post.get('title', 'Interesting Reddit Story')
        subreddit = reddit_post.get('subreddit', 'reddit')
        score = reddit_post.get('score', 0)
        
        # Professional Facebook fallback templates for Reddit content
        fallback_templates = [
            f"TRENDING DISCUSSION\n\nFrom r/{subreddit} ({score} upvotes):\n\n{title}\n\nWhat are your thoughts on this story?\n\nShare your perspective in the comments below.",
            
            f"REDDIT COMMUNITY STORY\n\nA user shared this experience in r/{subreddit}:\n\n{title}\n\nWhat's your take on this situation?\n\nLet us know your thoughts.",
            
            f"POPULAR STORY\n\nr/{subreddit} discussion:\n{title}\n\nThis received {score} upvotes from the community.\n\nWhat do you think about this?",
            
            f"COMMUNITY DISCUSSION\n\nShared on r/{subreddit}:\n\n{title}\n\n{score} people found this worth discussing.\n\nWhat's your perspective on this story?"
        ]
        
        content = random.choice(fallback_templates)
        
        # Add only 2 professional hashtags
        basic_hashtags = ['#Reddit', '#Story', '#Discussion', '#Community']
        content += f"\n\n{' '.join(random.sample(basic_hashtags, 2))}"
        
        return content
