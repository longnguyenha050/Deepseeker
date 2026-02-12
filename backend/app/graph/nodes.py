from graph.state import GraphState

def retrieve(state: GraphState):
    print("---NODE: RETRIEVE---")
    # Gọi service tìm kiếm
    # docs = retriever.invoke(state["question"])
    docs = {}
    return {"documents": docs}

def grade_documents(state: GraphState):
    print("---NODE: GRADE DOCUMENTS---")
    # Logic chấm điểm docs...
    # Giả sử trả về cờ web_search
    filtered_docs = {}
    return {"documents": filtered_docs, "web_search": "Yes"} # Chỉ update docs và flag

def generate(state: GraphState):
    print("---NODE: GENERATE---")
    # Logic sinh câu trả lời...
    result = ""
    return {"generation": result, "loop_step": state.get("loop_step", 0) + 1}