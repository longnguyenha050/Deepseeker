from langchain_openai import ChatOpenAI
import time

llm = ChatOpenAI(
    model="llm_proxy", 
    openai_api_base="http://localhost:4000",
    openai_api_key="sk-fake",
    temperature=0
)

print("--- Bắt đầu test xoay vòng ---")

# Check for changing
for i in range(1, 5):
    try:
        response = llm.invoke(f"Hello, what is your model's architecture name? For example: gemini-2.5-flash")
        print(f"\nLần {i}: {response.content}")
        print("-" * 30)
    except Exception as e:
        print(f"Lần {i} lỗi: {e}")
    
    time.sleep(1)