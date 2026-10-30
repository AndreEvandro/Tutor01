import csv
import io
from fastapi import APIRouter, Request, Depends, Form, responses, status
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

from app.database import get_db
from app.models.activity import Activity
from app.models.interaction import Interaction
from app.models.self_eval import SelfEvaluation
from app.models.user import User

router = APIRouter(prefix="/teacher")
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard")
def teacher_dashboard(request: Request, db: Session = Depends(get_db)):
    user_role = request.session.get("user_role")
    if not user_role or user_role != "docente":
        return responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    activities = db.query(Activity).all()
    interactions = db.query(Interaction).all()
    evaluations = db.query(SelfEvaluation).all()
    students = db.query(User).filter(User.role == "estudante").all()

    student_map = {s.id: s.name for s in students}
    activity_map = {a.id: a.title for a in activities}

    level_counts = [0, 0, 0, 0, 0, 0]
    for inter in interactions:
        if 1 <= inter.help_level <= 6:
            level_counts[inter.help_level - 1] += 1

    avg_comprehension = 0.0
    avg_confidence = 0.0
    if evaluations:
        avg_comprehension = round(sum(e.comprehension_level for e in evaluations) / len(evaluations), 2)
        avg_confidence = round(sum(e.confidence_level for e in evaluations) / len(evaluations), 2)

    return templates.TemplateResponse(
        request=request,
        name="docente.html",
        context={
            "user_name": request.session.get("user_name"),
            "activities": activities,
            "interactions": interactions,
            "evaluations": evaluations,
            "students": students,
            "student_map": student_map,
            "activity_map": activity_map,
            "level_counts": level_counts,
            "avg_comprehension": avg_comprehension,
            "avg_confidence": avg_confidence
        }
    )

@router.post("/activity/create")
def create_activity(
    request: Request,
    title: str = Form(...),
    subject: str = Form(...),
    description: str = Form(...),
    max_help_level: int = Form(6),
    db: Session = Depends(get_db)
):
    user_role = request.session.get("user_role")
    user_id = request.session.get("user_id")
    
    if not user_role or user_role != "docente":
        return responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    new_activity = Activity(
        title=title,
        subject=subject,
        description=description,
        max_help_level=max_help_level,
        docente_id=user_id
    )
    db.add(new_activity)
    db.commit()

    return responses.RedirectResponse(url="/teacher/dashboard", status_code=status.HTTP_303_SEE_OTHER)

# ENDPOINT AJAX: Atualização em Tempo Real da Régua do Nível Socrático
@router.post("/activity/update-level/{activity_id}")
async def update_activity_level(
    activity_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user_role = request.session.get("user_role")
    if not user_role or user_role != "docente":
        return responses.JSONResponse(status_code=403, content={"error": "Não autorizado"})

    body = await request.json()
    new_level = int(body.get("max_help_level", 6))
    new_level = min(max(new_level, 1), 6)

    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        return responses.JSONResponse(status_code=404, content={"error": "Atividade não encontrada"})

    activity.max_help_level = new_level
    db.commit()

    return {"status": "success", "activity_id": activity_id, "new_level": new_level}

@router.get("/export-csv")
def export_csv(request: Request, db: Session = Depends(get_db)):
    user_role = request.session.get("user_role")
    if not user_role or user_role != "docente":
        return responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    interactions = db.query(Interaction).all()
    users = {u.id: u.name for u in db.query(User).all()}
    activities = {a.id: a.title for a in db.query(Activity).all()}

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID Interacao", "Estudante", "Atividade", "Nivel de Ajuda",
        "Pergunta/Tentativa do Estudante", "Resposta do Tutor Socratico", "Data/Hora"
    ])

    for inter in interactions:
        writer.writerow([
            inter.id,
            users.get(inter.user_id, f"ID {inter.user_id}"),
            activities.get(inter.activity_id, "Geral"),
            inter.help_level,
            inter.student_prompt,
            inter.ai_response,
            inter.created_at.strftime("%Y-%m-%d %H:%M:%S") if inter.created_at else ""
        ])

    response = responses.StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=relatorio_interacoes_socraticas.csv"
    return response