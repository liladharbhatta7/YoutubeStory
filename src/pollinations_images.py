import requests
from PIL import Image
from io import BytesIO
import os
import time
from src.logger import logger


class ImageGenerator:
    BASE_STYLE = (
        "cinematic lighting, photorealistic, ultra detailed, "
        "natural skin texture, realistic faces, Nepal middle class context"
    )

    def __init__(self):
        # Cloudflare Worker API URL
        self.worker_url = os.getenv("WORKER_API_URL", "https://techkoseli.liladharbhatta9.workers.dev")
        self.api_key = os.getenv("WORKER_API_KEY")
        if not self.api_key:
            logger.warning(
                "[WorkerAI] WORKER_API_KEY not set. Requests will fail."
            )

    def generate_image(
        self,
        prompt: str,
        output_path: str,
        width: int = 1080,
        height: int = 1920,
        retries: int = 3,
        delay: float = 2.0
    ) -> bool:
        """
        Generate image via Cloudflare Worker API and save it.
        """

        enhanced_prompt = f"{prompt}, {self.BASE_STYLE}, vertical {width}x{height}"

        payload = {"prompt": enhanced_prompt}
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "Mozilla/5.0"
        }

        logger.info(f"[WorkerAI] Generating image: {prompt[:60]}")

        for attempt in range(1, retries + 1):
            try:
                response = requests.post(
                    self.worker_url,
                    json=payload,
                    headers=headers,
                    timeout=60
                )

                if response.status_code != 200:
                    raise RuntimeError(f"HTTP {response.status_code}: {response.text}")

                # Open image from bytes
                img = Image.open(BytesIO(response.content)).convert("RGB")
                img.save(output_path, format="PNG", optimize=True)

                logger.info(f"[WorkerAI] Image saved → {output_path}")
                return True

            except Exception as e:
                logger.warning(
                    f"[WorkerAI] Attempt {attempt}/{retries} failed: {e}"
                )
                if attempt < retries:
                    time.sleep(delay)

        logger.error("[WorkerAI] Image generation failed after retries")
        return False


# Example usage
if __name__ == "__main__":
    image_generator = ImageGenerator()
    image_generator.generate_image(
        prompt="Beautiful Himalaya mountains at sunrise",
        output_path="himalaya.png"
    )
