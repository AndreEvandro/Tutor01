from fastapi import APIRouter, Request, responses, status
from pydantic import BaseModel
from app.controllers.pedagogy_controller import PedagogyController

router = APIRouter(prefix="/student")
pedagogy = PedagogyController(max_help_level=5)

class MessageRequest(BaseModel):
    message: str
    current_level: int = 1

@router.post("/chat")
def chat_interaction(data: MessageRequest, request: Request):
    user_role = request.session.get("user_role")
    if not user_role or user_role != "estudante":
        return responses.JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Acesso não autorizado."}
        )

    # Gera resposta pedagógica baseada no nível atual
    result = pedagogy.generate_socratic_response(data.message, data.current_level)
    return result