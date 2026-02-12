from typing import List, TypedDict

class GraphState(TypedDict):
    question: str           # Câu hỏi người dùng
    generation: str         # Câu trả lời từ LLM
    documents: List[str]    # Context tìm được
    web_search: str         # Cờ: "Yes" hoặc "No"
    loop_step: int          # Đếm số lần lặp lại (quan trọng!)