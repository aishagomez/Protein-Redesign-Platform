from fastapi import APIRouter, Depends, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from dependencies import get_db, get_current_user
from models import User
from schemas.user import UserProfileUpdate
from schemas.group import ProfileResponse
from services.profile import serialize_profile, update_profile, save_avatar, avatar_file, deactivate_account

router = APIRouter(prefix="/profile", tags=["Perfil"])


@router.get("", response_model=ProfileResponse)
def get_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return serialize_profile(db, current_user)


@router.patch("", response_model=ProfileResponse)
def patch_profile(
    data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_profile(db, current_user, data)


@router.post("/avatar", response_model=ProfileResponse)
def upload_avatar(
    avatar: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return save_avatar(db, current_user, avatar)


@router.get("/avatar/{user_id}")
def get_avatar(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return FileResponse(avatar_file(user))


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    deactivate_account(db, current_user)
