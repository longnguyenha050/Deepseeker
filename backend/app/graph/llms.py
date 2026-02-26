from langchain_openai import ChatOpenAI

fast_llm = ChatOpenAI(
    model="fast-model", 
    openai_api_base="http://localhost:4000",
    openai_api_key="sk-fake",
    temperature=0
)
best_llm = ChatOpenAI(
    model="best-model", 
    openai_api_base="http://localhost:4000",
    openai_api_key="sk-fake",
    temperature=0
)
mql_llm = ChatOpenAI(
    model="mql-model", 
    openai_api_base="http://localhost:4000",
    openai_api_key="sk-fake",
    temperature=0
)