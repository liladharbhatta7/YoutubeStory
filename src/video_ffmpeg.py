import subprocess
import os
from PIL import Image, ImageDraw, ImageFont
import textwrap
from src.logger import logger
from src.config_loader import config

class VideoEditor:
    def __init__(self):
        self.width = 1080
        self.height = 1920
        # Font for text overlays
        self.font_path = str(
            config.root_dir / config.settings.get("FONT_PATH", "assets/fonts/NotoSansDevanagari-Bold.ttf")
        )

        # ✅ Background music directory (your new location)
        # Stored inside src/background_music/
        self.bgm_dir = config.root_dir / "src" / "background_music"

    def create_text_overlay(self, text, output_path, duration):
        """
        Creates a transparent PNG with the text to overlay.
        Better than FFmpeg drawtext for handling complex scripts like Nepali.
        """
        img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        if os.path.exists(self.font_path):
            font_size = 60
            font = ImageFont.truetype(self.font_path, font_size)
        else:
            # Fallback (will likely fail to render Nepali correctly, using standard)
            font = ImageFont.load_default()

        # Text wrapping
        lines = textwrap.wrap(text, width=30)  # Adjust width based on needs

        # Draw text at bottom center
        y_text = self.height - 400 - (len(lines) * 70)

        for line in lines:
            # Calculate text width (getbbox)
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x_text = (self.width - text_width) / 2

            # Simple shadow/stroke
            stroke_width = 3
            draw.text(
                (x_text, y_text),
                line,
                font=font,
                fill="black",
                stroke_width=stroke_width + 4,
                stroke_fill="black",
            )  # Thick outline
            draw.text((x_text, y_text), line, font=font, fill="yellow", stroke_width=0)  # Main text

            y_text += 70  # line height

        img.save(output_path)

    def assemble_video(self, scenes, audio_path, output_path, temp_dir, category=None):
        """
        Assembles video from scenes (images) and audio.
        scenes: list of dicts with 'image_path', 'text', 'duration'

        ✅ Change: background music is chosen by category from src/background_music/<category>.mp3
        """
        # 1. Generate text overlay images for each scene
        inputs = []
        filter_complex = []

        # Input 0: Narration Audio
        inputs.append("-i")
        inputs.append(audio_path)

        # ✅ Add background music by category (Input 1)
        bgm_path = self._get_bgm_for_category(category)
        has_bgm = False
        if bgm_path:
            inputs.append("-i")
            inputs.append(bgm_path)
            has_bgm = True
            logger.info(f"Selected BGM for category='{category}': {bgm_path}")
        else:
            logger.warning(f"No BGM found for category='{category}'. Proceeding without BGM.")

        video_streams = []
        current_input_idx = 2 if has_bgm else 1

        total_duration = 0

        for idx, scene in enumerate(scenes):
            image_path = scene['image_path']
            text = scene['text']
            duration = scene['duration']
            total_duration += duration

            # Create text overlay image
            text_overlay_path = os.path.join(temp_dir, f"text_{idx}.png")
            self.create_text_overlay(text, text_overlay_path, duration)

            # Add inputs
            inputs.extend(["-loop", "1", "-t", str(duration), "-i", image_path])
            inputs.extend(["-loop", "1", "-t", str(duration), "-i", text_overlay_path])

            img_idx = current_input_idx
            text_idx = current_input_idx + 1
            current_input_idx += 2

            frames = int(duration * 30)

            # Apply zoompan to image
            filter_complex.append(
                f"[{img_idx}:v]scale=1080*2:-1,"
                f"zoompan=z='min(zoom+0.0015,1.5)':d={frames}:"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920,"
                f"setsar=1[v{idx}_zoom]"
            )

            # Overlay text on top of zoomed image
            filter_complex.append(f"[{text_idx}:v]scale=1080:1920[v{idx}_text]")
            filter_complex.append(f"[v{idx}_zoom][v{idx}_text]overlay=0:0:shortest=1[v{idx}_out]")

            video_streams.append(f"[v{idx}_out]")

        # Concatenate all video segments
        filter_complex.append(f"{''.join(video_streams)}concat=n={len(scenes)}:v=1:a=0[v_final]")

        # Audio Mixing
        # Ensure narration is louder than BGM
        if has_bgm:
            # BGM is input 1, narration is input 0
            # Loop bgm indefinitely; final output uses -shortest to end when narration ends.
            filter_complex.append(f"[1:a]volume=0.1,aloop=loop=-1:size=2e+09[bgm_loop]")
            filter_complex.append(f"[0:a][bgm_loop]amix=inputs=2:duration=first:dropout_transition=2[a_final]")
            map_audio = "[a_final]"
        else:
            map_audio = "0:a"

        cmd = (
            ["ffmpeg", "-y"]
            + inputs
            + [
                "-filter_complex",
                ";".join(filter_complex),
                "-map",
                "[v_final]",
                "-map",
                map_audio,
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
                output_path,
            ]
        )

        logger.info("Running FFmpeg...")

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info(f"Video assembled at {output_path}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg failed: {e.stderr.decode()}")
            return False

    # ✅ New: Pick BGM by category from src/background_music/
    def _get_bgm_for_category(self, category):
        """
        Expected filenames:
          src/background_music/<Category>.mp3
        Example:
          src/background_music/Missed_Moment.mp3

        If exact match not found, tries case-insensitive stem match.
        """
        if not category:
            return None

        if not self.bgm_dir.exists():
            logger.warning(f"BGM directory not found: {self.bgm_dir}")
            return None

        # 1) Exact match
        exact = self.bgm_dir / f"{category}.mp3"
        if exact.exists():
            return str(exact)

        # 2) Case-insensitive match
        cat_lower = str(category).strip().lower()
        for f in self.bgm_dir.glob("*.mp3"):
            if f.stem.strip().lower() == cat_lower:
                return str(f)

        return None

video_editor = VideoEditor()
