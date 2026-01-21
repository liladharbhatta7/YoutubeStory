import requests
from src.config_loader import config
from src.logger import logger

class VoiceGenerator:
    def __init__(self):
        self.api_key = config.elevenlabs_api_key
        self.voice_id = config.settings.get("ELEVENLABS_VOICE_ID", "q7fnW6ILZEHm4u3pf2g0")
        self.model_id = config.settings.get("ELEVENLABS_MODEL_ID", "eleven_multilingual_v3")

    def generate_audio(self, text, output_path):
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        data = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        logger.info(f"Generating voice for text length: {len(text)}")
        try:
            response = requests.post(url, json=data, headers=headers)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                logger.info(f"Audio saved to {output_path}")
                return True
            else:
                logger.error(f"ElevenLabs Error: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Voice generation exception: {e}")
            return False

voice_generator = VoiceGenerator()
