import time
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

# ==========================================
# 1. ĐỊNH NGHĨA STATE
# ==========================================
class GraphState(TypedDict):
    question: str
    documents: List[str]
    generation: str
    web_search: str

# ==========================================
# 2. ĐỊNH NGHĨA CÁC NODES (MOCK WORKERS)
# ==========================================
def retrieve(state: GraphState):
    print("---NODE: MOCK RETRIEVE---")
    time.sleep(1) # Giả lập thời gian query Database mất 1 giây
    return {"documents": ["Tài liệu nội bộ 1: LangGraph rất tuyệt.", "Tài liệu nội bộ 2: API nhanh."]}

def grade_documents(state: GraphState):
    print("---NODE: MOCK GRADE---")
    time.sleep(1) # Giả lập thời gian LLM chấm điểm
    question = state.get("question", "").lower()
    
    # LOGIC GIẢ LẬP ĐỂ TEST RẼ NHÁNH:
    # Nếu câu hỏi có chữ "google", ta giả vờ là tài liệu nội bộ không đủ -> Bật cờ Web Search
    if "google" in question:
        print("   -> Không đủ thông tin, cần tìm web!")
        return {"web_search": "Yes"}
    
    print("   -> Tài liệu hợp lệ, tạo câu trả lời luôn!")
    return {"web_search": "No"}

def web_search_node(state: GraphState):
    print("---NODE: MOCK WEB SEARCH---")
    time.sleep(1.5) # Giả lập search internet mất 1.5 giây
    docs = state.get("documents", [])
    docs.append("Kết quả từ Internet: Thông tin mới nhất năm nay.")
    return {"documents": docs}

def generate(state: GraphState):
    print("---NODE: MOCK GENERATE---")
    time.sleep(2) # Giả lập thời gian LLM sinh câu trả lời
    
    docs = state.get("documents", [])
    doc_text = "\n- ".join(docs)
    
    mock_answer = (
        f"🤖 Đây là câu trả lời GIẢ LẬP cho câu hỏi: '{state['question']}'.\n\n"
        f"Tôi đã dựa vào các thông tin sau:\n- {doc_text}\n\n"
        f"✅ Xử lý thành công!"
    )
    return {"generation": mock_answer}

# ==========================================
# 3. ĐỊNH NGHĨA EDGES (ROUTERS)
# ==========================================
def route_after_grade(state: GraphState):
    """Quyết định hướng đi dựa trên cờ web_search"""
    if state.get("web_search") == "Yes":
        return "web_search_node"
    return "generate"

# ==========================================
# 4. LẮP RÁP GRAPH
# ==========================================
workflow = StateGraph(GraphState)

# Khai báo Nodes
workflow.add_node("retrieve", retrieve)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("web_search_node", web_search_node)
workflow.add_node("generate", generate)

# Định nghĩa luồng (Edges)
workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "grade_documents")

# Rẽ nhánh có điều kiện
workflow.add_conditional_edges(
    "grade_documents",
    route_after_grade,
    {
        "web_search_node": "web_search_node",
        "generate": "generate"
    }
)

workflow.add_edge("web_search_node", "generate")
workflow.add_edge("generate", END)

# Compile thành app_graph để main.py import
app_graph = workflow.compile()