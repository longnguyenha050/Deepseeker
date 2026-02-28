import json
from typing import Literal

from app.core.config import settings
from app.graph.llms import best_llm, fast_llm, mql_llm
from app.graph.prompts.prompts import FORMAT_SYS
from app.graph.retrievers.mongodb import MongoDBRetriever
from app.graph.state import MongoState
from langchain_core.messages import AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_mongodb.agent_toolkit import MONGODB_AGENT_SYSTEM_PROMPT
from langgraph.graph import StateGraph

mongo_retriever = MongoDBRetriever(best_llm)


def list_collections(state: dict):
    """Deterministic node to list only allowed collections"""
    # messages = state.get("messages", [])
    # call = {
    #     "name": "mongodb_list_collections",
    #     "args": {},
    #     "id": "abc",
    #     "type": "tool_call",
    # }

    summary = AIMessage(
        content=f"Available collections: {', '.join(settings.ALLOWED_COLLECTIONS)}"
    )
    return {"messages": [summary]}


def call_get_schema(state: dict):
    """Deterministic call to fetch schema for allowed collections"""

    call = {
        "name": "mongodb_schema",
        "args": {"collection_names": ", ".join(settings.ALLOWED_COLLECTIONS)},
        "id": "schema_call_1",
        "type": "tool_call",
    }

    call_msg = AIMessage(content="", tool_calls=[call])

    resp = mongo_retriever.tool_map["mongodb_schema"].invoke(call)

    return {"messages": [call_msg, resp]}


def generate_query(state: dict):
    """Generate MongoDB aggregation pipeline"""
    messages = state.get("messages", [])
    # print("messages get schema:", messages)
    llm_with = mql_llm.bind_tools(
        [mongo_retriever.tool_map["mongodb_query"]], tool_choice="mongodb_query"
    )
    resp = llm_with.invoke(
        [{"role": "system", "content": MONGODB_AGENT_SYSTEM_PROMPT}]
        + state.get("messages", [])
    )
    # print("==================================================")
    # print(resp)
    result = {"messages": messages + [resp]}
    print("messages after generate query:", [resp])
    return {"messages": [resp]}


def check_query(state: dict):
    """Validate and sanitize generated query"""
    messages = state.get("messages", [])
    original = messages[-1].tool_calls[0]["args"]["query"]
    resp = mql_llm.bind_tools(
        [mongo_retriever.tool_map["mongodb_query"]], tool_choice="any"
    ).invoke(
        [
            {"role": "system", "content": MONGODB_AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": original},
        ]
    )
    resp.id = messages[-1].id

    return {"messages": [resp]}


def format_answer(state: dict):
    messages = state.get("messages", [])
    # print("messages check query:", messages)
    raw_json = messages[-1].content
    question = state.get("query", "the user's query")

    try:
        data = json.loads(raw_json)
        docs_str = json.dumps(data, indent=2)

    except Exception:
        docs_str = raw_json

    print("==================================================")
    print("Raw query result:", docs_str)

    format_prompt = ChatPromptTemplate.from_template(FORMAT_SYS)

    format_chain = format_prompt | fast_llm | StrOutputParser()

    response = format_chain.invoke({"question": question, "docs": docs_str})

    return {"messages": [AIMessage(content=response)]}


# def format_answer(state: dict):
#     """Enhanced format function with large dataset handling"""
#     import json

#     raw_json = state["messages"][-1].content
#     question = state.get("query", "the user's query")

#     try:
#         data = json.loads(raw_json)

#         if isinstance(data, list):
#             data_size = len(data)

#             if data_size == 0:
#                 return {
#                     "messages": [
#                         AIMessage(
#                             content=f'**Answer to:** "{question}"\n\nI couldn\'t find any matching documents.'
#                         )
#                     ]
#                 }

#             elif data_size > 50:  # Large dataset threshold
#                 # Show first 10 + summary
#                 sample_data = data[:10]
#                 response_parts = [
#                     f'**Answer to:** "{question}"',
#                     f"Found **{data_size}** results. Showing first 10:",
#                     "",
#                 ]

#                 for i, item in enumerate(sample_data, 1):
#                     if isinstance(item, dict) and "_id" in item:
#                         if "movieCount" in item:
#                             response_parts.append(
#                                 f"{i}. {item['_id']}: {item['movieCount']} movies"
#                             )
#                         else:
#                             response_parts.append(f"{i}. {item['_id']}")

#                 response_parts.extend(
#                     [
#                         "",
#                         f"... and {data_size - 10} more results.",
#                         "💡 **Tip**: Try 'Show me the top 10...' for more manageable results",
#                     ]
#                 )

#                 formatted_response = "\n".join(response_parts)

#             else:  # Normal size dataset
#                 response_parts = [f'**Answer to:** "{question}"', ""]
#                 for i, item in enumerate(data, 1):
#                     if isinstance(item, dict) and "_id" in item:
#                         if "movieCount" in item:
#                             response_parts.append(
#                                 f"{i}. {item['_id']}: {item['movieCount']} movies"
#                             )
#                         else:
#                             response_parts.append(f"{i}. {item['_id']}")

#                 formatted_response = "\n".join(response_parts)
#         else:
#             formatted_response = f'**Answer to:** "{question}"\n\n{data!s}'

#     except Exception as e:
#         # Graceful error handling
#         formatted_response = f"**Answer to:** \"{question}\"\n\n⚠️ Large dataset found but too big to display. Try limiting your query (e.g., 'top 10', 'first 5')."

#     return {"messages": [AIMessage(content=formatted_response)]}


def need_checker(state: dict) -> Literal["generate_query", "check_query"]:
    """Conditional edge: run checker if tool call present"""
    messages = state.get("messages", [])
    return "check_query" if messages[-1].tool_calls else "generate_query"


def build_mongo_app():
    mongo_retriever = MongoDBRetriever(mql_llm)

    mongo_flow = StateGraph(MongoState)

    mongo_flow.add_node("list_collections", list_collections)
    mongo_flow.add_node("call_get_schema", call_get_schema)
    mongo_flow.add_node("get_schema", mongo_retriever.schema_node)
    mongo_flow.add_node("generate_query", generate_query)
    mongo_flow.add_node("check_query", check_query)
    mongo_flow.add_node("run_query", mongo_retriever.run_node)
    mongo_flow.add_node("format_answer", format_answer)

    mongo_flow.set_entry_point("list_collections")
    mongo_flow.add_edge("list_collections", "call_get_schema")
    mongo_flow.add_edge("call_get_schema", "get_schema")
    mongo_flow.add_edge("get_schema", "generate_query")
    mongo_flow.add_conditional_edges("generate_query", need_checker)
    mongo_flow.add_edge("check_query", "run_query")
    mongo_flow.add_edge("run_query", "format_answer")

    return mongo_flow.compile()
