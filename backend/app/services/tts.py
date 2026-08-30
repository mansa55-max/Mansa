import asyncio
import contextlib
import re
import shutil
import subprocess
import wave
from pathlib import Path

from .. import config


class TtsError(Exception):
    pass


def _split_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _format_srt_timestamp(seconds: float) -> str:
    millis = max(0, int(round(seconds * 1000)))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _write_srt(cues: list[tuple[float, float, str]], srt_path: Path) -> None:
    lines = []
    for idx, (start, end, text) in enumerate(cues, start=1):
        lines.append(str(idx))
        lines.append(f"{_format_srt_timestamp(start)} --> {_format_srt_timestamp(max(end, start + 0.3))}")
        lines.append(text)
        lines.append("")
    srt_path.write_text("\n".join(lines), encoding="utf-8")


async def _edge_tts_generate(text: str, audio_path: Path) -> list[dict]:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice=config.TTS_VOICE)
    word_boundaries: list[dict] = []
    with open(audio_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                word_boundaries.append(chunk)
    return word_boundaries


def _boundaries_to_cues(word_boundaries: list[dict]) -> list[tuple[float, float, str]]:
    cues: list[tuple[float, float, str]] = []
    current_words: list[str] = []
    current_start: float | None = None
    last_end = 0.0

    for boundary in word_boundaries:
        start = boundary["offset"] / 10_000_000
        end = (boundary["offset"] + boundary["duration"]) / 10_000_000
        word = boundary["text"]
        if current_start is None:
            current_start = start
        current_words.append(word)
        last_end = end
        joined = " ".join(current_words)
        ends_sentence = word.strip().endswith((".", "!", "?", "…"))
        if ends_sentence or len(current_words) >= 7 or len(joined) >= 42:
            cues.append((current_start, end, joined))
            current_words = []
            current_start = None

    if current_words and current_start is not None:
        cues.append((current_start, last_end, " ".join(current_words)))
    return cues


def _wav_duration_seconds(path: Path) -> float:
    with contextlib.closing(wave.open(str(path), "rb")) as wav_file:
        return wav_file.getnframes() / float(wav_file.getframerate())


def _espeak_generate(text: str, audio_path: Path) -> float:
    if not shutil.which("espeak-ng"):
        raise TtsError(
            "Aucun moteur de synthèse vocale disponible : edge-tts a échoué (pas de connexion internet ?) "
            "et espeak-ng n'est pas installé en secours (ex: 'apt install espeak-ng')."
        )
    result = subprocess.run(
        ["espeak-ng", "-v", "fr", "-s", "165", "-w", str(audio_path), text],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise TtsError(f"Échec de la synthèse vocale espeak-ng : {result.stderr[-1000:]}")
    return _wav_duration_seconds(audio_path)


def _espeak_cues(text: str, total_duration: float) -> list[tuple[float, float, str]]:
    sentences = _split_sentences(text)
    if not sentences:
        return []
    total_chars = sum(len(s) for s in sentences) or 1
    cues = []
    t = 0.0
    for sentence in sentences:
        duration = total_duration * (len(sentence) / total_chars)
        cues.append((t, t + duration, sentence))
        t += duration
    return cues


def generate_narration(text: str, audio_path: Path, srt_path: Path) -> float:
    """Génère l'audio de narration + un fichier .srt de sous-titres synchronisés.

    Essaie edge-tts (gratuit, sans clé, bonne qualité, nécessite internet) puis
    se replie sur espeak-ng (100% local, qualité robotique) si indisponible.
    Retourne la durée de l'audio en secondes.
    """
    text = text.strip()
    if not text:
        raise TtsError("Résumé vide, impossible de générer une narration.")

    try:
        word_boundaries = asyncio.run(_edge_tts_generate(text, audio_path))
        if not word_boundaries or not audio_path.exists() or audio_path.stat().st_size == 0:
            raise TtsError("edge-tts n'a renvoyé aucun audio exploitable.")
        cues = _boundaries_to_cues(word_boundaries)
        _write_srt(cues, srt_path)
        return cues[-1][1] if cues else 0.0
    except Exception as edge_exc:
        try:
            duration = _espeak_generate(text, audio_path)
        except TtsError:
            raise
        except Exception as espeak_exc:
            raise TtsError(
                f"Échec de la synthèse vocale (edge-tts indisponible : {edge_exc} ; "
                f"repli espeak-ng également en échec : {espeak_exc})"
            ) from espeak_exc
        cues = _espeak_cues(text, duration)
        _write_srt(cues, srt_path)
        return duration
