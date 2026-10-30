from sqlalchemy import Column, Integer, Text, Boolean, DateTime, ForeignKey
from datetime import datetime
from app.database import Base

class SelfEvaluation(Base):
    __tablename__ = "self_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False)
    solved_alone = Column(Boolean, default=True)
    comprehension_level = Column(Integer, default=5)
    confidence_level = Column(Integer, default=5)
    main_difficulty = Column(Text, nullable=True)
    helpful_strategy = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)