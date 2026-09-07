from fastapi import APIRouter, HTTPException

from ..services import heygen

router = APIRouter(prefix="/api/options", tags=["options"])


@router.get("/avatars")
def get_avatars():
    try:
        return heygen.list_avatars()
    except heygen.HeyGenNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except heygen.HeyGenError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/voices")
def get_voices():
    try:
        return heygen.list_voices()
    except heygen.HeyGenNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except heygen.HeyGenError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
