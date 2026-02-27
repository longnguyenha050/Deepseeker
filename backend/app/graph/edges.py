from app.graph.state import GraphState
from langgraph.types import Send
from langchain_core.messages import HumanMessage

def route_to_agents(state: GraphState) -> list[Send]:
    sends = []

    for i, c in enumerate(state["classifications"]):
        sub_query = c["query"]
        source = c["source"]

        base_state = {
            "question": state["question"],
            "query": sub_query,
        }

        if source == "mongodb_retriever":
            base_state["messages"] = [
                {"role": "user", "content": sub_query}
            ]

        sends.append(Send(source, base_state))

    return sends