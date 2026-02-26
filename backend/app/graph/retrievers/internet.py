from langchain_tavily import TavilySearch
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_core.documents import Document
from core.config import settings

class InternetRetriever:
    def __init__(self):
        self.top_n = settings.RERANK_TOP_N
        self.tavily_search_tool = TavilySearch(
            max_results=10,
            topic="general",
        )
        self.reranker = HuggingFaceCrossEncoder(
            model_name="BAAI/bge-reranker-v2-m3"
        )

        self.compressor = CrossEncoderReranker(
            model=self.reranker,
            top_n=self.top_n
        )
    def retrieve(self, query: str):
        search_result = self.tavily_search_tool.invoke(query)
        documents = []
        for result in search_result.get("results", []):
            content = result.get("content", "")
            title = result.get("title", "")
            url = result.get("url", "")

            documents.append(
                Document(
                    page_content=content,
                    metadata={
                        "title": title,
                        "source": url,
                        "type": "internet"
                    }
                )
            )
        compressed_docs = self.compressor.compress_documents(
        documents,
        query
        )
        return compressed_docs