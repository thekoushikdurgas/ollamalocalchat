
from datetime import datetime
from typing import Optional, Any, List, Literal
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, Text, DateTime

# Database Models
class Base(DeclarativeBase):
    pass

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    role = Column(String(10), nullable=False)
    content = Column(Text, nullable=False) 
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content,
            'created_at': self.created_at.isoformat()
        }

# Response Models
class ChatResponse(BaseModel):
    content: str
    format_type: Optional[str] = None
    structured_data: Optional[Any] = None

# Friend Models
class FriendInfo(BaseModel):
    name: str
    age: int
    is_available: bool

class FriendList(BaseModel):
    friends: List[FriendInfo]

# Image Analysis Models
class ImageObject(BaseModel):
    name: str
    confidence: float
    attributes: str

class ImageAnalysis(BaseModel):
    summary: str
    objects: List[ImageObject]
    scene: str
    colors: List[str]
    time_of_day: Literal['Morning', 'Afternoon', 'Evening', 'Night']
    setting: Literal['Indoor', 'Outdoor', 'Unknown']
    text_content: Optional[str] = None

# Other Models
class WeatherInfo(BaseModel):
    temperature: float
    conditions: str
    location: str

class RecipeInfo(BaseModel):
    name: str
    ingredients: List[str]
    steps: List[str]
