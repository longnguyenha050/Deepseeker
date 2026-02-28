import os

from langchain_classic.retrievers import ContextualCompressionRetriever
from app.utils.indexing import ContextualRAGBuilder
from app.core.config import settings
from langchain_cohere import CohereRerank


class VectorDBRetriever:
    def __init__(self):
        self.doc_path = settings.DOC_DIRECTORY
        self.top_n = settings.RERANK_TOP_N
        self.base_retriever = self._build_base_retriever()

        self.compressor = CohereRerank(
            cohere_api_key=os.getenv("COHERE_API_KEY"),
            model="rerank-multilingual-v3.0",
            top_n=self.top_n,
        )

        self.retriever = ContextualCompressionRetriever(
            base_retriever=self.base_retriever, base_compressor=self.compressor
        )

    def _build_base_retriever(self):
        builder = ContextualRAGBuilder()

        all_docs = builder.load_documents(self.doc_path)
        vector_db = builder.build_vector_store(all_docs)

        return builder.create_ensemble_retriever(vector_db, all_docs)

    def retrieve(self, query: str):
        return self.retriever.invoke(query)
