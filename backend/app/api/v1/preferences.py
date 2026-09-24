from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, UserPreferences
from app.db.session import get_db
from app.dependencies import get_current_user
from app.schemas.preferences import PreferencesPatch, PreferencesResponse

router = APIRouter(prefix="/preferences", tags=["preferences"])


async def _get_or_create(db: AsyncSession, user: User) -> UserPreferences:
    prefs = (
        await db.execute(select(UserPreferences).where(UserPreferences.user_id == user.id))
    ).scalar_one_or_none()
    if not prefs:
        prefs = UserPreferences(user_id=user.id)
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)
    return prefs


@router.get("", response_model=PreferencesResponse)
async def get_prefs(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> UserPreferences:
    return await _get_or_create(db, user)


@router.patch("", response_model=PreferencesResponse)
async def patch_prefs(
    payload: PreferencesPatch,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserPreferences:
    prefs = await _get_or_create(db, user)
    data = payload.model_dump(exclude_unset=True)
    if "preferred_quality" in data and data["preferred_quality"] not in ("any", "SD", "HD", "4K"):
        data.pop("preferred_quality")
    for k, v in data.items():
        setattr(prefs, k, v)
    await db.commit()
    await db.refresh(prefs)
    return prefs
