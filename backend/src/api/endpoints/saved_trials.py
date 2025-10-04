"""
Saved trials API endpoints for managing user's saved clinical trials.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging

from ...models.saved_trial import SavedTrial
from ...models.base import get_db_session
from ...utils.logging import get_logger
from ...utils.auth import get_current_user, User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update

router = APIRouter()
logger = get_logger(__name__)


class SaveTrialRequest(BaseModel):
    """Request model for saving a trial."""
    trial_id: str = Field(..., description="NCT ID of the trial")
    trial_data: Dict[str, Any] = Field(..., description="Complete trial match data")
    notes: Optional[str] = Field(None, description="User notes about the trial")


class UpdateNotesRequest(BaseModel):
    """Request model for updating trial notes."""
    notes: str = Field(..., description="Updated notes")


class SavedTrialResponse(BaseModel):
    """Response model for saved trial."""
    id: str
    user_id: str
    trial_id: str
    trial_data: Dict[str, Any]
    notes: Optional[str]
    created_at: str
    updated_at: str


@router.post("/saved-trials", response_model=Dict[str, str])
async def save_trial(
    request: SaveTrialRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Save a clinical trial for later reference.
    """
    try:
        # Check if trial is already saved
        stmt = select(SavedTrial).where(
            SavedTrial.user_id == current_user.id,
            SavedTrial.trial_id == request.trial_id
        )
        result = await db.execute(stmt)
        existing_trial = result.scalar_one_or_none()
        
        if existing_trial:
            raise HTTPException(
                status_code=400,
                detail="Trial is already saved"
            )
        
        # Create new saved trial
        saved_trial = SavedTrial(
            user_id=current_user.id,
            trial_id=request.trial_id,
            trial_data=request.trial_data,
            notes=request.notes
        )
        
        db.add(saved_trial)
        await db.commit()
        await db.refresh(saved_trial)
        
        logger.info(f"Trial {request.trial_id} saved successfully")
        
        return {
            "message": "Trial saved successfully",
            "trial_id": request.trial_id,
            "saved_id": saved_trial.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving trial {request.trial_id}: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to save trial"
        )


@router.get("/saved-trials", response_model=List[SavedTrialResponse])
async def get_saved_trials(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get all saved trials for the user.
    """
    try:
        stmt = select(SavedTrial).where(
            SavedTrial.user_id == current_user.id
        ).order_by(SavedTrial.created_at.desc())
        
        result = await db.execute(stmt)
        saved_trials = result.scalars().all()
        
        return [
            SavedTrialResponse(**trial.to_dict())
            for trial in saved_trials
        ]
        
    except Exception as e:
        logger.error(f"Error fetching saved trials: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch saved trials"
        )


@router.delete("/saved-trials/{trial_id}")
async def remove_saved_trial(
    trial_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Remove a saved trial.
    """
    try:
        stmt = delete(SavedTrial).where(
            SavedTrial.user_id == current_user.id,
            SavedTrial.trial_id == trial_id
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Saved trial not found"
            )
        
        logger.info(f"Trial {trial_id} removed from saved trials")
        
        return {"message": "Trial removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing saved trial {trial_id}: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to remove saved trial"
        )


@router.put("/saved-trials/{trial_id}/notes")
async def update_trial_notes(
    trial_id: str,
    request: UpdateNotesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Update notes for a saved trial.
    """
    try:
        stmt = update(SavedTrial).where(
            SavedTrial.user_id == current_user.id,
            SavedTrial.trial_id == trial_id
        ).values(
            notes=request.notes,
            updated_at=datetime.now(timezone.utc)
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Saved trial not found"
            )
        
        logger.info(f"Notes updated for trial {trial_id}")
        
        return {"message": "Notes updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating notes for trial {trial_id}: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to update notes"
        )