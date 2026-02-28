import os

from langchain_cohere import CohereRerank
from langchain_tavily import TavilySearch
from langchain_core.documents import Document
from app.core.config import settings

class InternetRetriever:
    def __init__(self):
        self.top_n = settings.RERANK_TOP_N
        self.tavily_search_tool = TavilySearch(
            max_results=10,
            topic="general",
        )

        self.compressor = CohereRerank(
            cohere_api_key=os.getenv("COHERE_API_KEY"), 
            model="rerank-multilingual-v3.0",
            top_n=self.top_n
        )
    def retrieve(self, query: str):
        search_result = self.tavily_search_tool.invoke(query)
        documents = []
        for result in search_result.get("results", []):
            content = result.get("content", "")
            title = result.get("title", "")
            url = result.get("url", "")

            # Tạo Document object với metadata (title, url)
            doc = Document(
                page_content=content,
                metadata={"title": title, "url": url, "source": "internet"}
            )
            documents.append(doc)
        
        # Compressor expects Document objects
        compressed_docs = self.compressor.compress_documents(documents, query)
        return compressed_docs