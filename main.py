import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.database import engine, Base, SessionLocal
from app.models.user import User
from app.models.activity import Activity
from app.routes import auth, admin, teacher, student

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Criar utilizadores pré-cadastrados se a base estiver vazia
    if db.query(User).count() == 0:
        admin_user = User(name="Administrador", email="admin@tutor.com", password="admin123", role="admin", is_active=True)
        teacher_user = User(name="Professor Carlos", email="docente@tutor.com", password="docente123", role="docente", is_active=True)
        student_user = User(name="Aluno Lucas", email="aluno@tutor.com", password="aluno123", role="estudante", is_active=True)
        
        db.add_all([admin_user, teacher_user, student_user])
        db.commit()

        # Criar atividade inicial com Régua Socrática Nível 6
        initial_activity = Activity(
            title="Estruturas Repetitivas (While / For)",
            subject="Programação I",
            description="Crie um programa em Python que leia números inteiros até que o utilizador digite 0, e exiba a soma acumulada.",
            max_help_level=6,
            docente_id=teacher_user.id
        )
        db.add(initial_activity)
        db.commit()

    db.close()
    yield

app = FastAPI(title="Tutor Socrático IA", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key="chave_secreta_socratic_tutor_2026")

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(teacher.router)
app.include_router(student.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)