import os
import logging
from openai import OpenAI

# Initialize Logger
logger = logging.getLogger("SalesBot")

# Initialize OpenAI Client
client = OpenAI()

def transcribe_audio(file_path: str) -> str:
    """
    Transcribes audio file using OpenAI Whisper.
    """
    if not os.path.exists(file_path):
        logger.error(f"Audio file not found: {file_path}")
        return ""

    try:
        logger.info(f"🎙️ Transcribing audio: {file_path}")
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                response_format="text"
            )
        logger.info(f"📝 Transcription result: {transcript[:50]}...")
        return transcript
    except Exception as e:
        logger.error(f"❌ Whisper Transcription Failed: {e}")
        return "[Audio ininteligible]"

def cleanup_file(file_path: str):
    """
    Deletes the file from disk to save space (TTL).
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"🗑️ Deleted temp media: {file_path}")
    except Exception as e:
        logger.error(f"⚠️ Failed to cleanup file {file_path}: {e}")

def cleanup_old_files(directory: str, max_age_hours: int = 24):
    """
    Deletes files in the specified directory that are older than max_age_hours.
    """
    import time
    
    if not os.path.exists(directory):
        return

    logger.info(f"🧹 Running cleanup for {directory} (Max Age: {max_age_hours}h)...")
    
    now = time.time()
    cutoff = now - (max_age_hours * 3600)
    count = 0
    
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            try:
                # Check creation/mod time
                file_time = os.path.getmtime(file_path)
                if file_time < cutoff:
                    os.remove(file_path)
                    count += 1
            except Exception as e:
                logger.error(f"⚠️ Error deleting {filename}: {e}")
                
    if count > 0:
        logger.info(f"✨ Deleted {count} old media files.")
    else:
        logger.info("✅ No old media files found.")

def encode_image_to_base64(file_path: str) -> str:
    """
    Encodes an image to Base64 string for GPT-4o input.
    """
    import base64
    
    if not os.path.exists(file_path):
        logger.error(f"Image file not found: {file_path}")
        return None

    try:
        with open(file_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        logger.info(f"🖼️ Encoded image {file_path} to Base64.")
        return encoded_string
    except Exception as e:
        logger.error(f"❌ Failed to encode image: {e}")
        return None
