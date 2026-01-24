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

def _extract_json_object(text: str) -> dict:
    """
    Extract the first top-level JSON object from a text response.
    This protects against occasional extra text or formatting.
    """
    if not text:
        raise ValueError("Empty response text from Gemini")

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in Gemini response text")

    candidate = text[start:end + 1]
    return json.loads(candidate)

class GeminiStoryGenerator:
    def __init__(self):
        genai.configure(api_key=config.gemini_api_key)
        self.model = genai.GenerativeModel(
            "gemini-2.5-flash",
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": StorySchema
            }
        )
        self.system_prompt = config.get_gemini_prompt()

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(5))
    def generate_story(self, topic):
        prompt = f"""
        Topic JSON: {json.dumps(topic, ensure_ascii=False)}
        Generate a story regarding this topic.
        Make sure the story_id follows format YYYY-MM-DD_<topic_id>.
        Current Date: {time.strftime("%Y-%m-%d")}
        """

        logger.info(f"Generating story for topic: {topic.get('id')}")
        try:
            response = self.model.generate_content([self.system_prompt, prompt])

            # Parse robustly (handles minor non-JSON wrappers)
            story_json = _extract_json_object(getattr(response, "text", ""))

            # Basic validation (no scene count enforcement)
            scenes = story_json.get("scenes", None)
            if not isinstance(scenes, list) or len(scenes) == 0:
                raise ValueError("Missing 'scenes' in response")

            logger.info("Story generated successfully.")
            return story_json

        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise

gemini_generator = GeminiStoryGenerator()
