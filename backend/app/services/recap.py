import math
import tempfile
from pathlib import Path

from .. import config
from .video_common import (
    ASPECT_RESOLUTIONS,
    VideoBuildError,
    check_ffmpeg,
    concat_clips,
    get_duration_seconds,
    mux_audio_and_captions,
    pad_to_duration,
    run_ffmpeg,
)

RecapError = VideoBuildError


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
    run_ffmpeg(
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
    check_ffmpeg()

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
            concat_clips(clip_paths, assembled_path, tmp_dir)

        padded_path = tmp_dir / "padded.mp4"
        pad_to_duration(assembled_path, narration_duration, padded_path)

        mux_audio_and_captions(padded_path, narration_audio, srt_path, out_path)
