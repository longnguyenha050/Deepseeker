import os
import uuid
import asyncio
import logging
from typing import List, Dict, Any
from glob import glob
from pathlib import Path
import json

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.retrievers import BM25Retriever
from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_classic.retrievers import EnsembleRetriever
import os
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
class Config:
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    PDF_PATH_PATTERN = '../../../research/data/*.pdf'
    PERSIST_DIRECTORY = "../../../data/vector_db"
    DOCUMENT_DIRECTORY = "../../../data/contextual_docs.json"
    COLLECTION_NAME = "vector_db"
    EMBEDDING_MODEL = "gemini-embedding-001"
    RETRIEVAL_K = 5

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ContextualRAGBuilder:
    def __init__(self):
        self.embeddings = GoogleGenerativeAIEmbeddings(model=Config.EMBEDDING_MODEL)
        self.llm  = ChatOpenAI(
            model="fast-model", 
            openai_api_base="http://localhost:4000",
            openai_api_key="sk-fake",
            temperature=0
        )
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE, 
            chunk_overlap=Config.CHUNK_OVERLAP
        )


    def _get_context_prompt(self) -> ChatPromptTemplate:
        """Define the prompt for situating chunks."""
        template = """You are an AI assistant specializing in research paper analysis.
Situating a chunk of text within the overall document to improve search retrieval.

<paper>
{paper}
</paper>

<chunk>
{chunk}
</chunk>

Provide a concise context (3-4 sentences max). 
Focus on explaining what this section contributes to the overall paper.
Answer only with the succinct context starting with 'Focuses on...'. 
Do not mention 'this chunk' or 'this section'."""
        return ChatPromptTemplate.from_template(template)

    async def _generate_chunk_context(self, full_paper_text: str, chunk_content: str) -> str:
        """Asynchronously generate context for a single chunk."""
        chain = self._get_context_prompt() | self.llm | StrOutputParser()
        try:
            return await chain.ainvoke({'paper': full_paper_text, 'chunk': chunk_content})
        except Exception as e:
            logger.error(f"Error generating context: {e}")
            return "Context unavailable."

    async def process_document(self, file_path: str) -> List[Document]:
        """Load, split, and enrich a PDF document with context."""
        logger.info(f"Processing: {file_path}")
        
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        chunks = self.splitter.split_documents(pages)
        
        full_paper_text = "\n".join([p.page_content for p in pages])
        contextual_docs = []

        # Process chunks with rate limiting (10s delay as requested)
        for i, chunk in enumerate(chunks):
            context = await self._generate_chunk_context(full_paper_text, chunk.page_content)
            
            new_metadata = {
                'id': str(uuid.uuid4()),
                'page': chunk.metadata.get('page', 0),
                'source': file_path,
                'title': os.path.basename(file_path)
            }
            
            enriched_content = f"{context}\n\n{chunk.page_content}"
            contextual_docs.append(Document(page_content=enriched_content, metadata=new_metadata))
            
            logger.info(f"Progress [{os.path.basename(file_path)}]: {i+1}/{len(chunks)}")
            await asyncio.sleep(2) # Reduced sleep for performance, adjust if hitting rate limits

        return contextual_docs

    def build_vector_store(self, documents: List[Document] = None) -> Chroma:
        """Load ChromaDB if exists, otherwise create it."""
        
        db_exists = os.path.exists(Config.PERSIST_DIRECTORY) and \
                    len(os.listdir(Config.PERSIST_DIRECTORY)) > 0

        if db_exists:
            logger.info(f"Loading existing Vector Store from {Config.PERSIST_DIRECTORY}...")
            db = Chroma(
                persist_directory=Config.PERSIST_DIRECTORY,
                embedding_function=self.embeddings,
                collection_name=Config.COLLECTION_NAME
            )
        else:
            if not documents:
                raise ValueError("Database doesn't exist. You must provide documents to create a new one.")
            
            logger.info("Creating NEW Vector Store...")
            db = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=Config.PERSIST_DIRECTORY,
                collection_name=Config.COLLECTION_NAME,
                collection_metadata={"hnsw:space": "cosine"}
            )
        
        return db

    def create_ensemble_retriever(self, vector_db: Chroma, documents: List[Document]) -> EnsembleRetriever:
        """Configure Hybrid Search (BM25 + Vector)."""
        logger.info("Configuring Ensemble Retriever...")
        
        vector_retriever = vector_db.as_retriever(
            search_type="similarity", 
            search_kwargs={"k": Config.RETRIEVAL_K}
        )
        
        bm25_retriever = BM25Retriever.from_documents(documents=documents)
        bm25_retriever.k = Config.RETRIEVAL_K
        
        return EnsembleRetriever(
            retrievers=[bm25_retriever, vector_retriever],
            weights=[0.5, 0.5]
        )
    def save_documents(self, documents: List[Document], save_path: str):
        """Save processed documents to JSON for reuse."""
        
        Path(os.path.dirname(save_path)).mkdir(parents=True, exist_ok=True)
        for doc in documents:
            print("page_content:", doc.page_content[:100])  

        serializable_docs = [
            {
                "page_content": doc.page_content,
                "metadata": doc.metadata
            }
            for doc in documents
        ]

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(serializable_docs, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(documents)} documents to {save_path}")

    def load_documents(self, load_path: str = None) -> List[Document]:
        """Load previously saved documents.
        """

        # Nếu không truyền path → dùng config
        if load_path is None:
            load_path = Config.DOCUMENT_DIRECTORY

        if not os.path.exists(load_path):
            raise FileNotFoundError(f"{load_path} not found.")

        if os.path.getsize(load_path) == 0:
            raise ValueError(f"{load_path} is empty.")

        with open(load_path, "r", encoding="utf-8") as f:
            raw_docs = json.load(f)

        documents = [
            Document(
                page_content=item["page_content"],
                metadata=item["metadata"]
            )
            for item in raw_docs
        ]

        logger.info(f"Loaded {len(documents)} documents from {load_path}")
        return documents
# --- MAIN EXECUTION ---
async def main():
    builder = ContextualRAGBuilder()
    pdf_files = glob(Config.PDF_PATH_PATTERN)
    
    if (os.path.exists(Config.DOCUMENT_DIRECTORY)):
        logger.info("Loading existing contextual documents...")
        all_contextual_docs = builder.load_documents(Config.DOCUMENT_DIRECTORY)
    else:
        all_contextual_docs = []
        for file in pdf_files:
            docs = await builder.process_document(file)
            all_contextual_docs.extend(docs)
        builder.save_documents(all_contextual_docs, Config.DOCUMENT_DIRECTORY)  

    if not all_contextual_docs:
        logger.warning("No documents processed. Check your data folder.")
        return

    # Build DB and Retriever
    vector_db = builder.build_vector_store(all_contextual_docs)
    retriever = builder.create_ensemble_retriever(vector_db, all_contextual_docs)
    
    logger.info("RAG Pipeline is ready.")
    return retriever

if __name__ == "__main__":
    asyncio.run(main())