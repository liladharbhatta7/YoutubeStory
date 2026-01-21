import google.generativeai as genai
import json
import typing_extensions as typing
from src.config_loader import config
from src.logger import logger
import time
from tenacity import retry, stop_after_attempt, wait_fixed

# Define strict schema for Gemini
class Scene(typing.TypedDict):
    duration_sec: float
    visual_prompt: str
    on_screen_text: str
    sfx: list[str]

class StorySchema(typing.TypedDict):
    series: str
    language: str
    story_id: str
    topic_id: str
    title: str
    mood: str
    narration_text: str
    scenes: list[Scene]
    hashtags: list[str]

class GeminiStoryGenerator:
    def __init__(self):
        genai.configure(api_key=config.gemini_api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash", 
            generation_config={"response_mime_type": "application/json", "response_schema": StorySchema}
        )
        self.system_prompt = config.get_gemini_prompt()

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(5))
    def generate_story(self, topic):
        prompt = f"""
        Topic JSON: {json.dumps(topic)}
        Generate a story regarding this topic.
        Make sure the story_id follows format YYYY-MM-DD_<topic_id>.
        Current Date: {time.strftime("%Y-%m-%d")}
        """
        
        logger.info(f"Generating story for topic: {topic.get('id')}")
        try:
            response = self.model.generate_content([self.system_prompt, prompt])
            story_json = json.loads(response.text)
            
            # Basic validation
            if "scenes" not in story_json:
                raise ValueError("Missing 'scenes' in response")
            
            logger.info("Story generated successfully.")
            return story_json
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise

gemini_generator = GeminiStoryGenerator()
