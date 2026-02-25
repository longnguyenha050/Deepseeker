from pydantic import BaseModel, Field
from typing import List, Optional

class GraphInput(BaseModel):
    """The data that needs to be sent by FE."""
    question: str = Field(..., description="User's question")
    # session_id: Optional[str] = Field(default="default-session", description="ID phiên chat")

class GraphOutput(BaseModel):
    """The data that BE returns."""
    generation: str
    documents: List[str]