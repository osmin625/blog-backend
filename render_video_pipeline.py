import os
import argparse
import logging
from pathlib import Path
import tempfile
import textwrap

# Requires: pip install gTTS moviepy
from gtts import gTTS
from moviepy.editor import TextClip, AudioFileClip, ColorClip, CompositeVideoClip

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def create_tts_audio(text: str, output_path: str, lang='ko'):
    """Generates a TTS audio file from the provided text using gTTS."""
    logging.info("Generating TTS audio...")
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(output_path)
    logging.info(f"TTS audio saved to {output_path}")

def render_video(markdown_filepath: Path, output_video_path: Path):
    """
    Reads a markdown file, parses the text, generates TTS, 
    and renders a simple video with the text overlaid.
    """
    if not markdown_filepath.exists():
        logging.error(f"Markdown file {markdown_filepath} does not exist.")
        return

    # 1. Parse text (simplistic approach: read all text, strip markdown formatting if needed)
    with open(markdown_filepath, 'r', encoding='utf-8') as f:
        # In a real scenario, you'd want to strip markdown formatting (e.g., #, *, [[ ]]) 
        # using a library like markdown or regex before sending to TTS.
        # For this template, we read as raw text.
        text = f.read()
        clean_text = text.replace('#', '').replace('*', '')

    if not clean_text.strip():
        logging.warning("No text found to process.")
        return

    with tempfile.TemporaryDirectory() as temp_dir:
        audio_path = os.path.join(temp_dir, "tts_audio.mp3")
        
        # 2. Generate Audio
        create_tts_audio(clean_text, audio_path)
        
        # 3. Assemble Video
        logging.info("Assembling video with MoviePy...")
        try:
            # Load the generated audio
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration

            # Create a background color clip (e.g., dark gray)
            bg_clip = ColorClip(size=(1920, 1080), color=(30, 30, 30)).set_duration(duration)

            # Create a text clip (Subtitles/Overlay)
            # Text formatting requires ImageMagick to be installed and configured for moviepy
            # Warning: MoviePy TextClip requires ImageMagick!
            # We'll wrap the text so it fits the screen
            wrapped_text = "\n".join(textwrap.wrap(clean_text[:500] + "..." if len(clean_text) > 500 else clean_text, width=60))
            
            try:
                txt_clip = TextClip(wrapped_text, fontsize=70, color='white', font='Arial', align='center')
                txt_clip = txt_clip.set_position('center').set_duration(duration)
                video_clip = CompositeVideoClip([bg_clip, txt_clip])
            except BaseException as e:
                logging.warning(f"Failed to create TextClip (ImageMagick missing?): {e}. Proceeding with blank background.")
                video_clip = CompositeVideoClip([bg_clip])

            # Set the audio of the composite video
            video_clip.audio = audio_clip

            # Render
            logging.info(f"Writing video to {output_video_path}...")
            video_clip.write_videofile(str(output_video_path), fps=24, logger=None)
            
            # Clean up moviepy open handles
            video_clip.close()
            audio_clip.close()
            logging.info("Video rendering complete!")

        except Exception as e:
            logging.error(f"Error during video assembly: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render a video natively from a Markdown file.")
    parser.add_argument("--input-md", required=True, help="Path to input markdown file")
    parser.add_argument("--output-mp4", default="output_video.mp4", help="Path to output mp4 video file")
    
    args = parser.parse_args()
    render_video(Path(args.input_md), Path(args.output_mp4))
