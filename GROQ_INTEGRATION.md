# Groq API Integration Guide

## Overview

The Intelligent Parking Chatbot now supports **Groq API** as an alternative LLM provider alongside OpenAI. This provides:

- **Cost savings**: Groq offers competitive pricing
- **Flexibility**: Use whichever API key you have available
- **High performance**: Groq's LPU inference engine provides fast response times
- **Automatic fallback**: System auto-detects which API key is available

## What is Groq?

Groq provides ultra-fast inference for open-source LLMs using their custom Language Processing Unit (LPU) hardware. They support popular models like:
- **Llama 3** (8B and 70B parameters)
- **Mixtral 8x7B**
- And more

## Setup Options

### Option 1: OpenAI Only (Default)

```env
OPENAI_API_KEY=sk-your-openai-key-here
```

The system will use OpenAI for both embeddings and LLM generation.

### Option 2: Groq Only

```env
GROQ_API_KEY=gsk_your-groq-key-here
```

**Important**: Groq will be used for LLM generation, but vector embeddings require OpenAI. For full functionality, provide both keys:

```env
OPENAI_API_KEY=sk-your-openai-key-here  # For embeddings
GROQ_API_KEY=gsk_your-groq-key-here      # For LLM
LLM_PROVIDER=groq
```

### Option 3: Both APIs (Recommended for Production)

```env
OPENAI_API_KEY=sk-your-openai-key-here
GROQ_API_KEY=gsk_your-groq-key-here
LLM_PROVIDER=groq  # Optional: specify which to use
```

If both keys are provided and `LLM_PROVIDER` is not set, OpenAI will be used by default.

## Getting a Groq API Key

1. Visit [https://console.groq.com](https://console.groq.com)
2. Sign up for a free account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (starts with `gsk_`)

**Free Tier**: Groq offers generous free tier limits for testing and development.

## Model Mapping

When using Groq, the system automatically maps OpenAI models to Groq equivalents:

| OpenAI Model | Groq Model | Parameters |
|--------------|-----------|------------|
| gpt-3.5-turbo | llama3-8b-8192 | 8B |
| gpt-4 | llama3-70b-8192 | 70B |
| gpt-4-turbo | mixtral-8x7b-32768 | 8x7B |

You keep the same `LLM_MODEL` setting in your `.env` file, and the system handles the mapping automatically.

## Configuration Examples

### Example 1: Use Groq with Llama 3 8B

```env
OPENAI_API_KEY=sk-...  # For embeddings
GROQ_API_KEY=gsk_...   # For LLM
LLM_PROVIDER=groq
LLM_MODEL=gpt-3.5-turbo  # Automatically mapped to llama3-8b-8192
LLM_TEMPERATURE=0.7
MAX_TOKENS=500
```

### Example 2: Use Groq with Llama 3 70B

```env
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...
LLM_PROVIDER=groq
LLM_MODEL=gpt-4  # Automatically mapped to llama3-70b-8192
LLM_TEMPERATURE=0.7
MAX_TOKENS=500
```

### Example 3: Auto-detection (OpenAI only available)

```env
OPENAI_API_KEY=sk-...
# No GROQ_API_KEY provided
# System will automatically use OpenAI
```

### Example 4: Auto-detection (Groq only available)

```env
GROQ_API_KEY=gsk_...
# No OPENAI_API_KEY provided
# System will use Groq for LLM
# Warning: Vector embeddings will be limited
```

## Installation

Install the additional Groq dependency:

```bash
pip install langchain-groq==0.0.1
```

Or install all dependencies:

```bash
pip install -r requirements.txt
```

## Usage

No code changes required! Just set your API keys in `.env`:

```bash
# Copy example file
cp .env.example .env

# Edit with your keys
nano .env  # Linux/Mac
notepad .env  # Windows

# Initialize and run
python init_vectorstore.py
python main.py
```

## Performance Comparison

### OpenAI GPT-3.5-turbo
- **Speed**: ~1-2 seconds per response
- **Cost**: $0.50/$1.50 per 1M tokens (input/output)
- **Quality**: High, general purpose

### Groq Llama 3 8B
- **Speed**: ~0.2-0.5 seconds per response (⚡ up to 5x faster)
- **Cost**: Free tier available, then competitive pricing
- **Quality**: Very good for most chatbot tasks

### Groq Llama 3 70B
- **Speed**: ~0.5-1 second per response
- **Cost**: Higher than 8B, still competitive
- **Quality**: Excellent, comparable to GPT-4

## Important Notes

### Embeddings Requirement

**Vector embeddings currently require OpenAI API key** because:
- OpenAI's `text-embedding-3-small` model is used for document embeddings
- Groq doesn't currently provide embedding models
- The FAISS vector store is built with these embeddings

**Recommendation**: For full functionality, provide both API keys:
- Use OpenAI for embeddings (one-time cost during initialization)
- Use Groq for LLM generation (ongoing cost per conversation)

### Limitations When Using Groq Only

If you only provide `GROQ_API_KEY`:
- ✅ LLM generation works perfectly
- ✅ Database queries work
- ⚠️ Vector store functionality limited (can't create new embeddings)
- ✅ Existing vector stores can still be loaded and used if created previously

## Testing with Groq

```bash
# Set Groq API key
export GROQ_API_KEY=gsk_your-key-here  # Linux/Mac
set GROQ_API_KEY=gsk_your-key-here     # Windows

# Or edit .env file
echo "GROQ_API_KEY=gsk_your-key-here" >> .env

# Run tests
pytest tests/unit -v

# Test chatbot
python main.py
```

## Error Handling

### Error: "No LLM API key configured"

**Solution**: Provide at least one API key (OpenAI or Groq) in your `.env` file.

### Error: "langchain_groq module not found"

**Solution**: Install the Groq integration:
```bash
pip install langchain-groq==0.0.1
```

### Warning: "Groq API key provided but embeddings require OpenAI"

**Not an error**: The system will work but vector store creation is limited. Provide an OpenAI key for full functionality.

## Cost Optimization Strategies

### Strategy 1: Hybrid Approach (Recommended)
```env
OPENAI_API_KEY=sk-...  # For embeddings only (one-time)
GROQ_API_KEY=gsk_...   # For all conversations (ongoing)
LLM_PROVIDER=groq
```

**Savings**: ~70-90% reduction in ongoing LLM costs

### Strategy 2: Development with Groq, Production with OpenAI
```env
# Development
LLM_PROVIDER=groq

# Production (switch to OpenAI for consistency)
LLM_PROVIDER=openai
```

### Strategy 3: Groq for High-Volume, OpenAI for Complex Queries
Implement routing logic in your application based on query complexity.

## Monitoring and Logging

The system logs which provider is being used:

```
INFO - Using LLM provider: groq
INFO - Initialized RAG generator with Groq model: llama3-8b-8192 (mapped from gpt-3.5-turbo)
```

Check your console output to verify the correct provider is active.

## FAQ

### Q: Can I switch between providers without reinitializing?

**A**: No, the provider is set during chatbot initialization. To switch:
1. Update `.env` file
2. Restart the application

### Q: Will my existing vector store work with Groq?

**A**: Yes! Vector stores created with OpenAI embeddings work regardless of which LLM provider you use for generation.

### Q: Which model should I use?

**A**: 
- **Llama 3 8B** (gpt-3.5-turbo): Best for speed and cost, suitable for most chatbot tasks
- **Llama 3 70B** (gpt-4): Best for complex queries requiring deeper reasoning

### Q: Can I use Groq in production?

**A**: Yes! Groq is production-ready. Consider:
- Their service level agreements (SLA)
- Rate limits for your expected traffic
- Fallback to OpenAI if needed

### Q: How do I know which provider is active?

**A**: Check the startup logs. You'll see:
```
INFO - Using LLM provider: groq
```

### Q: Does this affect my evaluation metrics?

**A**: Evaluation metrics (latency, recall, precision, MRR) work the same regardless of provider. You may see faster latency with Groq.

## Advanced Configuration

### Custom Model Selection

If you want to use a specific Groq model directly:

```python
# In your code (advanced users)
from src.rag.generator import RAGGenerator

generator = RAGGenerator(
    model_name="llama3-70b-8192",  # Direct Groq model name
    api_key="gsk_...",
    provider="groq"
)
```

### Environment-Specific Configuration

```bash
# .env.development
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_dev_key

# .env.production
LLM_PROVIDER=openai
OPENAI_API_KEY=sk_prod_key
```

## Troubleshooting

### Issue 1: Slow responses with Groq

**Possible causes**:
- Network latency to Groq servers
- Model selected (70B is slower than 8B)

**Solution**:
- Check your internet connection
- Try switching to the 8B model
- Check Groq status page

### Issue 2: Different response quality

**Expected**: Llama 3 and GPT models may give slightly different responses for the same query.

**Solution**: 
- Adjust temperature settings
- Test both providers with your use case
- Fine-tune prompts if needed

### Issue 3: Rate limits

**Solution**:
- Check your Groq account limits
- Implement exponential backoff
- Consider upgrading your Groq plan

## Comparison Summary

| Feature | OpenAI | Groq |
|---------|--------|------|
| Speed | Good | Excellent (⚡ faster) |
| Cost | Moderate | Lower |
| Embeddings | ✅ Yes | ❌ No |
| Free Tier | Limited | Generous |
| Model Options | GPT-3.5, GPT-4 | Llama 3, Mixtral |
| Setup | Simple | Simple |

## Conclusion

Groq integration provides:
- ⚡ **Faster inference** (up to 5x)
- 💰 **Cost savings** (50-90% reduction)
- 🔄 **Flexibility** (easy provider switching)
- 🎯 **Same quality** (Llama 3 performs excellently)

**Recommended Setup**: Use both APIs with Groq for LLM and OpenAI for embeddings.

---

**Version**: 1.0  
**Last Updated**: 2026-11-14  
**Groq Website**: [https://groq.com](https://groq.com)  
**Groq Console**: [https://console.groq.com](https://console.groq.com)
