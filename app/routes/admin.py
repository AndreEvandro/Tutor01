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
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    user_role = request.session.get("user_role")
    if not user_role or user_role != "admin":
        return responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    users = db.query(User).all()
    total_activities = db.query(Activity).count()
    total_interactions = db.query(Interaction).count()
    
    current_api_key = os.getenv("OPENAI_API_KEY", "")
    masked_key = f"{current_api_key[:6]}...{current_api_key[-4:]}" if len(current_api_key) > 10 else "Não configurada (Modo Simulado Ativo)"

    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "user_name": request.session.get("user_name"),
            "users": users,
            "total_activities": total_activities,
            "total_interactions": total_interactions,
            "masked_key": masked_key
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

    existing_user = db.query(User).filter(User.email == email).first()
    if not existing_user:
        new_user = User(
            name=name,
            email=email,
            password=password,
            role=role,
            is_active=True
        )
        db.add(new_user)
        db.commit()

    return responses.RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/user/toggle/{user_id}")
def toggle_user_status(user_id: int, request: Request, db: Session = Depends(get_db)):
    user_role = request.session.get("user_role")
    if not user_role or user_role != "admin":
        return responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_active = not user.is_active
        db.commit()

    return responses.RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/config/api-key")
def update_api_key(
    request: Request,
    api_key: str = Form(...)
):
    user_role = request.session.get("user_role")
    if not user_role or user_role != "admin":
        return responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    os.environ["OPENAI_API_KEY"] = api_key.strip()

    return responses.RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)