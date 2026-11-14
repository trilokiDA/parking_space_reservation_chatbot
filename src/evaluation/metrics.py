"""Evaluation metrics for RAG system performance."""
import time
import logging
from typing import List, Dict, Any, Tuple
from collections import defaultdict
import numpy as np
from sklearn.metrics import precision_score, recall_score

logger = logging.getLogger(__name__)


class RAGEvaluator:
    """Evaluator for RAG system performance metrics."""

    def __init__(self):
        """Initialize RAG evaluator."""
        self.metrics = defaultdict(list)

    def measure_latency(self, func, *args, **kwargs) -> Tuple[Any, float]:
        """Measure latency of a function execution.

        Args:
            func: Function to measure
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Tuple of (result, latency_ms)
        """
        start_time = time.time()
        result = func(*args, **kwargs)
        latency = (time.time() - start_time) * 1000  # Convert to milliseconds

        self.metrics["latency"].append(latency)
        return result, latency

    def calculate_recall_at_k(
        self,
        retrieved_docs: List[str],
        relevant_docs: List[str],
        k: int = 3
    ) -> float:
        """Calculate Recall@K metric.

        Args:
            retrieved_docs: List of retrieved document IDs
            relevant_docs: List of relevant document IDs
            k: Number of top documents to consider

        Returns:
            Recall@K score
        """
        if not relevant_docs:
            return 0.0

        retrieved_k = set(retrieved_docs[:k])
        relevant = set(relevant_docs)

        intersection = retrieved_k.intersection(relevant)
        recall = len(intersection) / len(relevant)

        self.metrics[f"recall@{k}"].append(recall)
        return recall

    def calculate_precision_at_k(
        self,
        retrieved_docs: List[str],
        relevant_docs: List[str],
        k: int = 3
    ) -> float:
        """Calculate Precision@K metric.

        Args:
            retrieved_docs: List of retrieved document IDs
            relevant_docs: List of relevant document IDs
            k: Number of top documents to consider

        Returns:
            Precision@K score
        """
        if not retrieved_docs:
            return 0.0

        retrieved_k = set(retrieved_docs[:k])
        relevant = set(relevant_docs)

        intersection = retrieved_k.intersection(relevant)
        precision = len(intersection) / len(retrieved_k) if retrieved_k else 0.0

        self.metrics[f"precision@{k}"].append(precision)
        return precision

    def calculate_mrr(
        self,
        retrieved_docs: List[str],
        relevant_docs: List[str]
    ) -> float:
        """Calculate Mean Reciprocal Rank (MRR).

        Args:
            retrieved_docs: List of retrieved document IDs
            relevant_docs: List of relevant document IDs

        Returns:
            MRR score
        """
        relevant = set(relevant_docs)

        for i, doc in enumerate(retrieved_docs, 1):
            if doc in relevant:
                mrr = 1.0 / i
                self.metrics["mrr"].append(mrr)
                return mrr

        self.metrics["mrr"].append(0.0)
        return 0.0

    def evaluate_retrieval_quality(
        self,
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Evaluate retrieval quality across multiple test cases.

        Args:
            test_cases: List of test cases with queries and expected results

        Returns:
            Dictionary of average metrics
        """
        results = {
            "avg_recall@3": [],
            "avg_precision@3": [],
            "avg_mrr": [],
            "avg_latency_ms": []
        }

        for test_case in test_cases:
            query = test_case.get("query")
            expected_docs = test_case.get("expected_docs", [])
            retrieved_docs = test_case.get("retrieved_docs", [])
            latency = test_case.get("latency", 0)

            # Calculate metrics
            recall = self.calculate_recall_at_k(retrieved_docs, expected_docs, k=3)
            precision = self.calculate_precision_at_k(retrieved_docs, expected_docs, k=3)
            mrr = self.calculate_mrr(retrieved_docs, expected_docs)

            results["avg_recall@3"].append(recall)
            results["avg_precision@3"].append(precision)
            results["avg_mrr"].append(mrr)
            results["avg_latency_ms"].append(latency)

        # Calculate averages
        summary = {
            metric: np.mean(values) if values else 0.0
            for metric, values in results.items()
        }

        logger.info(f"Evaluation complete: {summary}")
        return summary

    def get_statistics(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all collected metrics.

        Returns:
            Dictionary of statistics for each metric
        """
        stats = {}

        for metric_name, values in self.metrics.items():
            if values:
                stats[metric_name] = {
                    "mean": np.mean(values),
                    "median": np.median(values),
                    "std": np.std(values),
                    "min": np.min(values),
                    "max": np.max(values),
                    "count": len(values)
                }

        return stats

    def generate_report(self) -> str:
        """Generate evaluation report.

        Returns:
            Formatted report string
        """
        stats = self.get_statistics()

        report_lines = ["=" * 60, "RAG System Evaluation Report", "=" * 60, ""]

        for metric_name, metric_stats in stats.items():
            report_lines.append(f"\n{metric_name.upper()}:")
            report_lines.append(f"  Mean:   {metric_stats['mean']:.4f}")
            report_lines.append(f"  Median: {metric_stats['median']:.4f}")
            report_lines.append(f"  Std:    {metric_stats['std']:.4f}")
            report_lines.append(f"  Min:    {metric_stats['min']:.4f}")
            report_lines.append(f"  Max:    {metric_stats['max']:.4f}")
            report_lines.append(f"  Count:  {metric_stats['count']}")

        report_lines.append("\n" + "=" * 60)

        report = "\n".join(report_lines)
        logger.info("Evaluation report generated")

        return report

    def reset_metrics(self):
        """Reset all collected metrics."""
        self.metrics.clear()
        logger.info("Metrics reset")
