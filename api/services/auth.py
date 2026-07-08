from datetime import datetime, timedelta, timezone
from typing import Optional

# Workaround para incompatibilidad passlib + bcrypt>=4.x
import bcrypt
if not hasattr(bcrypt, '__about__'):
    bcrypt.__about__ = type('about', (), {'__version__': bcrypt.__version__})()

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models import User
from schemas.user import UserCreate
from schemas.token import TokenData

# ── Configuración ──────────────────────────────────────────────────────────────
SECRET_KEY = "CHANGE_ME_IN_PRODUCTION"   # ← mover a variable de entorno
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24    # 24 horas
ADMIN_EMAIL = "aishaggch13@gmail.com"
ADMIN_PASSWORD = "12345678"
ADMIN_USERNAME = "admin"
ADMIN_ROLE = "admin"
USER_ROLE = "user"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Hashing ────────────────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT ────────────────────────────────────────────────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role")
        if user_id is None:
            raise credentials_exception
        return TokenData(user_id=int(user_id), email=email, role=role)
    except JWTError:
        raise credentials_exception


# ── Operaciones de BD ──────────────────────────────────────────────────────────
def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def register_user(db: Session, data: UserCreate) -> User:
    if get_user_by_email(db, data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado",
        )
    if get_user_by_username(db, data.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El nombre de usuario ya está en uso",
        )
    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        role=USER_ROLE,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no registrado",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta desactivada",
        )
    if not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def is_admin_user(user: User | None) -> bool:
    return bool(user and getattr(user, "role", USER_ROLE) == ADMIN_ROLE)


def is_admin_user_id(db: Session, user_id: int) -> bool:
    user = db.query(User).filter(User.id == user_id).first()
    return is_admin_user(user)


def ensure_bootstrap_admin(db: Session) -> User:
    admin = get_user_by_email(db, ADMIN_EMAIL)
    if admin:
        updated = False
        if not admin.is_active:
            admin.is_active = True
            updated = True
        if admin.role != ADMIN_ROLE:
            admin.role = ADMIN_ROLE
            updated = True
        if admin.username != ADMIN_USERNAME:
            admin.username = ADMIN_USERNAME
            updated = True
        if updated:
            db.commit()
            db.refresh(admin)
        return admin

    admin = User(
        username=ADMIN_USERNAME,
        email=ADMIN_EMAIL,
        password_hash=hash_password(ADMIN_PASSWORD),
        role=ADMIN_ROLE,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin
