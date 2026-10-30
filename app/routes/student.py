from fastapi import APIRouter, Request, Depends, Form, responses, status
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

from app.database import get_db
from app.models.activity import Activity
from app.models.interaction import Interaction
from app.models.self_eval import SelfEvaluation
from app.controllers.pedagogy_controller import PedagogyController

router = APIRouter(prefix="/student")
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard")
def student_dashboard(request: Request, activity_id: int = None, db: Session = Depends(get_db)):
    user_role = request.session.get("user_role")
    user_id = request.session.get("user_id")

    if not user_role or user_role != "estudante":
        return responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    activities = db.query(Activity).all()
    selected_activity = None
    interactions = []

    if activities:
        if activity_id:
            selected_activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not selected_activity:
            selected_activity = activities[0]

        interactions = db.query(Interaction).filter(
            Interaction.user_id == user_id,
            Interaction.activity_id == selected_activity.id
        ).order_by(Interaction.created_at.asc()).all()

    return templates.TemplateResponse(
        request=request,
        name="estudante.html",
        context={
            "user_name": request.session.get("user_name"),
            "activities": activities,
            "selected_activity": selected_activity,
            "interactions": interactions
        }
    )

@router.post("/chat")
def send_student_message(
    request: Request,
    activity_id: int = Form(...),
    student_prompt: str = Form(...),
    db: Session = Depends(get_db)
):
    user_role = request.session.get("user_role")
    user_id = request.session.get("user_id")

    if not user_role or user_role != "estudante":
        return responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        return responses.RedirectResponse(url="/student/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    controller = PedagogyController(max_help_level=activity.max_help_level)
    result = controller.process_interaction(student_prompt=student_prompt, help_level=activity.max_help_level)

    new_interaction = Interaction(
        user_id=user_id,
        activity_id=activity_id,
        help_level=result["level"],
        student_prompt=student_prompt,
        ai_response=result["response"],
        prompt_tokens=result.get("prompt_tokens", 0),
        completion_tokens=result.get("completion_tokens", 0),
        total_tokens=result.get("total_tokens", 0)
    )
    db.add(new_interaction)
    db.commit()

    return responses.RedirectResponse(
        url=f"/student/dashboard?activity_id={activity_id}",
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.post("/self-evaluation")
def submit_self_eval(
    request: Request,
    activity_id: int = Form(...),
    solved_alone: bool = Form(...),
    comprehension_level: int = Form(...),
    confidence_level: int = Form(3),
    main_difficulty: str = Form(None),
    helpful_strategy: str = Form(None),
    db: Session = Depends(get_db)
):
    user_role = request.session.get("user_role")
    user_id = request.session.get("user_id")

    if not user_role or user_role != "estudante":
        return responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    new_eval = SelfEvaluation(
        user_id=user_id,
        activity_id=activity_id,
        solved_alone=solved_alone,
        comprehension_level=comprehension_level,
        confidence_level=confidence_level,
        main_difficulty=main_difficulty,
        helpful_strategy=helpful_strategy
    )
    db.add(new_eval)
    db.commit()

    return responses.RedirectResponse(
        url=f"/student/dashboard?activity_id={activity_id}",
        status_code=status.HTTP_303_SEE_OTHER
    )