import json
import shutil
import subprocess
from pathlib import Path

ASPECT_RESOLUTIONS = {
    "vertical": (1080, 1920),
    "horizontal": (1920, 1080),
}


class VideoBuildError(Exception):
    pass


def check_ffmpeg() -> None:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise VideoBuildError("ffmpeg/ffprobe n'est pas installé sur cette machine.")


def run_ffmpeg(command: list[str], step: str) -> None:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise VideoBuildError(f"Échec ffmpeg ({step}) : {result.stderr[-2000:]}")


def get_duration_seconds(path: Path) -> float:
    check_ffmpeg()
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
        raise VideoBuildError(f"Impossible de lire la durée du fichier : {result.stderr[-1000:]}")
    data = json.loads(result.stdout)
    try:
        return float(data["format"]["duration"])
    except (KeyError, TypeError, ValueError) as exc:
        raise VideoBuildError("Durée introuvable dans la sortie ffprobe.") from exc


def concat_clips(clip_paths: list[Path], out_path: Path, tmp_dir: Path) -> None:
    list_file = tmp_dir / "concat_list.txt"
    list_file.write_text("".join(f"file '{p.resolve()}'\n" for p in clip_paths), encoding="utf-8")
    run_ffmpeg(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(out_path)],
        "concaténation des extraits",
    )


def pad_to_duration(video_path: Path, duration: float, out_path: Path) -> None:
    run_ffmpeg(
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


def escape_subtitles_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def mux_audio_and_captions(video_path: Path, audio_path: Path, srt_path: Path, out_path: Path) -> None:
    subtitles_filter = (
        f"subtitles={escape_subtitles_path(srt_path)}:"
        "force_style='FontSize=16,PrimaryColour=&H00FFFFFF,OutlineColour=&H80000000,"
        "BorderStyle=3,Outline=2,Shadow=0,Alignment=2,MarginV=80'"
    )
    run_ffmpeg(
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
