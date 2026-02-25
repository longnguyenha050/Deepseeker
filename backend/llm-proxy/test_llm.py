from langchain_openai import ChatOpenAI
import time

fast_llm = ChatOpenAI(
    model="fast-model", 
    openai_api_base="http://localhost:4000",
    openai_api_key="sk-fake",
    temperature=0.7
)

best_llm = ChatOpenAI(
    model="best-model", 
    openai_api_base="http://localhost:4000",
    openai_api_key="sk-fake",
    temperature=0.7
)

print("--- Bắt đầu test xoay vòng ---")

# Check for changing
for i in range(1, 5):
    try:
        import time
        start = time.time()
        response = fast_llm.invoke(f"Hello, who are you?")
        print(f"\nLần {i}: - Time: {round((time.time()-start)*1000)} ms -- {response.content}")
        print("-" * 30)
    except Exception as e:
        print(f"Lần {i} lỗi: {e}")

for i in range(1, 5):
    try:
        import time
        start = time.time()
        response = best_llm.invoke(f"Hello, what is your model's architecture name? For example: gemini-2.5-flash")
        print(f"\nLần {i}: - Time: {round((time.time()-start)*1000)} ms -- {response.content}")
        print("-" * 30)
    except Exception as e:
        print(f"Lần {i} lỗi: {e}")
    