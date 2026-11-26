from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import select
from database.connection import get_session
from models.users import User, UserSignIn

user_router = APIRouter(tags=["User"])

@user_router.post("/signup")
async def sign_user_up(user: User, session=Depends(get_session)) -> dict:
    statement = select(User).where(User.email == user.email)
    existing_user = session.exec(statement).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже существует"
        )
    session.add(user)
    session.commit()
    return {"message": "Пользователь успешно зарегистрирован (Руслан Киков)"}

@user_router.post("/signin")
async def sign_user_in(user: UserSignIn, session=Depends(get_session)) -> dict:
    statement = select(User).where(User.email == user.email)
    db_user = session.exec(statement).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    if db_user.password != user.password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Неверный пароль"
        )
    return {"message": "Пользователь успешно вошёл (Руслан Киков)"}
