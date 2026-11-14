"""Unit tests for evaluation module."""
import pytest
from src.evaluation.metrics import RAGEvaluator


class TestRAGEvaluator:
    """Test cases for RAGEvaluator class."""

    @pytest.fixture
    def evaluator(self):
        """Create an evaluator instance."""
        return RAGEvaluator()

    def test_initialization(self, evaluator):
        """Test evaluator initialization."""
        assert evaluator is not None
        assert evaluator.metrics is not None

    def test_measure_latency(self, evaluator):
        """Test latency measurement."""
        def sample_function(x, y):
            return x + y

        result, latency = evaluator.measure_latency(sample_function, 2, 3)

        assert result == 5
        assert latency >= 0
        assert len(evaluator.metrics["latency"]) == 1

    def test_calculate_recall_at_k(self, evaluator):
        """Test Recall@K calculation."""
        retrieved = ["doc1", "doc2", "doc3", "doc4"]
        relevant = ["doc2", "doc3", "doc5"]

        recall = evaluator.calculate_recall_at_k(retrieved, relevant, k=3)

        # Should find 2 out of 3 relevant docs in top 3
        assert recall == pytest.approx(2/3, 0.01)

    def test_calculate_recall_perfect(self, evaluator):
        """Test perfect recall."""
        retrieved = ["doc1", "doc2", "doc3"]
        relevant = ["doc1", "doc2"]

        recall = evaluator.calculate_recall_at_k(retrieved, relevant, k=3)
        assert recall == 1.0

    def test_calculate_precision_at_k(self, evaluator):
        """Test Precision@K calculation."""
        retrieved = ["doc1", "doc2", "doc3", "doc4"]
        relevant = ["doc2", "doc3", "doc5"]

        precision = evaluator.calculate_precision_at_k(retrieved, relevant, k=3)

        # Should find 2 out of 3 retrieved docs are relevant
        assert precision == pytest.approx(2/3, 0.01)

    def test_calculate_mrr(self, evaluator):
        """Test MRR calculation."""
        retrieved = ["doc1", "doc2", "doc3"]
        relevant = ["doc2"]

        mrr = evaluator.calculate_mrr(retrieved, relevant)

        # First relevant doc is at position 2
        assert mrr == pytest.approx(1/2, 0.01)

    def test_calculate_mrr_first_position(self, evaluator):
        """Test MRR when relevant doc is first."""
        retrieved = ["doc1", "doc2", "doc3"]
        relevant = ["doc1"]

        mrr = evaluator.calculate_mrr(retrieved, relevant)
        assert mrr == 1.0

    def test_evaluate_retrieval_quality(self, evaluator):
        """Test retrieval quality evaluation."""
        test_cases = [
            {
                "query": "test1",
                "expected_docs": ["doc1", "doc2"],
                "retrieved_docs": ["doc1", "doc2", "doc3"],
                "latency": 100
            },
            {
                "query": "test2",
                "expected_docs": ["doc3"],
                "retrieved_docs": ["doc3", "doc4", "doc5"],
                "latency": 150
            }
        ]

        results = evaluator.evaluate_retrieval_quality(test_cases)

        assert "avg_recall@3" in results
        assert "avg_precision@3" in results
        assert "avg_mrr" in results
        assert "avg_latency_ms" in results

        assert results["avg_recall@3"] > 0
        assert results["avg_precision@3"] > 0

    def test_get_statistics(self, evaluator):
        """Test statistics generation."""
        # Add some metrics
        evaluator.metrics["latency"] = [100, 150, 200]
        evaluator.metrics["recall@3"] = [0.8, 0.9, 0.7]

        stats = evaluator.get_statistics()

        assert "latency" in stats
        assert "recall@3" in stats

        assert "mean" in stats["latency"]
        assert "median" in stats["latency"]
        assert "std" in stats["latency"]
        assert "min" in stats["latency"]
        assert "max" in stats["latency"]
        assert "count" in stats["latency"]

    def test_generate_report(self, evaluator):
        """Test report generation."""
        evaluator.metrics["latency"] = [100, 150, 200]

        report = evaluator.generate_report()

        assert isinstance(report, str)
        assert "RAG System Evaluation Report" in report
        assert "LATENCY" in report

    def test_reset_metrics(self, evaluator):
        """Test metrics reset."""
        evaluator.metrics["latency"] = [100, 150, 200]

        assert len(evaluator.metrics) > 0

        evaluator.reset_metrics()

        assert len(evaluator.metrics) == 0
