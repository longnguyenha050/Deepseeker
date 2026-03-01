from app.graph.flows.mongo_flow import build_mongo_app
from app.graph.llms import best_llm, fast_llm
from app.graph.prompts.prompts import (
    ANSWER_SYNTHESIS_PROMPT,
    QUERY_TRANSLATION,
    ROUTER_SYSTEM_PROMPT,
)
from app.graph.retrievers.internet import InternetRetriever
from app.graph.retrievers.vectordb import VectorDBRetriever
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from .state import ClassificationResult, GraphState

vector_retriever = VectorDBRetriever()
internet_retriever = InternetRetriever()
mongo_app = build_mongo_app()


def query_translation(state: GraphState):
    print("---NODE: QUERY TRANSLATION---")

    prompt_perspectives = ChatPromptTemplate.from_template(QUERY_TRANSLATION)

    generate_queries_chain = (
        prompt_perspectives
        | fast_llm
        | StrOutputParser()
        | (lambda x: [q.strip() for q in x.split("\n") if q.strip()])
    )

    questions = generate_queries_chain.invoke({"question": state.get("question")})
    print("Generated query variations:")
    for q in questions:
        print(f"  - {q}")
    return {"questions": questions}


# def classify_query(state: GraphState) -> dict:
#     """Classify query and determine which agents to invoke."""
#     print("---NODE: QUERY CLASSIFICATION---")
#     structured_llm = fast_llm.with_structured_output(ClassificationResult)

#     questions_to_process = state.get("questions", [state["question"]])

#     all_classifications = []

#     for q in questions_to_process:
#         result = structured_llm.invoke(
#             [
#                 {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
#                 {"role": "user", "content": q},
#             ]
#         )

#         if result and result.classifications:
#             for c in result.classifications:
#                 all_classifications.append({"source": c["source"], "query": q})

#     return {"classifications": all_classifications}

def classify_query(state: GraphState) -> dict:
    print("---NODE: QUERY CLASSIFICATION---")
    questions_to_process = state.get("questions", [state["question"]])
    all_classifications = []

    for q in questions_to_process:
        # gọi LLM thô (không dùng with_structured_output)
        resp = fast_llm.invoke(
            [
                {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                {"role": "user", "content": q},
            ]
        )

        # Log token usage nếu có
        if hasattr(resp, "usage_metadata"):
            u = resp.usage_metadata
            print(f"  Classification tokens - In:{u.get('input_tokens',0)} Out:{u.get('output_tokens',0)} Total:{u.get('total_tokens',0)}")

        raw = getattr(resp, "content", "") or str(resp)

        # Thử parse JSON; fallback: tìm các dòng 'source: ...' bằng regex/simple parsing
        parsed = None
        try:
            parsed = json.loads(raw)
        except Exception:
            # ví dụ expected format: [{"source":"mongodb_retriever","query":"..."}]
            try:
                # minimal safe fallback: look for JSON array inside text
                start = raw.find("[")
                end = raw.rfind("]") + 1
                if start != -1 and end != -1 and end > start:
                    parsed = json.loads(raw[start:end])
            except Exception:
                parsed = None

        if isinstance(parsed, list):
            for item in parsed:
                src = item.get("source") if isinstance(item, dict) else None
                if src:
                    all_classifications.append({"source": src, "query": q})
        else:
            # Last-resort: if LLM returned plain text like "mongodb_retriever"
            if "mongodb" in raw:
                all_classifications.append({"source": "mongodb_retriever", "query": q})
            elif "vector" in raw or "vectordb" in raw:
                all_classifications.append({"source": "vectordb_retriever", "query": q})
            elif "internet" in raw:
                all_classifications.append({"source": "internet_retriever", "query": q})
            elif "greeting" in raw:
                all_classifications.append({"source": "greeting", "query": q})

    return {"classifications": all_classifications}


def vectordb_retriever(state: dict):
    query = state.get("query")

    print("---NODE: VECTOR DB RETRIEVER---")
    print(f"Query: {query}")

    documents = vector_retriever.retrieve(query)
    documents_text = [doc.page_content for doc in documents]

    return {"documents": documents_text}


def internet_search_retriever(state: dict):
    query = state.get("query")
    print("---NODE: INTERNET SEARCH RETRIEVER---")
    print(f"Query: {query}")
    documents = internet_retriever.retrieve(query)
    documents_text = [doc.page_content for doc in documents]
    return {"documents": documents_text}


def mongodb_retriever(state: dict):
    print("---NODE: MONGODB RETRIEVER---")
    print(f"Query: {state.get('query')}")
    # results = []
    documents = []

    branch_result = mongo_app.invoke(
        {"query": state.get("query", ""), "messages": state.get("messages", [])}
    )

    documents.append(branch_result.get("messages", [])[-1].content)

    # print ("MongoDB Retriever Result:", branch_result)
    return {"documents": documents}

def greeting(state: dict):
    print("---NODE: GREETING---")
    return {"greeting": "Hello! How can I assist you today?"}

def generate(state: GraphState):
    question = state.get("question", "")
    documents = state.get("documents", [])

    docs_text = "\n\n".join(doc for doc in documents)

    prompt = ANSWER_SYNTHESIS_PROMPT.format(question=question, documents=docs_text)

    resp = best_llm.invoke(prompt)
    return {"generation": resp.content}
