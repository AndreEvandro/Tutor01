import os
from fastapi import FastAPI, Request, Depends, responses, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.database import engine, Base, get_db
from app.models.user import User
from app.routes.auth import router as auth_router
from app.routes.student import router as student_router

os.makedirs("static", exist_ok=True)
os.makedirs("app/templates", exist_ok=True)

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(auth_router)
app.include_router(student_router)

def seed_initial_users(db: Session):
    if db.query(User).count() == 0:
        initial_users = [
            User(name="Administrador", email="admin@tutor.com", password="admin123", role="admin"),
            User(name="Docente Exemplo", email="docente@tutor.com", password="docente123", role="docente"),
            User(name="Estudante Exemplo", email="aluno@tutor.com", password="aluno123", role="estudante"),
        ]
        db.add_all(initial_users)
        db.commit()

@app.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    seed_initial_users(db)
    return responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)