import requests
import urllib.parse
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
        self.api_key = os.getenv("POLLINATIONS_API_KEY")
        if not self.api_key:
            logger.warning(
                "[Pollinations] POLLINATIONS_API_KEY not set. "
                "Requests may be rate-limited."
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
        Generate image via Pollinations API and save it.
        Uses API key if provided.
        """

        enhanced_prompt = f"{prompt}, {self.BASE_STYLE}"
        encoded_prompt = urllib.parse.quote(enhanced_prompt)
        seed = os.urandom(4).hex()

        url = (
            f"https://image.pollinations.ai/prompt/{encoded_prompt}"
            f"?width={width}&height={height}&nologo=true&seed={seed}"
        )

        headers = {
            "User-Agent": "Mozilla/5.0",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        logger.info(f"[Pollinations] Generating image: {prompt[:60]}")

        for attempt in range(1, retries + 1):
            try:
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=40
                )

                if response.status_code != 200:
                    raise RuntimeError(f"HTTP {response.status_code}")

                content_type = response.headers.get("Content-Type", "")
                if not content_type.startswith("image/"):
                    raise RuntimeError(f"Invalid content-type: {content_type}")

                img = Image.open(BytesIO(response.content)).convert("RGB")

                # PNG is safer for FFmpeg zoom/pan + subtitles
                img.save(output_path, format="PNG", optimize=True)

                logger.info(f"[Pollinations] Image saved → {output_path}")
                return True

            except Exception as e:
                logger.warning(
                    f"[Pollinations] Attempt {attempt}/{retries} failed: {e}"
                )
                if attempt < retries:
                    time.sleep(delay)

        logger.error("[Pollinations] Image generation failed after retries")
        return False


image_generator = ImageGenerator()
