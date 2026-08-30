import tempfile
from pathlib import Path

from .video_common import (
    ASPECT_RESOLUTIONS,
    VideoBuildError,
    check_ffmpeg,
    concat_clips,
    mux_audio_and_captions,
    pad_to_duration,
    run_ffmpeg,
)

StoryVideoError = VideoBuildError

FPS = 30
MAX_ZOOM = 1.15
MIN_IMAGE_SECONDS = 1.0


def _build_image_clip(image_path: Path, duration: float, aspect: str, out_path: Path) -> None:
    width, height = ASPECT_RESOLUTIONS[aspect]
    total_frames = max(1, round(duration * FPS))
    zoom_increment = (MAX_ZOOM - 1) / total_frames

    video_filter = (
        f"scale={width * 2}:{height * 2}:force_original_aspect_ratio=increase,"
        f"crop={width * 2}:{height * 2},"
        f"zoompan=z='min(zoom+{zoom_increment:.8f},{MAX_ZOOM})':"
        f"d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"s={width}x{height}:fps={FPS},format=yuv420p"
    )
    run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(image_path),
            "-t",
            f"{duration:.3f}",
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
        f"animation de l'image {image_path.name}",
    )


def build_story_video(
    image_paths: list[Path],
    narration_audio: Path,
    srt_path: Path,
    narration_duration: float,
    aspect: str,
    out_path: Path,
) -> None:
    if aspect not in ASPECT_RESOLUTIONS:
        raise StoryVideoError(f"Format inconnu : {aspect}")
    if not image_paths:
        raise StoryVideoError("Aucune image fournie pour générer la vidéo.")
    check_ffmpeg()

    per_image_duration = max(MIN_IMAGE_SECONDS, narration_duration / len(image_paths))

    with tempfile.TemporaryDirectory(prefix="mansa_story_") as tmp:
        tmp_dir = Path(tmp)
        clip_paths = []
        for idx, image_path in enumerate(image_paths):
            clip_path = tmp_dir / f"clip_{idx:03d}.mp4"
            _build_image_clip(image_path, per_image_duration, aspect, clip_path)
            clip_paths.append(clip_path)

        assembled_path = tmp_dir / "assembled.mp4"
        if len(clip_paths) == 1:
            assembled_path = clip_paths[0]
        else:
            concat_clips(clip_paths, assembled_path, tmp_dir)

        padded_path = tmp_dir / "padded.mp4"
        pad_to_duration(assembled_path, narration_duration, padded_path)

        mux_audio_and_captions(padded_path, narration_audio, srt_path, out_path)
