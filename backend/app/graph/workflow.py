from langgraph.graph import END, StateGraph
from app.graph.state import GraphState
from app.graph.nodes import classify_query, query_translation, vectordb_retriever, internet_search_retriever, mongodb_retriever, greeting, generate
from app.graph.edges import route_to_agents
# from app.graph.nodes import *
# from app.graph.edges import *

# 1. Khởi tạo Graph
workflow = StateGraph(GraphState)

# 2. Thêm các Node chính
workflow.add_node("query_translation", query_translation)
workflow.add_node("classify_query", classify_query)
workflow.add_node("vectordb_retriever", vectordb_retriever)
workflow.add_node("internet_retriever", internet_search_retriever)
workflow.add_node("mongodb_retriever", mongodb_retriever)
workflow.add_node("greeting", greeting)
workflow.add_node("generate", generate)

# 5. Thiết lập luồng đi
# workflow.set_entry_point("query_translation")
# workflow.add_edge("query_translation", "classify_query")
workflow.set_entry_point("classify_query")
workflow.add_conditional_edges(
    "classify_query",
    route_to_agents,
    ["mongodb_retriever", "vectordb_retriever", "internet_retriever","greeting"]
)
workflow.add_edge("mongodb_retriever", "generate")
workflow.add_edge("vectordb_retriever", "generate")
workflow.add_edge("internet_retriever", "generate")
workflow.add_edge("greeting", "generate")
workflow.add_edge("generate", END)

# 6. Compile và Chạy
app_graph = workflow.compile(debug=True)

# if __name__ == "__main__":
#     result = app_workflow.invoke({
#         # "question": "What is the status of customer order #12345 and do we have any internal documentation on handling pending orders?",
#         "question": "Tổng số lượng hàng tồn kho của shop?",
#     })
#     print("==================================================")
#     print(result["generation"])  # In ra câu trả lời cuối cùng từ LLM sau khi tổng hợp thông tin từ các retriever