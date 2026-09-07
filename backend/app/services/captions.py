import json
import subprocess
from pathlib import Path


class CaptionError(Exception):
    pass


def get_duration_seconds(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise CaptionError(f"Impossible de lire la durée de la vidéo : {result.stderr[-1000:]}")
    data = json.loads(result.stdout)
    try:
        return float(data["format"]["duration"])
    except (KeyError, TypeError, ValueError) as exc:
        raise CaptionError("Durée introuvable dans la sortie ffprobe.") from exc


def _format_srt_timestamp(seconds: float) -> str:
    millis = max(0, int(round(seconds * 1000)))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def build_srt(script_text: str, duration: float, srt_path: Path, words_per_chunk: int = 4) -> None:
    """Découpe le script en groupes de mots courts (style sous-titres UGC) répartis
    uniformément sur la durée de la vidéo (on ne connaît pas le timing réel de la voix)."""
    words = script_text.split()
    if not words:
        raise CaptionError("Script vide, impossible de générer les sous-titres.")

    chunks = [words[i : i + words_per_chunk] for i in range(0, len(words), words_per_chunk)]
    time_per_word = duration / len(words)

    lines = []
    cursor = 0.0
    for idx, chunk in enumerate(chunks, start=1):
        chunk_duration = time_per_word * len(chunk)
        start, end = cursor, cursor + chunk_duration
        lines.append(str(idx))
        lines.append(f"{_format_srt_timestamp(start)} --> {_format_srt_timestamp(end)}")
        lines.append(" ".join(chunk).upper())
        lines.append("")
        cursor = end

    srt_path.write_text("\n".join(lines), encoding="utf-8")


def _escape_subtitles_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def burn_captions(video_path: Path, srt_path: Path, out_path: Path) -> None:
    subtitles_filter = (
        f"subtitles={_escape_subtitles_path(srt_path)}:"
        "force_style='FontSize=20,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
        "BorderStyle=1,Outline=3,Shadow=0,Alignment=2,MarginV=90'"
    )
    result = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vf",
            subtitles_filter,
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "copy",
            "-movflags",
            "+faststart",
            str(out_path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise CaptionError(f"Échec de l'incrustation des sous-titres : {result.stderr[-2000:]}")
