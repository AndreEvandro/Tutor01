from fastapi import APIRouter, Request, Depends, Form, responses, status
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

from app.database import get_db
from app.models.user import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
def root():
    return responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email, User.password == password).first()
    
    if not user or not user.is_active:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "Credenciais inválidas ou conta inativa."}
        )

    request.session["user_id"] = user.id
    request.session["user_name"] = user.name
    request.session["user_role"] = user.role

    if user.role == "admin":
        return responses.RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    elif user.role == "docente":
        return responses.RedirectResponse(url="/teacher/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    else:
        return responses.RedirectResponse(url="/student/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)