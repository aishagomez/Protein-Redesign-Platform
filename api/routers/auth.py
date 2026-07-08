from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from dependencies import get_db, get_current_user
from models import User
from schemas.user import UserCreate, UserResponse
from schemas.token import Token
from services.auth import register_user, authenticate_user, create_access_token

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario",
)
def register(data: UserCreate, db: Session = Depends(get_db)):
    """
    Crea una cuenta nueva.

    - **username**: mínimo 3 caracteres, único
    - **email**: formato válido, único
    - **password**: mínimo 8 caracteres
    """
    return register_user(db, data)


@router.post(
    "/login",
    response_model=Token,
    summary="Iniciar sesión",
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Devuelve un JWT Bearer token.

    Usa **email** en el campo `username` del formulario OAuth2.
    """
    user = authenticate_user(db, email=form_data.username, password=form_data.password)
    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    return Token(access_token=token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Perfil del usuario autenticado",
)
def me(current_user: User = Depends(get_current_user)):
    """Requiere token Bearer. Devuelve los datos del usuario en sesión."""
    return current_user
