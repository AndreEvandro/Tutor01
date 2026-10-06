from fastapi import APIRouter, Request, Depends, Form, responses, status
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

from app.database import get_db
from app.models.user import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@router.post("/login")
def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email, User.password == password).first()
    if not user:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "E-mail ou senha incorretos."}
        )
    
    # Salva o usuário na sessão do navegador
    request.session["user_id"] = user.id
    request.session["user_name"] = user.name
    request.session["user_role"] = user.role

    return responses.RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/dashboard")
def dashboard(request: Request):
    user_role = request.session.get("user_role")
    user_name = request.session.get("user_name")

    if not user_role:
        return responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    template_map = {
        "admin": "admin.html",
        "docente": "docente.html",
        "estudante": "estudante.html"
    }

    template_name = template_map.get(user_role, "login.html")
    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context={"user_name": user_name, "user_role": user_role}
    )