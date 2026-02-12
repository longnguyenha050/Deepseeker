from graph.state import GraphState

def route_to_research(state: GraphState):
    """
    Quyết định: Tìm kiếm Web hay Generate luôn?
    """
    if state["web_search"] == "Yes":
        return "web_search_node" # Tên node phải khớp trong workflow
    return "generate"

def check_hallucination(state: GraphState):
    """
    Quyết định: Câu trả lời có bịa không?
    """
    # Nếu lặp quá 3 lần -> Dừng lại để tiết kiệm tiền
    if state["loop_step"] > 3:
        return "end"

    # score = hallucination_grader.invoke(...)
    score = 0
    if score.binary_score == "yes":
        return "end" # Tốt -> Kết thúc
    else:
        return "generate" # Bịa -> Generate lại