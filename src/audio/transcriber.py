import logging
from faster_whisper import WhisperModel
from src.core.config import WHISPER_MODEL_SIZE

logger = logging.getLogger(__name__)

class AudioTranscriber:
    def __init__(self):
        logger.info(f"Loading Whisper model '{WHISPER_MODEL_SIZE}'...")
        self.model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
        logger.info("Whisper model loaded successfully.")

    def transcribe(self, audio_path: str, language: str = "it", beam_size: int = 5) -> str:
        segments, _ = self.model.transcribe(audio_path, language=language, beam_size=beam_size)
        transcript = [segment.text for segment in segments]
        return " ".join(transcript).strip()
