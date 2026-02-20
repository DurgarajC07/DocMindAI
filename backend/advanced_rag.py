"""Advanced RAG engine with hybrid search, semantic chunking, and optimization."""

import asyncio
import time
from collections import defaultdict
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
from sentence_transformers import SentenceTransformer, CrossEncoder

from backend.config import get_settings

settings = get_settings()


class AdvancedChunkingStrategy:
    """Advanced document chunking with semantic awareness."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def semantic_split(self, text: str) -> list[str]:
        """Split text semantically at natural boundaries."""
        # Split by paragraphs first
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            # If adding this paragraph would exceed chunk size
            if len(current_chunk) + len(para) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    # Add overlap from end of previous chunk
                    overlap_start = max(0, len(current_chunk) - self.chunk_overlap)
                    current_chunk = current_chunk[overlap_start:] + "\n\n" + para
                else:
                    # Single paragraph is too large, split by sentences
                    chunks.extend(self._split_large_paragraph(para))
                    current_chunk = ""
            else:
                current_chunk += "\n\n" + para if current_chunk else para

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _split_large_paragraph(self, paragraph: str) -> list[str]:
        """Split a large paragraph by sentences."""
        import re
        sentences = re.split(r"(?<=[.!?])\s+", paragraph)
        chunks = []
        current_chunk = ""

        for sent in sentences:
            if len(current_chunk) + len(sent) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sent
            else:
                current_chunk += " " + sent if current_chunk else sent

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def hierarchical_split(self, documents: list[Document]) -> list[Document]:
        """Create hierarchical chunks with parent-child relationships."""
        all_chunks = []
        
        for doc in documents:
            # Create parent chunks (large context)
            parent_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size * 3,
                chunk_overlap=self.chunk_overlap,
                separators=["\n\n\n", "\n\n", "\n", ". ", " ", ""],
            )
            parent_chunks = parent_splitter.split_documents([doc])

            # For each parent, create child chunks
            for parent_idx, parent in enumerate(parent_chunks):
                child_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                    separators=["\n\n", "\n", ". ", " ", ""],
                )
                child_chunks = child_splitter.split_documents([parent])

                # Add metadata linking parent-child
                for child_idx, child in enumerate(child_chunks):
                    child.metadata.update({
                        "parent_id": f"{doc.metadata.get('source', 'unknown')}_{parent_idx}",
                        "chunk_type": "child",
                        "parent_content": parent.page_content[:500],  # Store snippet of parent
                    })
                    all_chunks.append(child)

        return all_chunks


class HybridSearch:
    """Hybrid search combining dense embeddings with BM25 sparse retrieval."""

    def __init__(self, vector_store: Chroma):
        self.vector_store = vector_store
        self.bm25_index: dict[str, Any] = {}
        self.doc_frequencies: dict[str, int] = defaultdict(int)
        self.total_docs = 0
        self._build_bm25_index()

    def _build_bm25_index(self):
        """Build BM25 index from vector store documents."""
        try:
            # Get all documents from collection
            collection = self.vector_store._collection
            results = collection.get(include=["documents", "metadatas"])
            
            if not results or not results.get("documents"):
                logger.warning("No documents found for BM25 indexing")
                return

            documents = results["documents"]
            self.total_docs = len(documents)

            # Build inverse document frequency
            for doc_id, text in enumerate(documents):
                if not text:
                    continue
                    
                terms = self._tokenize(text)
                unique_terms = set(terms)
                
                for term in unique_terms:
                    self.doc_frequencies[term] += 1

                self.bm25_index[doc_id] = {
                    "text": text,
                    "terms": terms,
                    "length": len(terms),
                }

            logger.info(f"Built BM25 index with {self.total_docs} documents")

        except Exception as e:
            logger.error(f"Failed to build BM25 index: {e}")

    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenization."""
        import re
        text = text.lower()
        # Remove punctuation and split
        terms = re.findall(r'\b\w+\b', text)
        return terms

    def _bm25_score(self, query_terms: list[str], doc_terms: list[str], doc_length: int) -> float:
        """Calculate BM25 score."""
        k1 = 1.5
        b = 0.75
        avg_doc_length = sum(doc["length"] for doc in self.bm25_index.values()) / max(self.total_docs, 1)

        score = 0.0
        for term in query_terms:
            if term not in doc_terms:
                continue

            # Term frequency in document
            tf = doc_terms.count(term)
            # Document frequency
            df = self.doc_frequencies.get(term, 0)
            
            if df == 0:
                continue

            # IDF calculation
            idf = max(0, (self.total_docs - df + 0.5) / (df + 0.5))

            # BM25 formula
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * (doc_length / avg_doc_length))
            score += idf * (numerator / denominator)

        return score

    def search(self, query: str, k: int = 10, alpha: float = 0.5) -> list[tuple[Document, float]]:
        """
        Hybrid search combining dense and sparse retrieval.
        
        Args:
            query: Search query
            k: Number of results
            alpha: Weight for dense search (1-alpha for BM25). 0.5 = equal weight
        """
        # Dense search (semantic)
        try:
            dense_results = self.vector_store.similarity_search_with_score(query, k=k*2)
            dense_docs = {doc.page_content: (doc, score) for doc, score in dense_results}
        except Exception as e:
            logger.error(f"Dense search failed: {e}")
            dense_docs = {}

        # BM25 search (keyword)
        query_terms = self._tokenize(query)
        bm25_scores = []

        for doc_id, doc_data in self.bm25_index.items():
            score = self._bm25_score(query_terms, doc_data["terms"], doc_data["length"])
            if score > 0:
                bm25_scores.append((doc_id, score, doc_data["text"]))

        # Sort by BM25 score
        bm25_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Normalize scores
        max_dense = max([score for _, score in dense_docs.values()], default=1.0)
        max_bm25 = max([score for _, score, _ in bm25_scores], default=1.0)

        # Combine scores
        combined_scores = {}

        # Add dense results
        for content, (doc, score) in dense_docs.items():
            norm_score = score / max_dense if max_dense > 0 else 0
            combined_scores[content] = {
                "doc": doc,
                "score": alpha * norm_score,
            }

        # Add BM25 results
        for doc_id, score, text in bm25_scores[:k*2]:
            norm_score = score / max_bm25 if max_bm25 > 0 else 0
            if text in combined_scores:
                combined_scores[text]["score"] += (1 - alpha) * norm_score
            else:
                # Create document from text
                doc = Document(page_content=text)
                combined_scores[text] = {
                    "doc": doc,
                    "score": (1 - alpha) * norm_score,
                }

        # Sort by combined score and return top k
        sorted_results = sorted(
            combined_scores.values(),
            key=lambda x: x["score"],
            reverse=True
        )[:k]

        return [(item["doc"], item["score"]) for item in sorted_results]


class QueryExpansion:
    """Expand queries with synonyms and related terms."""

    def __init__(self):
        self.expansion_cache: dict[str, list[str]] = {}

    async def expand_query(self, query: str, llm: Ollama) -> list[str]:
        """Generate query variations for better retrieval."""
        if query in self.expansion_cache:
            return self.expansion_cache[query]

        try:
            prompt = f"""Generate 2-3 alternative phrasings of this question that mean the same thing:

Question: {query}

Alternatives (one per line):"""

            response = llm.invoke(prompt)
            alternatives = [line.strip() for line in response.split("\n") if line.strip()]
            alternatives = [query] + alternatives[:3]  # Include original + max 3 alternatives
            
            self.expansion_cache[query] = alternatives
            return alternatives

        except Exception as e:
            logger.error(f"Query expansion failed: {e}")
            return [query]


class ReRanker:
    """Re-rank retrieved documents using cross-encoder."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        try:
            self.model = CrossEncoder(model_name)
            logger.info(f"Loaded reranker model: {model_name}")
        except Exception as e:
            logger.warning(f"Failed to load reranker, using fallback: {e}")
            self.model = None

    def rerank(self, query: str, documents: list[Document], top_k: int = 5) -> list[Document]:
        """Re-rank documents based on relevance to query."""
        if not self.model or not documents:
            return documents[:top_k]

        try:
            # Prepare pairs
            pairs = [(query, doc.page_content) for doc in documents]
            
            # Get scores
            scores = self.model.predict(pairs)
            
            # Sort by score
            doc_scores = list(zip(documents, scores))
            doc_scores.sort(key=lambda x: x[1], reverse=True)
            
            return [doc for doc, _ in doc_scores[:top_k]]

        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return documents[:top_k]


class ConversationMemory:
    """Manage conversation context and history."""

    def __init__(self, max_history: int = 5):
        self.max_history = max_history
        self.sessions: dict[str, list[dict[str, str]]] = defaultdict(list)

    def add_turn(self, session_id: str, user_msg: str, bot_msg: str):
        """Add a conversation turn."""
        self.sessions[session_id].append({
            "user": user_msg,
            "bot": bot_msg,
        })
        
        # Keep only last N turns
        if len(self.sessions[session_id]) > self.max_history:
            self.sessions[session_id] = self.sessions[session_id][-self.max_history:]

    def get_context(self, session_id: str) -> str:
        """Get conversation context as string."""
        history = self.sessions.get(session_id, [])
        if not history:
            return ""

        context_parts = []
        for turn in history[-3:]:  # Last 3 turns
            context_parts.append(f"User: {turn['user']}")
            context_parts.append(f"Assistant: {turn['bot']}")

        return "\n".join(context_parts)

    def clear_session(self, session_id: str):
        """Clear a session history."""
        if session_id in self.sessions:
            del self.sessions[session_id]


class AdvancedRAGEngine:
    """Production-grade RAG engine with all optimizations."""
    
    # Class-level lock to serialize vector store writes (prevent SQLite concurrent write errors)
    _vector_store_lock = asyncio.Lock()

    def __init__(
        self,
        business_id: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        use_hybrid_search: bool = True,
        use_reranking: bool = True,
    ):
        self.business_id = business_id
        self.collection_name = f"{settings.chroma_collection_prefix}{business_id}"
        
        # Initialize components
        self.chunking_strategy = AdvancedChunkingStrategy(chunk_size, chunk_overlap)
        self.conversation_memory = ConversationMemory()
        self.query_expansion = QueryExpansion()
        
        # Initialize embeddings
        try:
            self.embeddings = self._load_embeddings()
        except Exception as e:
            logger.warning(f"Failed to load on {settings.embedding_device}, falling back to CPU: {e}")
            self.embeddings = self._load_embeddings(device="cpu")
        
        # Initialize Ollama LLM
        self.llm = Ollama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            temperature=0.3,
        )
        
        # Initialize ChromaDB
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
        
        # Initialize search components
        self.use_hybrid_search = use_hybrid_search
        self.hybrid_search = HybridSearch(self.vector_store) if use_hybrid_search else None
        
        self.use_reranking = use_reranking
        self.reranker = ReRanker() if use_reranking else None
        
        # Response cache
        self.response_cache: dict[str, tuple[str, int, int]] = {}
        
        logger.info(f"Advanced RAG engine initialized for business: {business_id}")

    def _load_embeddings(self, device: str = None):
        """Load embedding model."""
        from sentence_transformers import SentenceTransformer
        
        device = device or settings.embedding_device
        model = SentenceTransformer(settings.embedding_model, device=device)
        
        class CustomEmbeddings:
            def __init__(self, model):
                self.model = model

            def embed_documents(self, texts: list[str]) -> list[list[float]]:
                # Sanitize texts: remove None, empty, or whitespace-only strings
                sanitized_texts = []
                for text in texts:
                    if text is None:
                        sanitized_texts.append("")
                        continue
                    # Convert to string if not already
                    text_str = str(text).strip()
                    # Replace empty with placeholder
                    if not text_str:
                        sanitized_texts.append("empty")
                    else:
                        sanitized_texts.append(text_str)
                
                if not sanitized_texts:
                    return []
                
                embeddings = self.model.encode(sanitized_texts, convert_to_numpy=True)
                return embeddings.tolist()

            def embed_query(self, text: str) -> list[float]:
                # Sanitize query text
                text_str = str(text).strip() if text else "empty"
                embedding = self.model.encode(text_str, convert_to_numpy=True)
                return embedding.tolist()

        return CustomEmbeddings(model)

    async def ingest_pdf(self, file_path: Path) -> dict[str, Any]:
        """Ingest PDF with advanced chunking."""
        try:
            loader = PyPDFLoader(str(file_path))
            documents = await asyncio.to_thread(loader.load)
            return await self._process_documents(documents, source=str(file_path))
        except Exception as e:
            logger.error(f"Failed to ingest PDF {file_path}: {e}")
            raise Exception(f"PDF processing failed: {str(e)}")

    async def ingest_text(self, file_path: Path) -> dict[str, Any]:
        """Ingest text file."""
        try:
            loader = TextLoader(str(file_path), encoding="utf-8")
            documents = await asyncio.to_thread(loader.load)
            return await self._process_documents(documents, source=str(file_path))
        except Exception as e:
            logger.error(f"Failed to ingest text file {file_path}: {e}")
            raise Exception(f"Text file processing failed: {str(e)}")

    async def ingest_url(self, url: str) -> dict[str, Any]:
        """Ingest content from URL."""
        try:
            loader = WebBaseLoader(url)
            documents = await asyncio.to_thread(loader.load)
            return await self._process_documents(documents, source=url)
        except Exception as e:
            logger.error(f"Failed to ingest URL {url}: {e}")
            raise Exception(f"URL processing failed: {str(e)}")

    async def _process_documents(
        self,
        documents: list[Document],
        source: str,
    ) -> dict[str, Any]:
        """Process documents with advanced chunking."""
        if not documents:
            raise Exception("No content extracted from document")

        # Use hierarchical chunking
        chunks = self.chunking_strategy.hierarchical_split(documents)
        
        if not chunks:
            raise Exception("Document splitting produced no chunks")

        # Sanitize and validate chunks
        valid_chunks = []
        for i, chunk in enumerate(chunks):
            # Ensure page_content is a valid string
            if chunk.page_content is None:
                continue
            
            content = str(chunk.page_content).strip()
            if not content or len(content) < 3:
                continue
            
            # Update content and metadata
            chunk.page_content = content
            chunk.metadata.update({
                "business_id": self.business_id,
                "source": source,
                "chunk_id": i,
                "total_chunks": len(chunks),
            })
            valid_chunks.append(chunk)
        
        if not valid_chunks:
            raise Exception("No valid chunks after sanitization")
        
        logger.info(f"Sanitized {len(chunks)} chunks down to {len(valid_chunks)} valid chunks")

        # Add to vector store in batches with lock to prevent concurrent write errors
        batch_size = 100
        async with AdvancedRAGEngine._vector_store_lock:
            logger.info(f"🔒 Acquired vector store lock for {source}")
            for i in range(0, len(valid_chunks), batch_size):
                batch = valid_chunks[i:i + batch_size]
                try:
                    await asyncio.to_thread(self.vector_store.add_documents, batch)
                    logger.info(f"✅ Added batch {i//batch_size + 1}/{(len(valid_chunks) + batch_size - 1)//batch_size}")
                except Exception as e:
                    logger.error(f"Failed to add batch {i//batch_size}: {e}")
                    raise
            
            logger.info(f"✅ Added {len(valid_chunks)} chunks from {source} to vector store")

        # Rebuild hybrid search index
        if self.hybrid_search:
            self.hybrid_search._build_bm25_index()

        return {
            "chunks_count": len(valid_chunks),
            "source": source,
            "status": "success",
        }

    async def ask(
        self,
        question: str,
        session_id: str = None,
        use_context: bool = True,
        system_prompt: str = None,
    ) -> tuple[str, int, int]:
        """
        Answer question with all optimizations.
        
        Returns:
            tuple: (answer, response_time_ms, sources_count)
        """
        start_time = time.time()
        
        # Check cache
        cache_key = f"{question}_{session_id}" if session_id else question
        if cache_key in self.response_cache:
            cached = self.response_cache[cache_key]
            logger.info("Returning cached response")
            return cached

        try:
            # Get conversation context
            context_history = ""
            if session_id and use_context:
                context_history = self.conversation_memory.get_context(session_id)

            # Retrieve relevant documents
            if self.use_hybrid_search and self.hybrid_search:
                # Hybrid search
                doc_scores = self.hybrid_search.search(question, k=10)
                docs = [doc for doc, _ in doc_scores]
            else:
                # Standard dense search
                docs = self.vector_store.similarity_search(question, k=10)

            # Re-rank documents
            if self.use_reranking and self.reranker and docs:
                docs = self.reranker.rerank(question, docs, top_k=5)
            else:
                docs = docs[:5]

            # Build context from documents
            context = "\n\n".join([doc.page_content for doc in docs])

            # Build prompt
            default_system_prompt = """You are a helpful, friendly customer support assistant for this business.
Answer the question using ONLY the provided context below.
If the answer is not in the context, politely say "I don't have that information. Please contact us directly."

Be professional, concise, and helpful. Answer in the same language as the question."""

            prompt_template = f"""{system_prompt or default_system_prompt}

{"Previous conversation:" if context_history else ""}
{context_history}

Context:
{context}

Question: {question}

Answer:"""

            # Get answer from LLM
            answer = await asyncio.to_thread(self.llm.invoke, prompt_template)
            
            # Clean up answer
            answer = answer.strip()

            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)

            # Update conversation memory
            if session_id:
                self.conversation_memory.add_turn(session_id, question, answer)

            # Cache response
            result = (answer, response_time_ms, len(docs))
            self.response_cache[cache_key] = result

            logger.info(f"Question answered in {response_time_ms}ms with {len(docs)} sources")
            
            return result

        except Exception as e:
            logger.error(f"Error answering question: {e}")
            response_time_ms = int((time.time() - start_time) * 1000)
            error_message = (
                "I apologize, I'm having trouble right now. "
                "Please try again or contact us directly."
            )
            return error_message, response_time_ms, 0

    def clear_cache(self):
        """Clear response cache."""
        self.response_cache.clear()
        logger.info("Response cache cleared")

    def get_stats(self) -> dict[str, Any]:
        """Get engine statistics."""
        try:
            collection = self.vector_store._collection
            chunk_count = collection.count()
            
            return {
                "business_id": self.business_id,
                "total_chunks": chunk_count,
                "cached_responses": len(self.response_cache),
                "active_sessions": len(self.conversation_memory.sessions),
                "hybrid_search_enabled": self.use_hybrid_search,
                "reranking_enabled": self.use_reranking,
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"error": str(e)}


# Global cache
_advanced_rag_engines: dict[str, AdvancedRAGEngine] = {}


def get_advanced_rag_engine(business_id: str) -> AdvancedRAGEngine:
    """Get or create advanced RAG engine."""
    if business_id not in _advanced_rag_engines:
        _advanced_rag_engines[business_id] = AdvancedRAGEngine(business_id)
    return _advanced_rag_engines[business_id]


def clear_rag_cache():
    """Clear all RAG engines."""
    global _advanced_rag_engines
    _advanced_rag_engines.clear()
    logger.info("Cleared advanced RAG engine cache")
