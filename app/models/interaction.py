from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from app.database import Base

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=True)
    help_level = Column(Integer, default=1)
    student_prompt = Column(String, nullable=False)
    ai_response = Column(String, nullable=False)
    
    # Métricas de consumo de Tokens OpenAI
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)