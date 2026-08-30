import shutil
import subprocess
from pathlib import Path

from .. import config


class TranscriptionError(Exception):
    pass


def check_ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def extract_audio(video_path: Path, audio_path: Path) -> None:
    if not check_ffmpeg_available():
        raise TranscriptionError(
            "ffmpeg n'est pas installé sur cette machine. Installe-le (ex: 'apt install ffmpeg' "
            "ou 'brew install ffmpeg') puis réessaie."
        )

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-f",
        "wav",
        str(audio_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise TranscriptionError(f"Échec de l'extraction audio avec ffmpeg: {result.stderr[-2000:]}")


_model = None


def _load_model():
    global _model
    if _model is None:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise TranscriptionError(
                "La bibliothèque faster-whisper n'est pas installée. Lance 'pip install -r requirements.txt'."
            ) from exc
        try:
            _model = WhisperModel(
                config.WHISPER_MODEL_SIZE,
                device=config.WHISPER_DEVICE,
                compute_type=config.WHISPER_COMPUTE_TYPE,
            )
        except Exception as exc:
            raise TranscriptionError(
                f"Impossible de charger le modèle de transcription Whisper ({config.WHISPER_MODEL_SIZE}). "
                "Vérifie ta connexion internet (le modèle est téléchargé depuis huggingface.co au premier "
                f"lancement) : {exc}"
            ) from exc
    return _model


def transcribe_audio(audio_path: Path) -> str:
    model = _load_model()
    try:
        segments, _info = model.transcribe(str(audio_path), beam_size=5)
        return " ".join(segment.text.strip() for segment in segments).strip()
    except Exception as exc:
        raise TranscriptionError(f"Échec de la transcription audio : {exc}") from exc
