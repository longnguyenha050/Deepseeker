from typing import List, Literal, Annotated
from typing_extensions import TypedDict
import operator
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage

class Classification(TypedDict):
    """A single routing decision: which agent to call with what query."""
    source: Literal["mongodb_retriever", "internet_retriever", "vectordb_retriever"]
    query: str

class ClassificationResult(BaseModel):
    """Result of classifying a user query into agent-specific sub-questions."""
    classifications: list[Classification] = Field(
        description="List of agents to invoke with their targeted sub-questions"
    )

class GraphState(TypedDict):
    question: str           # Câu hỏi người dùng
    generation: str         # Câu trả lời từ LLM
    questions: list[str]
    documents: Annotated[list[str], operator.add]
    # loop_step: int          # Đếm số lần lặp lại (quan trọng!)
    classifications: list[Classification] 
    # sub_query: str             # Câu hỏi con hiện tại đang được xử lý
    # messages: list[BaseMessage]         

class MongoState(TypedDict):
    query: str
    messages: Annotated[list, operator.add]