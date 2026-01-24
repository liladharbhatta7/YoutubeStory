import json
import time
from pydantic import BaseModel
from google import genai
from src.config_loader import config
from src.logger import logger
from tenacity import retry, stop_after_attempt, wait_fixed

# 1. Define Pydantic Models (Better for JSON enforcement)
class Scene(BaseModel):
    duration_sec: float
    visual_prompt: str
    on_screen_text: str
    sfx: list[str]

class StorySchema(BaseModel):
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
        # Use the modern Client
        self.client = genai.Client(api_key=config.gemini_api_key)
        # Corrected Model: gemini-2.0-flash or gemini-1.5-flash
        self.model_id = "gemini-2.0-flash" 
        self.system_prompt = config.get_gemini_prompt()

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(5))
    def generate_story(self, topic):
        topic_id = topic.get('id', 'unknown')
        current_date = time.strftime("%Y-%m-%d")
        
        user_prompt = f"""
        Topic JSON: {json.dumps(topic, ensure_ascii=False)}
        Generate a story regarding this topic.
        Make sure the story_id follows format: {current_date}_{topic_id}.
        Current Date: {current_date}
        """

        logger.info(f"Generating story for topic: {topic_id}")
        
        try:
            # The new SDK passes system_instruction inside the config
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=user_prompt,
                config={
                    'system_instruction': self.system_prompt,
                    'response_mime_type': 'application/json',
                    'response_schema': StorySchema, 
                }
            )

            # response.parsed is already a Pydantic object
            if not response.parsed:
                raise ValueError("Empty response from Gemini")

            # Convert to dict for your existing pipeline
            story_json = response.parsed.model_dump()

            logger.info("Story generated successfully.")
            return story_json

        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise

gemini_generator = GeminiStoryGenerator()
