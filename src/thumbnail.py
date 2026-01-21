from PIL import Image, ImageDraw, ImageFont
import os
from src.logger import logger
from src.config_loader import config

class ThumbnailGenerator:
    def __init__(self):
        pass

    def create_thumbnail(self, image_path, title_text, output_path):
        """
        Creates a thumbnail by loading an image and adding text.
        """
        try:
            img = Image.open(image_path)
            draw = ImageDraw.Draw(img)
            
            # Simple Text Overlay
            # Try to load a font, otherwise default
            # In a production env (CI), we might need to rely on a specific font path or download one.
            # Using a basic logic here.
            font_path = config.root_dir / config.settings.get("FONT_PATH", "assets/fonts/NotoSansDevanagari-Bold.ttf")
            
            # Fallback if font doesn't exist, we skip text or use default (which won't support Nepali)
            if not os.path.exists(font_path):
                logger.warning(f"Font not found at {font_path}, attempting system fallback or skipping detailed text render.")
                # We can't really render beautiful Nepali text without a good font. 
                # Assuming the user accepts purely the visual or we ensure font provision in setup.
                # For now, we will assume the environment provided the font or we skip the text to avoid squares.
                pass
            
            if os.path.exists(font_path):
                font_size = 100
                try:
                    font = ImageFont.truetype(str(font_path), font_size)
                except:
                    font = ImageFont.load_default()

                # Text positioning (Centered, middle-bottom)
                # This is a simplification. 
                # PIL Draw Text
                # Stroke for outline
                text_color = "white"
                stroke_color = "black"
                stroke_width = 5
                
                # Approximate positioning
                # We would do text wrap logic here for long titles
                
                draw.text((100, 800), title_text, font=font, fill=text_color, stroke_width=stroke_width, stroke_fill=stroke_color)

            img.save(output_path)
            logger.info(f"Thumbnail saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Thumbnail generation failed: {e}")
            return False

thumbnail_generator = ThumbnailGenerator()
