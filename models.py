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
from typing import Optional, Any

class ChatResponse(BaseModel):
    content: str
    format_type: Optional[str] = None
    structured_data: Optional[Any] = None

class FriendInfo(BaseModel):
    name: str
    age: int
    is_available: bool

class FriendList(BaseModel):
    friends: list[FriendInfo]

# Image analysis models
class ImageObject(BaseModel):
    name: str
    confidence: float
    attributes: str

class ImageAnalysis(BaseModel):
    summary: str
    objects: list[ImageObject]
    scene: str
    colors: list[str]
    time_of_day: Literal['Morning', 'Afternoon', 'Evening', 'Night']
    setting: Literal['Indoor', 'Outdoor', 'Unknown']
    text_content: str | None = None

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