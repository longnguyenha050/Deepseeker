from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_chroma import Chroma
from .state import ClassificationResult, GraphState
import time
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, StateGraph
from typing import Literal
from core.config import settings
from graph.llms import fast_llm, mql_llm, best_llm
from graph.prompts.prompts import ROUTER_SYSTEM_PROMPT, QUERY_TRANSLATION, ANSWER_SYNTHESIS_PROMPT
from graph.retrievers.vectordb import VectorDBRetriever
from graph.retrievers.internet import InternetRetriever
from graph.flows.mongo_flow import build_mongo_app



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


def classify_query(state: GraphState) -> dict:
    """Classify query and determine which agents to invoke."""
    print("---NODE: QUERY CLASSIFICATION---")
    structured_llm = fast_llm.with_structured_output(ClassificationResult)

    questions_to_process = state.get("questions", [state["question"]])
    
    all_classifications = []

    for q in questions_to_process:
        result = structured_llm.invoke([
            {
                "role": "system",
                "content": ROUTER_SYSTEM_PROMPT
            },
            {"role": "user", "content": q}
        ])
        
        if result and result.classifications:
            for c in result.classifications:
                all_classifications.append({
                    "source": c["source"], 
                    "query": q  
                })

    return {"classifications": all_classifications}



def vectordb_retriever(state: dict):
    query = state.get("query")

    print(f"---NODE: VECTOR DB RETRIEVER---")
    print(f"Query: {query}")

    documents = vector_retriever.retrieve(query)

    return {
        "documents": documents
    }

def internet_search_retriever(state: dict):
    query = state.get("query")
    print(f"---NODE: INTERNET SEARCH RETRIEVER---")
    print(f"Query: {query}")
    documents = internet_retriever.retrieve(query)
    return {"documents": documents}

def mongodb_retriever(state: dict):
    print(f"---NODE: MONGODB RETRIEVER---")
    print(f"Query: {state.get('query')}")
    results = []
    documents = []
    
    branch_result = mongo_app.invoke({
        "query": state.get("query", ""),
        "messages": state.get("messages", [])
    })

    documents.append(
            Document(
                page_content=branch_result.get("messages", [])[-1].content,
                metadata={
                    "type": "mongodb"
                }
            )
        )


    # print ("MongoDB Retriever Result:", branch_result)
    return {"documents": documents}



def generate(state: GraphState):

    question = state.get("question", "")
    documents = state.get("documents", [])

    docs_text = "\n\n".join(
        doc.page_content for doc in documents
    )

    prompt = ANSWER_SYNTHESIS_PROMPT.format(
        question=question,
        documents=docs_text
    )

    resp = best_llm.invoke(prompt)
    return {"generation": resp.content}





