from langgraph.graph import END, StateGraph
from graph.state import GraphState
from graph.nodes import *
from graph.edges import *

# 1. Khởi tạo
workflow = StateGraph(GraphState)

# 2. Thêm Nodes
workflow.add_node("retrieve", retrieve)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("generate", generate)
# workflow.add_node("web_search_node", web_search)

# 3. Entry Point
workflow.set_entry_point("retrieve")

# 4. Normal Edges (Đi thẳng)
workflow.add_edge("retrieve", "grade_documents")

# 5. Conditional Edges (Rẽ nhánh)
workflow.add_conditional_edges(
    "grade_documents",      # Node xuất phát
    route_to_research,      # Hàm router logic
    {                       # Mapping: Kết quả hàm -> Tên Node đích
        "web_search_node": "web_search_node",
        "generate": "generate",
    }
)

workflow.add_conditional_edges(
    "generate",
    check_hallucination,
    {
        "generate": "generate", # Loop lại
        "end": END
    }
)

# 6. Compile
app = workflow.compile()