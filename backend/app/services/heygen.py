from pathlib import Path

import httpx

from .. import config

ASPECT_DIMENSIONS = {
    "vertical": {"width": 1080, "height": 1920},
    "horizontal": {"width": 1920, "height": 1080},
}


class HeyGenError(Exception):
    pass


class HeyGenNotConfiguredError(HeyGenError):
    pass


def _client() -> httpx.Client:
    if not config.HEYGEN_API_KEY:
        raise HeyGenNotConfiguredError(
            "HEYGEN_API_KEY manquant. Ajoute-le dans le fichier .env pour activer la génération de pubs."
        )
    return httpx.Client(
        base_url=config.HEYGEN_BASE_URL,
        headers={"X-Api-Key": config.HEYGEN_API_KEY, "Accept": "application/json"},
        timeout=30.0,
    )


def list_avatars() -> list[dict]:
    with _client() as client:
        response = client.get("/v2/avatars")
        response.raise_for_status()
        data = response.json()

    avatars = data.get("data", {}).get("avatars", []) or data.get("avatars", [])
    results = []
    for item in avatars:
        results.append(
            {
                "avatar_id": item.get("avatar_id"),
                "name": item.get("avatar_name") or item.get("avatar_id"),
                "preview_image_url": item.get("preview_image_url"),
                "default_voice_id": item.get("default_voice_id"),
            }
        )
    return [a for a in results if a["avatar_id"]]


def list_voices() -> list[dict]:
    with _client() as client:
        response = client.get("/v2/voices")
        response.raise_for_status()
        data = response.json()

    voices = data.get("data", {}).get("voices", []) or data.get("voices", [])
    results = []
    for item in voices:
        results.append(
            {
                "voice_id": item.get("voice_id"),
                "name": item.get("name"),
                "language": item.get("language"),
                "gender": item.get("gender"),
                "preview_audio_url": item.get("preview_audio"),
            }
        )
    return [v for v in results if v["voice_id"]]


def generate_video(script_text: str, avatar_id: str, voice_id: str, aspect: str) -> str:
    if aspect not in ASPECT_DIMENSIONS:
        raise HeyGenError(f"Format inconnu : {aspect}")

    payload = {
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": avatar_id,
                    "avatar_style": "normal",
                },
                "voice": {
                    "type": "text",
                    "input_text": script_text,
                    "voice_id": voice_id,
                },
                "background": {"type": "color", "value": "#F1F1F1"},
            }
        ],
        "dimension": ASPECT_DIMENSIONS[aspect],
    }

    with _client() as client:
        response = client.post("/v2/video/generate", json=payload)
        if response.status_code >= 400:
            raise HeyGenError(f"Échec de la génération HeyGen ({response.status_code}) : {response.text[:500]}")
        data = response.json()

    video_id = data.get("data", {}).get("video_id")
    if not video_id:
        raise HeyGenError(f"Réponse HeyGen inattendue (pas de video_id) : {data}")
    return video_id


def get_video_status(video_id: str) -> dict:
    with _client() as client:
        response = client.get("/v1/video_status.get", params={"video_id": video_id})
        if response.status_code >= 400:
            raise HeyGenError(f"Échec de la lecture du statut HeyGen ({response.status_code}) : {response.text[:500]}")
        data = response.json()

    payload = data.get("data") or {}
    return {
        "status": payload.get("status"),
        "video_url": payload.get("video_url"),
        "error": payload.get("error"),
    }


def download_video(video_url: str, out_path: Path) -> None:
    with httpx.stream("GET", video_url, timeout=120.0, follow_redirects=True) as response:
        if response.status_code >= 400:
            raise HeyGenError(f"Échec du téléchargement de la vidéo HeyGen ({response.status_code})")
        with open(out_path, "wb") as f:
            for chunk in response.iter_bytes(1024 * 1024):
                f.write(chunk)
