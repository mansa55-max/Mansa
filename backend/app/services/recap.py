import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

from .. import config

ASPECT_RESOLUTIONS = {
    "vertical": (1080, 1920),
    "horizontal": (1920, 1080),
}


class RecapError(Exception):
    pass


def _check_ffmpeg() -> None:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RecapError("ffmpeg/ffprobe n'est pas installé sur cette machine.")


def _run(command: list[str], step: str) -> None:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RecapError(f"Échec ffmpeg ({step}) : {result.stderr[-2000:]}")


def get_duration_seconds(path: Path) -> float:
    _check_ffmpeg()
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RecapError(f"Impossible de lire la durée de la vidéo : {result.stderr[-1000:]}")
    data = json.loads(result.stdout)
    try:
        return float(data["format"]["duration"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RecapError("Durée de la vidéo introuvable dans la sortie ffprobe.") from exc


def _pick_clip_starts(source_duration: float, narration_duration: float, clip_length: float) -> tuple[list[float], float]:
    margin = min(1.0, source_duration * 0.05)
    usable_span = max(source_duration - 2 * margin, 1.0)
    clip_length = min(clip_length, usable_span)
    num_clips = max(1, math.ceil(narration_duration / clip_length))

    if num_clips == 1 or usable_span <= clip_length:
        return [margin], clip_length

    step = (usable_span - clip_length) / (num_clips - 1)
    starts = [margin + i * step for i in range(num_clips)]
    return starts, clip_length


def _extract_clip(source: Path, start: float, length: float, aspect: str, out_path: Path) -> None:
    width, height = ASPECT_RESOLUTIONS[aspect]
    video_filter = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},setsar=1,fps=30"
    )
    _run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            f"{start:.3f}",
            "-i",
            str(source),
            "-t",
            f"{length:.3f}",
            "-vf",
            video_filter,
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            str(out_path),
        ],
        "extraction d'un extrait",
    )


def _concat_clips(clip_paths: list[Path], out_path: Path, tmp_dir: Path) -> None:
    list_file = tmp_dir / "concat_list.txt"
    list_file.write_text("".join(f"file '{p.resolve()}'\n" for p in clip_paths), encoding="utf-8")
    _run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(out_path)],
        "concaténation des extraits",
    )


def _pad_to_duration(video_path: Path, duration: float, out_path: Path) -> None:
    _run(
        [
            "ffmpeg",
            "-y",
            "-stream_loop",
            "-1",
            "-i",
            str(video_path),
            "-t",
            f"{duration:.3f}",
            "-c",
            "copy",
            str(out_path),
        ],
        "ajustement de la durée",
    )


def _escape_subtitles_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def _mux_audio_and_captions(video_path: Path, audio_path: Path, srt_path: Path, out_path: Path) -> None:
    subtitles_filter = (
        f"subtitles={_escape_subtitles_path(srt_path)}:"
        "force_style='FontSize=16,PrimaryColour=&H00FFFFFF,OutlineColour=&H80000000,"
        "BorderStyle=3,Outline=2,Shadow=0,Alignment=2,MarginV=80'"
    )
    _run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-i",
            str(audio_path),
            "-vf",
            subtitles_filter,
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-shortest",
            "-movflags",
            "+faststart",
            str(out_path),
        ],
        "incrustation des sous-titres et mixage audio",
    )


def build_recap_video(
    source_video: Path,
    narration_audio: Path,
    srt_path: Path,
    narration_duration: float,
    aspect: str,
    out_path: Path,
) -> None:
    if aspect not in ASPECT_RESOLUTIONS:
        raise RecapError(f"Format inconnu : {aspect}")
    _check_ffmpeg()

    source_duration = get_duration_seconds(source_video)
    starts, clip_length = _pick_clip_starts(source_duration, narration_duration, config.RECAP_CLIP_SECONDS)

    with tempfile.TemporaryDirectory(prefix="mansa_recap_") as tmp:
        tmp_dir = Path(tmp)
        clip_paths = []
        for idx, start in enumerate(starts):
            clip_path = tmp_dir / f"clip_{idx:03d}.mp4"
            _extract_clip(source_video, start, clip_length, aspect, clip_path)
            clip_paths.append(clip_path)

        assembled_path = tmp_dir / "assembled.mp4"
        if len(clip_paths) == 1:
            assembled_path = clip_paths[0]
        else:
            _concat_clips(clip_paths, assembled_path, tmp_dir)

        padded_path = tmp_dir / "padded.mp4"
        _pad_to_duration(assembled_path, narration_duration, padded_path)

        _mux_audio_and_captions(padded_path, narration_audio, srt_path, out_path)
