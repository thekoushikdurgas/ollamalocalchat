from datetime import datetime
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, Text, DateTime

class Base(DeclarativeBase):
    pass

class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    role = Column(String(10), nullable=False)  # 'user' or 'bot'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Structured output models
class FriendInfo(BaseModel):
    name: str
    age: int
    is_available: bool

class FriendList(BaseModel):
    friends: list[FriendInfo]

# Add more structured output models as needed
class WeatherInfo(BaseModel):
    temperature: float
    conditions: str
    location: str

class RecipeInfo(BaseModel):
    name: str
    ingredients: list[str]
    steps: list[str]


    def to_dict(self):
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content,
            'created_at': self.created_at.isoformat()
        }