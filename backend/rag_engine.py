"""RAG (Retrieval-Augmented Generation) engine for document processing and chat."""

import time
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, TextLoader, WebBaseLoader
from langchain_community.llms import Ollama
from langchain_core.documents import Document
from loguru import logger
from sentence_transformers import SentenceTransformer

from backend.config import get_settings

settings = get_settings()


class CustomEmbeddings:
    """Custom embeddings using sentence-transformers."""

    def __init__(self, model_name: str, device: str = "cuda"):
        """Initialize the embedding model."""
        self.model = SentenceTransformer(model_name, device=device)
        logger.info(f"Loaded embedding model: {model_name} on {device}")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents."""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()


class RAGEngine:
    """RAG engine for document ingestion and question answering."""

    def __init__(self, business_id: str):
        """Initialize the RAG engine for a specific business."""
        self.business_id = business_id
        self.collection_name = f"{settings.chroma_collection_prefix}{business_id}"
        
        # Initialize embeddings
        try:
            self.embeddings = CustomEmbeddings(
                model_name=settings.embedding_model,
                device=settings.embedding_device,
            )
        except Exception as e:
            logger.warning(f"Failed to load on {settings.embedding_device}, falling back to CPU: {e}")
            self.embeddings = CustomEmbeddings(
                model_name=settings.embedding_model,
                device="cpu",
            )
        
        # Initialize Ollama LLM
        self.llm = Ollama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            temperature=0.3,
        )
        
        # Initialize ChromaDB client
        chroma_client = chromadb.PersistentClient(
            path=str(settings.chroma_persist_dir),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )
        
        # Initialize vector store
        self.vector_store = Chroma(
            client=chroma_client,
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
        )
        
        logger.info(f"RAG engine initialized for business: {business_id}")

    async def ingest_pdf(self, file_path: Path) -> dict[str, Any]:
        """Ingest a PDF document."""
        try:
            loader = PyPDFLoader(str(file_path))
            documents = loader.load()
            return await self._process_documents(documents, source=str(file_path))
        except Exception as e:
            logger.error(f"Failed to ingest PDF {file_path}: {e}")
            raise Exception(f"PDF processing failed: {str(e)}")

    async def ingest_text(self, file_path: Path) -> dict[str, Any]:
        """Ingest a text document."""
        try:
            loader = TextLoader(str(file_path), encoding="utf-8")
            documents = loader.load()
            return await self._process_documents(documents, source=str(file_path))
        except Exception as e:
            logger.error(f"Failed to ingest text file {file_path}: {e}")
            raise Exception(f"Text file processing failed: {str(e)}")

    async def ingest_url(self, url: str) -> dict[str, Any]:
        """Ingest content from a URL."""
        try:
            loader = WebBaseLoader(url)
            documents = loader.load()
            return await self._process_documents(documents, source=url)
        except Exception as e:
            logger.error(f"Failed to ingest URL {url}: {e}")
            raise Exception(f"URL processing failed: {str(e)}")

    async def _process_documents(
        self, documents: list[Document], source: str
    ) -> dict[str, Any]:
        """Process and store documents in vector database."""
        if not documents:
            raise Exception("No content extracted from document")

        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )
        chunks = text_splitter.split_documents(documents)
        
        if not chunks:
            raise Exception("Document splitting produced no chunks")

        # Add metadata
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                "business_id": self.business_id,
                "source": source,
                "chunk_id": i,
            })

        # Add to vector store
        try:
            self.vector_store.add_documents(chunks)
            logger.info(f"Added {len(chunks)} chunks from {source} to vector store")
        except Exception as e:
            logger.error(f"Failed to add documents to vector store: {e}")
            raise Exception(f"Vector store update failed: {str(e)}")

        return {
            "chunks_count": len(chunks),
            "source": source,
            "status": "success",
        }

    async def ask(self, question: str, language: str = "auto") -> tuple[str, int, int]:
        """Answer a question using the RAG pipeline.
        
        Returns:
            tuple: (answer, response_time_ms, sources_count)
        """
        start_time = time.time()
        
        # Create prompt template
        prompt_template = PromptTemplate(
            template="""You are a helpful customer support assistant for this business.
Answer the question ONLY using the provided context below.
If the answer is not in the context, politely say "I don't have that information in my knowledge base. Please contact us directly for assistance."

Be friendly, concise, and professional.
Answer in the same language as the question.

Context:
{context}

Question: {question}

Helpful Answer:""",
            input_variables=["context", "question"],
        )

        try:
            # Create retrieval chain
            retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 4},
            )
            
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=retriever,
                chain_type_kwargs={"prompt": prompt_template},
                return_source_documents=True,
            )

            # Get answer
            result = qa_chain.invoke({"query": question})
            answer = result["result"]
            sources = result.get("source_documents", [])
            
            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)
            
            logger.info(
                f"Question answered in {response_time_ms}ms with {len(sources)} sources"
            )
            
            return answer, response_time_ms, len(sources)

        except Exception as e:
            logger.error(f"Error answering question: {e}")
            response_time_ms = int((time.time() - start_time) * 1000)
            error_message = (
                "I apologize, but I'm having trouble processing your question right now. "
                "Please try again in a moment or contact us directly."
            )
            return error_message, response_time_ms, 0

    def get_collection_stats(self) -> dict[str, Any]:
        """Get statistics about the vector store collection."""
        try:
            collection = self.vector_store._collection
            count = collection.count()
            return {
                "business_id": self.business_id,
                "total_chunks": count,
                "collection_name": self.collection_name,
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {
                "business_id": self.business_id,
                "total_chunks": 0,
                "collection_name": self.collection_name,
                "error": str(e),
            }

    async def delete_collection(self) -> bool:
        """Delete the entire vector store collection for this business."""
        try:
            self.vector_store.delete_collection()
            logger.info(f"Deleted collection for business: {self.business_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            return False


# Global cache for RAG engines
_rag_engines: dict[str, RAGEngine] = {}


def get_rag_engine(business_id: str) -> RAGEngine:
    """Get or create a RAG engine for a business."""
    if business_id not in _rag_engines:
        _rag_engines[business_id] = RAGEngine(business_id)
    return _rag_engines[business_id]


def clear_rag_cache() -> None:
    """Clear the RAG engine cache."""
    global _rag_engines
    _rag_engines.clear()
    logger.info("Cleared RAG engine cache")
