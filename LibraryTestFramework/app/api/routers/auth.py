from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.auth import UserRegister, UserOut, Token
from app.services.auth_service import AuthService
from app.api.deps import get_auth_service, get_current_user
from app.models import User

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: UserRegister, service: AuthService = Depends(get_auth_service)):
    return service.register(data)


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), service: AuthService = Depends(get_auth_service)):
    token = service.login(form.username, form.password)
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
