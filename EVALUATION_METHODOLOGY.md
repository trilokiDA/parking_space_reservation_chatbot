# RAG System Evaluation Methodology

## Overview

This document describes the evaluation methodology for the Intelligent Parking Chatbot's RAG (Retrieval-Augmented Generation) system implemented in Stage 1.

## Evaluation Metrics

### 1. Response Latency

**Definition**: Time taken to process a user query and generate a response.

**Measurement**: 
- Tracked using Python's `time.time()` function
- Measured in milliseconds
- Includes: input sanitization, context retrieval, LLM generation, output filtering

**Acceptable Ranges**:
- Excellent: < 1000ms
- Good: 1000-2000ms
- Acceptable: 2000-3000ms
- Poor: > 3000ms

**Implementation**:
```python
start_time = time.time()
result = function(*args, **kwargs)
latency = (time.time() - start_time) * 1000  # Convert to ms
```

### 2. Recall@K

**Definition**: Proportion of relevant documents that are successfully retrieved in the top K results.

**Formula**:
```
Recall@K = |Retrieved@K ∩ Relevant| / |Relevant|
```

**Interpretation**:
- 1.0 = Perfect recall (all relevant docs retrieved)
- 0.0 = Complete failure (no relevant docs retrieved)

**K Values Used**: K=3 (retrieves top 3 most similar documents)

**Example**:
- Relevant documents: [doc1, doc2, doc5]
- Retrieved top 3: [doc1, doc2, doc3]
- Recall@3 = 2/3 = 0.667

### 3. Precision@K

**Definition**: Proportion of retrieved documents that are actually relevant.

**Formula**:
```
Precision@K = |Retrieved@K ∩ Relevant| / |Retrieved@K|
```

**Interpretation**:
- 1.0 = Perfect precision (all retrieved docs are relevant)
- 0.0 = Complete failure (no retrieved docs are relevant)

**Example**:
- Relevant documents: [doc1, doc2, doc5]
- Retrieved top 3: [doc1, doc2, doc3]
- Precision@3 = 2/3 = 0.667

### 4. Mean Reciprocal Rank (MRR)

**Definition**: Average of the reciprocal ranks of the first relevant document.

**Formula**:
```
MRR = 1/rank (where rank is position of first relevant document)
```

**Interpretation**:
- 1.0 = First result is relevant
- 0.5 = Second result is first relevant one
- 0.33 = Third result is first relevant one

**Example**:
- Retrieved: [doc3, doc1, doc5]
- Relevant: [doc1, doc2]
- First relevant doc (doc1) is at position 2
- MRR = 1/2 = 0.5

## Evaluation Process

### Automated Evaluation

Run the evaluation script:
```bash
python run_evaluation.py
```

This script:
1. Initializes the chatbot with test configuration
2. Processes predefined test queries
3. Measures latency for each query
4. Collects performance statistics
5. Generates a comprehensive report

### Manual Evaluation

For qualitative assessment:

1. **Correctness**: Does the response answer the question?
2. **Completeness**: Is all necessary information included?
3. **Relevance**: Is the response on-topic?
4. **Coherence**: Is the response well-structured and readable?
5. **Safety**: No sensitive data exposure?

### Test Query Categories

**Category 1: Operating Hours**
- "What are your hours?"
- "When are you open?"
- "Operating hours?"

**Category 2: Pricing**
- "How much does parking cost?"
- "What are your rates?"
- "Pricing information?"

**Category 3: Availability**
- "Are there available spaces?"
- "Do you have space?"
- "Is parking available?"

**Category 4: Location**
- "Where is the parking?"
- "What is your address?"
- "How do I find you?"

**Category 5: Facilities**
- "Do you have EV charging?"
- "What amenities do you offer?"
- "Is there handicap parking?"

**Category 6: Policies**
- "What is your cancellation policy?"
- "Can I modify my reservation?"
- "What are your rules?"

## Baseline Performance Targets

Based on similar RAG systems, we target:

| Metric | Target | Minimum Acceptable |
|--------|--------|-------------------|
| Latency | < 1500ms | < 3000ms |
| Recall@3 | > 0.80 | > 0.60 |
| Precision@3 | > 0.75 | > 0.60 |
| MRR | > 0.85 | > 0.70 |

## Evaluation Results Interpretation

### Latency Analysis

**High Latency (>3000ms) Causes**:
- Network delays (OpenAI API calls)
- Large document corpus
- Inefficient embedding computation
- Database query bottlenecks

**Optimization Strategies**:
- Cache embeddings locally
- Reduce chunk size
- Implement request batching
- Use faster embedding models

### Recall Analysis

**Low Recall (<0.60) Causes**:
- Poor document chunking
- Inadequate embedding model
- Insufficient K value
- Irrelevant documents in corpus

**Optimization Strategies**:
- Improve chunking strategy
- Use better embedding model (text-embedding-3-large)
- Increase K value
- Clean up document corpus

### Precision Analysis

**Low Precision (<0.60) Causes**:
- Documents too generic
- Poor query understanding
- Overly large chunks
- Weak semantic similarity threshold

**Optimization Strategies**:
- Refine document metadata
- Add query preprocessing
- Adjust chunk size
- Implement re-ranking

## Continuous Evaluation

### During Development

```python
# Track metrics in real-time
evaluator = chatbot.get_evaluator()
response = chatbot.process_message(query)
stats = evaluator.get_statistics()
```

### In Production

Recommended monitoring:
- Average latency per hour
- Recall/Precision trends over time
- User satisfaction scores
- Error rates

## Guard Rails Evaluation

### Sensitive Data Detection Rate

**Metric**: Percentage of PII correctly identified

**Test Cases**:
- Email addresses
- Phone numbers
- Credit card numbers
- License plates

**Expected Performance**: > 95% detection rate

### False Positive Rate

**Metric**: Percentage of non-PII flagged as sensitive

**Target**: < 5%

### Input Validation Success Rate

**Metric**: Percentage of invalid inputs correctly rejected

**Test Cases**:
- XSS attempts
- SQL injection attempts
- Malformed dates
- Invalid names/car numbers

**Expected Performance**: 100% (all malicious inputs blocked)

## Reporting Format

### Automated Report Structure

```
============================================================
RAG System Evaluation Report
============================================================

LATENCY:
  Mean:   1234.56ms
  Median: 1200.00ms
  Std:    150.25ms
  Min:    980.50ms
  Max:    1580.75ms
  Count:  50

RECALL@3:
  Mean:   0.8523
  Median: 0.8667
  Std:    0.0842
  Min:    0.6667
  Max:    1.0000
  Count:  50

PRECISION@3:
  Mean:   0.8234
  Median: 0.8333
  Std:    0.0923
  Min:    0.6667
  Max:    1.0000
  Count:  50

MRR:
  Mean:   0.8956
  Median: 1.0000
  Std:    0.1234
  Min:    0.5000
  Max:    1.0000
  Count:  50

============================================================
```

## Benchmark Comparisons

### Industry Standards

Typical RAG systems achieve:
- **Latency**: 1000-2000ms (with caching)
- **Recall@3**: 0.70-0.85
- **Precision@3**: 0.65-0.80
- **MRR**: 0.75-0.90

### Our System Goals

Stage 1 targets:
- **Latency**: < 1500ms average
- **Recall@3**: > 0.80
- **Precision@3**: > 0.75
- **MRR**: > 0.85

## Future Improvements

### Stage 2-4 Enhancements

1. **Advanced Retrieval**
   - Hybrid search (semantic + keyword)
   - Re-ranking mechanisms
   - Query expansion

2. **Performance Optimization**
   - Response caching
   - Async processing
   - Model quantization

3. **Quality Metrics**
   - BLEU scores for response quality
   - User satisfaction ratings
   - Conversation success rate

4. **A/B Testing**
   - Compare different embedding models
   - Test various prompt templates
   - Evaluate chunking strategies

## References

- **Recall and Precision**: Standard information retrieval metrics
- **MRR**: Search engine evaluation metric
- **RAG**: [Retrieval-Augmented Generation paper](https://arxiv.org/abs/2005.11401)
- **LangChain Evaluation**: [Official docs](https://python.langchain.com/docs/guides/evaluation)

---

**Document Version**: 1.0  
**Last Updated**: Stage 1 Implementation  
**Next Review**: Stage 2 Planning
