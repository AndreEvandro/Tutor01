import os
from fastapi import APIRouter, Request, Depends, Form, responses, status
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

from app.database import get_db
from app.models.user import User
from app.models.activity import Activity
from app.models.interaction import Interaction

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard")
def admin_dashboard(
    request: Request,
    error: str = None,
    success: str = None,
    db: Session = Depends(get_db)
):
    user_role = request.session.get("user_role")
    if not user_role or user_role != "admin":
        return responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    users = db.query(User).all()
    total_activities = db.query(Activity).count()
    total_interactions = db.query(Interaction).count()
    
    current_api_key = os.getenv("OPENAI_API_KEY", "")
    masked_key = f"{current_api_key[:6]}...{current_api_key[-4:]}" if len(current_api_key) > 10 else "Não configurada (Modo Simulado Ativo)"

    error_msg = None
    if error == "email_exists":
        error_msg = "O e-mail informado já está em uso por outro usuário."
    elif error == "not_found":
        error_msg = "Usuário não encontrado."

    success_msg = None
    if success == "created":
        success_msg = "Novo usuário cadastrado com sucesso!"
    elif success == "updated":
        success_msg = "Dados do usuário atualizados com sucesso!"
    elif success == "status":
        success_msg = "Status do usuário alterado com sucesso!"
    elif success == "api_key":
        success_msg = "Chave da API OpenAI atualizada com sucesso!"

    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "user_name": request.session.get("user_name"),
            "users": users,
            "total_activities": total_activities,
            "total_interactions": total_interactions,
            "masked_key": masked_key,
            "error_msg": error_msg,
            "success_msg": success_msg
        }
    )

@router.post("/user/create")
def create_user(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db)
):
    user_role = request.session.get("user_role")
    if not user_role or user_role != "admin":
        return responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    existing_user = db.query(User).filter(User.email == email.strip()).first()
    if existing_user:
        return responses.RedirectResponse(url="/admin/dashboard?error=email_exists", status_code=status.HTTP_303_SEE_OTHER)

    new_user = User(
        name=name.strip(),
        email=email.strip(),
        password=password.strip(),
        role=role,
        is_active=True
    )
    db.add(new_user)
    db.commit()

    return responses.RedirectResponse(url="/admin/dashboard?success=created", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/user/update/{user_id}")
def update_user(
    user_id: int,
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
    is_active: bool = Form(True),
    password: str = Form(None),
    db: Session = Depends(get_db)
):
    user_role = request.session.get("user_role")
    if not user_role or user_role != "admin":
        return responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return responses.RedirectResponse(url="/admin/dashboard?error=not_found", status_code=status.HTTP_303_SEE_OTHER)

    existing_email = db.query(User).filter(User.email == email.strip(), User.id != user_id).first()
    if existing_email:
        return responses.RedirectResponse(url="/admin/dashboard?error=email_exists", status_code=status.HTTP_303_SEE_OTHER)

    user.name = name.strip()
    user.email = email.strip()
    user.role = role
    user.is_active = is_active
    if password and password.strip():
        user.password = password.strip()

    db.commit()
    return responses.RedirectResponse(url="/admin/dashboard?success=updated", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/user/toggle/{user_id}")
def toggle_user_status(user_id: int, request: Request, db: Session = Depends(get_db)):
    user_role = request.session.get("user_role")
    if not user_role or user_role != "admin":
        return responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_active = not user.is_active
        db.commit()

    return responses.RedirectResponse(url="/admin/dashboard?success=status", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/config/api-key")
def update_api_key(
    request: Request,
    api_key: str = Form(...)
):
    user_role = request.session.get("user_role")
    if not user_role or user_role != "admin":
        return responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    os.environ["OPENAI_API_KEY"] = api_key.strip()
    return responses.RedirectResponse(url="/admin/dashboard?success=api_key", status_code=status.HTTP_303_SEE_OTHER)