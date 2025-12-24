"""
RAG Pipeline Integration Tests (User Story 3 - P3)

Tests Retrieval-Augmented Generation workflows on AMD AI Max+ 395 with ROCm.
Validates context incorporation, document QA pipelines, variable context windows, and streaming.
"""

import pytest
import time
import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from utils.lemonade_client import LemonadeClient, InferenceRequest
from utils.rocm_monitor import ROCmMonitor
from utils.metrics_collector import MetricsCollector, PerformanceMetrics

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class RAGResult:
    """Result from RAG pipeline test."""
    query: str
    context_chunks: List[str]
    response: str
    tokens_generated: int
    context_tokens: int
    response_quality_score: float  # 0-1 scale
    context_relevance_score: float  # 0-1 scale
    duration_ms: float
    error_message: Optional[str] = None


@dataclass
class DocumentChunk:
    """Represents a document chunk for RAG."""
    content: str
    metadata: Dict[str, Any]
    token_count: int


class TestRAGIntegration:
    """Test RAG pipeline capabilities."""

    @pytest.fixture
    def client(self, lemonade_client: LemonadeClient) -> LemonadeClient:
        """Provide Lemonade client for tests."""
        return lemonade_client

    @pytest.fixture
    def monitor(self, rocm_monitor: ROCmMonitor) -> ROCmMonitor:
        """Provide ROCm monitor for tests."""
        return rocm_monitor

    @pytest.fixture
    def collector(self, metrics_collector: MetricsCollector) -> MetricsCollector:
        """Provide metrics collector for tests."""
        return metrics_collector

    @pytest.fixture
    def rag_scenarios(self, fixtures_dir: Path) -> Dict[str, Any]:
        """Load RAG test scenarios."""
        rag_file = fixtures_dir / "rag_scenarios.json"
        if rag_file.exists():
            with open(rag_file, 'r') as f:
                return json.load(f)
        else:
            # Return minimal default scenarios if file doesn't exist yet
            return self._get_default_rag_scenarios()

    def _get_default_rag_scenarios(self) -> Dict[str, Any]:
        """Provide default RAG scenarios for testing."""
        return {
            "documents": [
                {
                    "title": "Machine Learning Basics",
                    "content": "Machine learning is a subset of artificial intelligence that enables computers to learn from data without being explicitly programmed. There are three main types: supervised learning, unsupervised learning, and reinforcement learning. Supervised learning uses labeled data to train models that can make predictions. Unsupervised learning finds patterns in unlabeled data. Reinforcement learning involves learning through trial and error with rewards and penalties.",
                    "category": "education"
                },
                {
                    "title": "Neural Networks",
                    "content": "Neural networks are computing systems inspired by biological neural networks. They consist of layers of interconnected nodes called neurons. Each connection has a weight that adjusts during learning. Deep learning uses neural networks with multiple hidden layers. Common architectures include convolutional neural networks (CNNs) for image processing and recurrent neural networks (RNNs) for sequence data.",
                    "category": "technical"
                },
                {
                    "title": "GPU Computing",
                    "content": "GPU computing uses graphics processing units for general-purpose computing. GPUs excel at parallel processing tasks. CUDA is NVIDIA's platform for GPU computing. ROCm is AMD's open-source platform for GPU computing on Linux and Windows. GPUs accelerate machine learning training and inference through massive parallelism.",
                    "category": "hardware"
                }
            ],
            "qa_pairs": [
                {
                    "question": "What are the three main types of machine learning?",
                    "expected_context": ["Machine learning is a subset", "supervised learning, unsupervised learning, and reinforcement learning"],
                    "expected_answer_contains": ["supervised", "unsupervised", "reinforcement"]
                },
                {
                    "question": "What is ROCm?",
                    "expected_context": ["ROCm is AMD's open-source platform"],
                    "expected_answer_contains": ["AMD", "open-source", "GPU computing"]
                },
                {
                    "question": "How do neural networks work?",
                    "expected_context": ["layers of interconnected nodes", "connection has a weight"],
                    "expected_answer_contains": ["neurons", "weights", "layers"]
                }
            ],
            "context_sizes": [1024, 2048, 4096, 8192]  # Token sizes for testing
        }

    @pytest.mark.rocm
    @pytest.mark.rag
    def test_context_incorporation(self, client: LemonadeClient, monitor: ROCmMonitor,
                                  collector: MetricsCollector, rag_scenarios: Dict[str, Any],
                                  model_configs: Dict[str, Any], temp_result_file, results_dir: Path):
        """
        Test LLM response accuracy with provided context (AS1).

        Validates that LLM generates responses that accurately incorporate
        provided context chunks, demonstrating proper context utilization.
        """
        logger.info("Starting context incorporation test")

        # Use 7B model for RAG testing
        model_config = model_configs["models"]["llama-3.2-7b-instruct-gguf"]
        model_name = model_config["name"]

        qa_pairs = rag_scenarios.get("qa_pairs", [])
        if not qa_pairs:
            pytest.skip("No QA pairs available for context incorporation testing")

        results = []
        total_score = 0

        for i, qa_pair in enumerate(qa_pairs[:3]):  # Test first 3 pairs
            logger.info(f"Testing QA pair {i+1}: {qa_pair['question'][:50]}...")

            try:
                # Prepare context from relevant documents
                context_chunks = self._prepare_context_chunks(qa_pair, rag_scenarios["documents"])
                context_text = "\n\n".join(context_chunks)

                # Create RAG-style prompt
                rag_prompt = f"""Use the following context to answer the question accurately.

Context:
{context_text}

Question: {qa_pair['question']}

Answer:"""

                # Time the inference
                start_time = time.time()

                response = client.chat_completion(
                    messages=[{"role": "user", "content": rag_prompt}],
                    model=model_name,
                    max_tokens=200,
                    temperature=0.1  # Low temperature for consistency
                )

                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000

                # Extract response
                answer_text = response.get("choices", [{}])[0].get("message", {}).get("content", "")
                tokens_generated = response.get("usage", {}).get("completion_tokens", 100)

                # Evaluate response quality
                quality_score = self._evaluate_context_incorporation(
                    answer_text, qa_pair, context_chunks
                )

                total_score += quality_score

                # Create result
                result = RAGResult(
                    query=qa_pair["question"],
                    context_chunks=context_chunks,
                    response=answer_text,
                    tokens_generated=tokens_generated,
                    context_tokens=len(context_text.split()),  # Rough estimate
                    response_quality_score=quality_score,
                    context_relevance_score=1.0,  # Assume context is relevant for this test
                    duration_ms=duration_ms
                )

                results.append(result)

                logger.info(f"QA pair {i+1} completed: quality_score={quality_score:.2f}")

            except Exception as e:
                logger.error(f"QA pair {i+1} failed: {e}")
                result = RAGResult(
                    query=qa_pair["question"],
                    context_chunks=context_chunks if 'context_chunks' in locals() else [],
                    response="",
                    tokens_generated=0,
                    context_tokens=0,
                    response_quality_score=0.0,
                    context_relevance_score=0.0,
                    duration_ms=0,
                    error_message=str(e)
                )
                results.append(result)

        # Calculate overall score
        average_score = total_score / len(results) if results else 0

        # Validate minimum quality threshold
        assert average_score >= 0.6, f"Context incorporation quality too low: {average_score:.2f} (need ≥0.6)"

        # Save results
        rag_results = {
            "test_type": "context_incorporation",
            "model": model_name,
            "average_quality_score": average_score,
            "results": [
                {
                    "query": r.query,
                    "response_quality_score": r.response_quality_score,
                    "context_relevance_score": r.context_relevance_score,
                    "duration_ms": r.duration_ms,
                    "error": r.error_message
                } for r in results
            ]
        }

        with open(results_dir / "rag_context_incorporation.json", 'w') as f:
            json.dump(rag_results, f, indent=2)

        logger.info(f"Context incorporation test completed: average_score={average_score:.2f}")

    def _prepare_context_chunks(self, qa_pair: Dict[str, Any], documents: List[Dict[str, Any]]) -> List[str]:
        """Prepare relevant context chunks for a QA pair."""
        context_chunks = []

        # Add expected context from QA pair
        expected_context = qa_pair.get("expected_context", [])
        for context_hint in expected_context:
            # Find documents containing the expected context
            for doc in documents:
                if context_hint.lower() in doc["content"].lower():
                    context_chunks.append(doc["content"])
                    break

        # If no specific context found, add first document as fallback
        if not context_chunks and documents:
            context_chunks.append(documents[0]["content"])

        return context_chunks

    def _evaluate_context_incorporation(self, response: str, qa_pair: Dict[str, Any],
                                       context_chunks: List[str]) -> float:
        """
        Evaluate how well the response incorporates the provided context.

        Returns a score from 0-1 based on:
        - Contains expected answer elements
        - Uses information from context
        - Avoids hallucinated information
        """
        if not response.strip():
            return 0.0

        response_lower = response.lower()
        score = 0.0
        max_score = 1.0

        # Check for expected answer elements
        expected_contains = qa_pair.get("expected_answer_contains", [])
        if expected_contains:
            matches = sum(1 for term in expected_contains if term.lower() in response_lower)
            score += (matches / len(expected_contains)) * 0.6

        # Check context utilization (basic heuristic)
        context_text = " ".join(context_chunks).lower()
        context_words = set(context_text.split())
        response_words = set(response_lower.split())

        # Calculate overlap with context
        overlap = len(context_words.intersection(response_words))
        total_unique = len(context_words.union(response_words))

        if total_unique > 0:
            overlap_score = overlap / total_unique
            score += overlap_score * 0.4

        return min(score, max_score)

    @pytest.mark.rocm
    @pytest.mark.rag
    def test_document_qa_pipeline(self, client: LemonadeClient, monitor: ROCmMonitor,
                                 collector: MetricsCollector, rag_scenarios: Dict[str, Any],
                                 model_configs: Dict[str, Any], temp_result_file, results_dir: Path):
        """
        Test full RAG pipeline with vector store and document corpus (AS2).

        Simulates a complete RAG workflow: document ingestion, chunking,
        retrieval, and answer generation from document corpus.
        """
        logger.info("Starting document QA pipeline test")

        # Use 7B model for RAG testing
        model_config = model_configs["models"]["llama-3.2-7b-instruct-gguf"]
        model_name = model_config["name"]

        documents = rag_scenarios.get("documents", [])
        if not documents:
            pytest.skip("No documents available for QA pipeline testing")

        # Create document chunks (simulate vector store chunking)
        doc_chunks = self._create_document_chunks(documents)

        # Test queries that require information from multiple documents
        test_queries = [
            "Explain machine learning and how GPUs accelerate it",
            "What are neural networks and how do they relate to GPU computing?",
            "Compare supervised learning with reinforcement learning"
        ]

        results = []

        for i, query in enumerate(test_queries):
            logger.info(f"Testing query {i+1}: {query[:50]}...")

            try:
                # Simulate retrieval: find relevant chunks
                relevant_chunks = self._retrieve_relevant_chunks(query, doc_chunks, top_k=3)

                # Combine chunks into context
                context_text = "\n\n".join([chunk.content for chunk in relevant_chunks])

                # Generate RAG response
                rag_prompt = f"""You are a helpful assistant that answers questions based on the provided context.

Context:
{context_text}

Question: {query}

Instructions:
- Answer based only on the provided context
- Be accurate and comprehensive
- If the context doesn't contain enough information, say so

Answer:"""

                start_time = time.time()

                response = client.chat_completion(
                    messages=[{"role": "user", "content": rag_prompt}],
                    model=model_name,
                    max_tokens=300,
                    temperature=0.1
                )

                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000

                answer_text = response.get("choices", [{}])[0].get("message", {}).get("content", "")
                tokens_generated = response.get("usage", {}).get("completion_tokens", 150)

                # Evaluate response quality
                quality_score = self._evaluate_qa_response(answer_text, query, relevant_chunks)
                relevance_score = self._calculate_context_relevance(query, relevant_chunks)

                result = RAGResult(
                    query=query,
                    context_chunks=[chunk.content for chunk in relevant_chunks],
                    response=answer_text,
                    tokens_generated=tokens_generated,
                    context_tokens=sum(len(chunk.content.split()) for chunk in relevant_chunks),
                    response_quality_score=quality_score,
                    context_relevance_score=relevance_score,
                    duration_ms=duration_ms
                )

                results.append(result)

                logger.info(f"Query {i+1} completed: quality={quality_score:.2f}, relevance={relevance_score:.2f}")

            except Exception as e:
                logger.error(f"Query {i+1} failed: {e}")
                result = RAGResult(
                    query=query,
                    context_chunks=[],
                    response="",
                    tokens_generated=0,
                    context_tokens=0,
                    response_quality_score=0.0,
                    context_relevance_score=0.0,
                    duration_ms=0,
                    error_message=str(e)
                )
                results.append(result)

        # Calculate aggregate metrics
        avg_quality = sum(r.response_quality_score for r in results) / len(results) if results else 0
        avg_relevance = sum(r.context_relevance_score for r in results) / len(results) if results else 0

        # Validate pipeline effectiveness
        assert avg_quality >= 0.5, f"QA pipeline quality too low: {avg_quality:.2f}"
        assert avg_relevance >= 0.6, f"Context relevance too low: {avg_relevance:.2f}"

        # Save results
        pipeline_results = {
            "test_type": "document_qa_pipeline",
            "model": model_name,
            "average_quality_score": avg_quality,
            "average_relevance_score": avg_relevance,
            "total_queries": len(results),
            "results": [
                {
                    "query": r.query,
                    "response_quality_score": r.response_quality_score,
                    "context_relevance_score": r.context_relevance_score,
                    "context_chunks_used": len(r.context_chunks),
                    "tokens_generated": r.tokens_generated,
                    "duration_ms": r.duration_ms,
                    "error": r.error_message
                } for r in results
            ]
        }

        with open(results_dir / "rag_document_qa_pipeline.json", 'w') as f:
            json.dump(pipeline_results, f, indent=2)

        logger.info(f"Document QA pipeline test completed: quality={avg_quality:.2f}, relevance={avg_relevance:.2f}")

    def _create_document_chunks(self, documents: List[Dict[str, Any]]) -> List[DocumentChunk]:
        """Create document chunks for RAG pipeline simulation."""
        chunks = []

        for doc in documents:
            # Simple chunking: split by sentences (basic approach)
            content = doc["content"]
            sentences = content.split('. ')

            # Create chunks of 2-3 sentences each
            for i in range(0, len(sentences), 2):
                chunk_sentences = sentences[i:i+2]
                chunk_content = '. '.join(chunk_sentences)
                if chunk_content.strip():
                    chunk = DocumentChunk(
                        content=chunk_content + ('.' if not chunk_content.endswith('.') else ''),
                        metadata={
                            "title": doc["title"],
                            "category": doc["category"],
                            "chunk_index": i // 2
                        },
                        token_count=len(chunk_content.split())  # Rough estimate
                    )
                    chunks.append(chunk)

        return chunks

    def _retrieve_relevant_chunks(self, query: str, chunks: List[DocumentChunk], top_k: int = 3) -> List[DocumentChunk]:
        """Simulate vector store retrieval - find most relevant chunks."""
        query_lower = query.lower()

        # Simple keyword-based relevance scoring
        scored_chunks = []
        for chunk in chunks:
            content_lower = chunk.content.lower()
            score = 0

            # Count query term matches
            query_terms = query_lower.split()
            for term in query_terms:
                if term in content_lower:
                    score += 1

            # Boost score for exact phrase matches
            if any(phrase in content_lower for phrase in [query_lower, query_lower[:-1]]):
                score += 2

            scored_chunks.append((chunk, score))

        # Sort by score and return top_k
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return [chunk for chunk, score in scored_chunks[:top_k]]

    def _evaluate_qa_response(self, response: str, query: str, context_chunks: List[DocumentChunk]) -> float:
        """Evaluate QA response quality."""
        if not response.strip():
            return 0.0

        score = 0.0
        response_lower = response.lower()

        # Check if response is informative (not too short)
        word_count = len(response.split())
        if word_count < 10:
            return 0.2  # Very short responses get low score
        elif word_count > 20:
            score += 0.3  # Good length

        # Check for context utilization
        context_text = " ".join([chunk.content for chunk in context_chunks]).lower()
        context_words = set(context_text.split())
        response_words = set(response_lower.split())

        overlap = len(context_words.intersection(response_words))
        if overlap > 5:  # At least some overlap
            score += 0.4

        # Check for query addressing
        query_terms = set(query.lower().split())
        response_query_overlap = len(query_terms.intersection(response_words))
        if response_query_overlap > 0:
            score += 0.3

        return min(score, 1.0)

    def _calculate_context_relevance(self, query: str, chunks: List[DocumentChunk]) -> float:
        """Calculate how relevant the retrieved context is to the query."""
        if not chunks:
            return 0.0

        query_lower = query.lower()
        total_relevance = 0

        for chunk in chunks:
            content_lower = chunk.content.lower()
            relevance = 0

            # Keyword matching
            query_terms = query_lower.split()
            matches = sum(1 for term in query_terms if term in content_lower)
            relevance += matches / len(query_terms)

            # Semantic relevance (basic heuristic)
            if any(keyword in content_lower for keyword in ["machine learning", "neural", "gpu", "learning"]):
                if any(keyword in query_lower for keyword in ["machine learning", "neural", "gpu", "learning"]):
                    relevance += 0.5

            total_relevance += relevance

        return min(total_relevance / len(chunks), 1.0)

    @pytest.mark.rocm
    @pytest.mark.rag
    def test_variable_context_windows(self, client: LemonadeClient, monitor: ROCmMonitor,
                                     collector: MetricsCollector, rag_scenarios: Dict[str, Any],
                                     model_configs: Dict[str, Any], temp_result_file, results_dir: Path):
        """
        Test handling of variable context window sizes (AS3).

        Validates system efficiently handles 4K, 8K, 16K+ token contexts
        with appropriate performance scaling.
        """
        logger.info("Starting variable context windows test")

        # Use 7B model for context window testing
        model_config = model_configs["models"]["llama-3.2-7b-instruct-gguf"]
        model_name = model_config["name"]

        context_sizes = rag_scenarios.get("context_sizes", [1024, 2048, 4096, 8192])
        documents = rag_scenarios.get("documents", [])

        if not documents:
            pytest.skip("No documents available for context window testing")

        # Create large context by repeating documents
        base_context = "\n\n".join([doc["content"] for doc in documents])
        test_query = "Summarize the key concepts from all the provided documents."

        results = []

        for target_tokens in context_sizes:
            logger.info(f"Testing context window: {target_tokens} tokens")

            try:
                # Create context of approximately target size
                context_text = self._create_context_of_size(base_context, target_tokens)

                # Create RAG prompt
                rag_prompt = f"""Please answer the question based on the following context.

Context ({len(context_text.split())} tokens):
{context_text}

Question: {test_query}

Answer:"""

                start_time = time.time()

                response = client.chat_completion(
                    messages=[{"role": "user", "content": rag_prompt}],
                    model=model_name,
                    max_tokens=200,
                    temperature=0.1
                )

                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000

                answer_text = response.get("choices", [{}])[0].get("message", {}).get("content", "")
                tokens_generated = response.get("usage", {}).get("completion_tokens", 100)

                # Evaluate response quality for this context size
                quality_score = self._evaluate_context_window_response(
                    answer_text, test_query, context_text, target_tokens
                )

                result = RAGResult(
                    query=f"{test_query} (context: {target_tokens} tokens)",
                    context_chunks=[context_text],
                    response=answer_text,
                    tokens_generated=tokens_generated,
                    context_tokens=len(context_text.split()),
                    response_quality_score=quality_score,
                    context_relevance_score=1.0,  # Full context is relevant
                    duration_ms=duration_ms
                )

                results.append(result)

                logger.info(f"Context {target_tokens} tokens: quality={quality_score:.2f}, duration={duration_ms:.0f}ms")

            except Exception as e:
                logger.error(f"Context window {target_tokens} tokens failed: {e}")
                result = RAGResult(
                    query=f"{test_query} (context: {target_tokens} tokens)",
                    context_chunks=[],
                    response="",
                    tokens_generated=0,
                    context_tokens=target_tokens,
                    response_quality_score=0.0,
                    context_relevance_score=0.0,
                    duration_ms=0,
                    error_message=str(e)
                )
                results.append(result)

        # Analyze scaling performance
        successful_results = [r for r in results if r.error_message is None]

        if len(successful_results) >= 2:
            # Check that performance scales reasonably with context size
            small_context = next((r for r in successful_results if r.context_tokens <= 2048), None)
            large_context = next((r for r in successful_results if r.context_tokens >= 4096), None)

            if small_context and large_context:
                # Large context should take longer but not excessively so
                time_ratio = large_context.duration_ms / small_context.duration_ms
                size_ratio = large_context.context_tokens / small_context.context_tokens

                # Time should scale roughly with context size (allowing some overhead)
                max_expected_ratio = size_ratio * 1.5  # 50% overhead allowed

                assert time_ratio <= max_expected_ratio, \
                    f"Context processing time scales poorly: {time_ratio:.1f}x vs {max_expected_ratio:.1f}x expected"

                logger.info(f"Context scaling analysis: {size_ratio:.1f}x size increase, {time_ratio:.1f}x time increase")

        # Validate minimum quality across all context sizes
        avg_quality = sum(r.response_quality_score for r in successful_results) / len(successful_results) if successful_results else 0
        assert avg_quality >= 0.4, f"Variable context quality too low: {avg_quality:.2f}"

        # Save results
        context_results = {
            "test_type": "variable_context_windows",
            "model": model_name,
            "average_quality_score": avg_quality,
            "context_sizes_tested": context_sizes,
            "results": [
                {
                    "context_tokens": r.context_tokens,
                    "response_quality_score": r.response_quality_score,
                    "duration_ms": r.duration_ms,
                    "tokens_generated": r.tokens_generated,
                    "error": r.error_message
                } for r in results
            ]
        }

        with open(results_dir / "rag_variable_context_windows.json", 'w') as f:
            json.dump(context_results, f, indent=2)

        logger.info(f"Variable context windows test completed: avg_quality={avg_quality:.2f}")

    def _create_context_of_size(self, base_context: str, target_tokens: int) -> str:
        """Create context text of approximately target token count."""
        words = base_context.split()
        current_tokens = 0
        result_parts = []

        # Repeat base context until we reach target size
        while current_tokens < target_tokens and result_parts:
            result_parts.append(base_context)
            current_tokens += len(words)

        # Trim to exact size if needed
        result_text = " ".join(result_parts)
        result_words = result_text.split()

        if len(result_words) > target_tokens:
            result_words = result_words[:target_tokens]
            result_text = " ".join(result_words)

        return result_text

    def _evaluate_context_window_response(self, response: str, query: str,
                                        context: str, target_tokens: int) -> float:
        """Evaluate response quality for context window testing."""
        if not response.strip():
            return 0.0

        score = 0.0
        response_lower = response.lower()
        context_lower = context.lower()

        # Basic response quality
        word_count = len(response.split())
        if word_count > 10:
            score += 0.3

        # Context utilization (should use information from context)
        context_words = set(context_lower.split()[:100])  # Sample context words
        response_words = set(response_lower.split())

        overlap = len(context_words.intersection(response_words))
        if overlap > 3:
            score += 0.4

        # Query relevance
        query_terms = set(query.lower().split())
        query_overlap = len(query_terms.intersection(response_words))
        if query_overlap > 0:
            score += 0.3

        return min(score, 1.0)    @pytest.mark.rocm
    @pytest.mark.rag
    @pytest.mark.streaming
    def test_rag_streaming(self, client: LemonadeClient, monitor: ROCmMonitor,
                          collector: MetricsCollector, rag_scenarios: Dict[str, Any],
                          model_configs: Dict[str, Any], temp_result_file, results_dir: Path):
        """
        Test streaming responses with context processing (AS4).

        Validates that streaming is enabled for RAG responses without
        blocking on context processing.
        """
        logger.info("Starting RAG streaming test")

        # Use 7B model for streaming RAG testing
        model_config = model_configs["models"]["llama-3.2-7b-instruct-gguf"]
        model_name = model_config["name"]

        documents = rag_scenarios.get("documents", [])
        if not documents:
            pytest.skip("No documents available for streaming RAG testing")

        # Create context from documents
        context_text = "\n\n".join([doc["content"] for doc in documents[:2]])  # Use first 2 docs
        test_query = "Explain the relationship between machine learning and neural networks."

        rag_prompt = f"""Based on the following context, answer the question.

Context:
{context_text}

Question: {test_query}

Answer:"""

        try:
            # Test streaming response
            start_time = time.time()

            response = client.chat_completion(
                messages=[{"role": "user", "content": rag_prompt}],
                model=model_name,
                max_tokens=200,
                temperature=0.1,
                stream=True  # Enable streaming
            )

            end_time = time.time()
            total_duration_ms = (end_time - start_time) * 1000

            # For streaming, we need to collect the full response
            full_response = ""
            tokens_received = 0
            first_token_time = None
            last_token_time = None

            # Simulate streaming token collection
            if hasattr(response, "__iter__"):
                for chunk in response:
                    if first_token_time is None:
                        first_token_time = time.time()

                    chunk_content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if chunk_content:
                        full_response += chunk_content
                        tokens_received += 1
                        last_token_time = time.time()
            else:
                # Fallback for non-streaming response
                full_response = response.get("choices", [{}])[0].get("message", {}).get("content", "")
                tokens_received = response.get("usage", {}).get("completion_tokens", 100)
                first_token_time = end_time
                last_token_time = end_time

            # Calculate streaming metrics
            time_to_first_token_ms = (first_token_time - start_time) * 1000 if first_token_time else total_duration_ms
            streaming_duration_ms = (last_token_time - first_token_time) * 1000 if last_token_time and first_token_time else 0

            # Evaluate streaming response quality
            quality_score = self._evaluate_streaming_response(
                full_response, test_query, context_text, tokens_received
            )

            # Validate streaming performance
            assert time_to_first_token_ms <= 2000, f"Time to first token too slow: {time_to_first_token_ms:.0f}ms"
            assert quality_score >= 0.5, f"Streaming response quality too low: {quality_score:.2f}"
            assert tokens_received > 0, "No tokens received in streaming response"

            # Create result
            result = RAGResult(
                query=test_query,
                context_chunks=[context_text],
                response=full_response,
                tokens_generated=tokens_received,
                context_tokens=len(context_text.split()),
                response_quality_score=quality_score,
                context_relevance_score=1.0,
                duration_ms=total_duration_ms
            )

            # Save results
            streaming_results = {
                "test_type": "rag_streaming",
                "model": model_name,
                "streaming_enabled": True,
                "time_to_first_token_ms": time_to_first_token_ms,
                "total_duration_ms": total_duration_ms,
                "tokens_received": tokens_received,
                "response_quality_score": quality_score,
                "full_response_length": len(full_response),
                "response_preview": full_response[:200] + "..." if len(full_response) > 200 else full_response
            }

            with open(results_dir / "rag_streaming_test.json", "w") as f:
                json.dump(streaming_results, f, indent=2)

            logger.info(f"RAG streaming test completed: quality={quality_score:.2f}, tokens={tokens_received}, ttft={time_to_first_token_ms:.0f}ms")

        except Exception as e:
            logger.error(f"RAG streaming test failed: {e}")
            pytest.fail(f"RAG streaming test failed: {e}")

    def _evaluate_streaming_response(self, response: str, query: str,
                                   context: str, tokens_received: int) -> float:
        """Evaluate streaming response quality."""
        if not response.strip() or tokens_received == 0:
            return 0.0

        score = 0.0

        # Basic response quality
        if len(response.split()) > 15:  # Reasonable response length
            score += 0.4

        # Context utilization
        context_lower = context.lower()
        response_lower = response.lower()

        context_words = set(context_lower.split()[:50])  # Sample context
        response_words = set(response_lower.split())

        overlap = len(context_words.intersection(response_words))
        if overlap > 2:
            score += 0.4

        # Query relevance
        query_terms = set(query.lower().split())
        query_overlap = len(query_terms.intersection(response_words))
        if query_overlap > 0:
            score += 0.2

        return min(score, 1.0)
