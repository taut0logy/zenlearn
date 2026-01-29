# 🎓 RAG-Powered Learning Platform - Complete Architecture Guide

> **A Sophisticated AI Learning System with Advanced Retrieval and Grounded Generation**

---

## 🌟 Overview

This comprehensive guide details the architecture and implementation of an **AI-powered university learning platform** featuring:

- **Multi-course content management** for Theory and Lab materials
- **Intelligent semantic search** with hybrid retrieval (dense + sparse)
- **LLM-assisted code preprocessing** for natural language to code search
- **Grounded content generation** with precise citations
- **Agentic workflows** for quality validation and self-improvement

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| RAG Framework | LlamaIndex + LangGraph | Retrieval quality + Agentic workflows |
| Vector Database | ChromaDB | Semantic similarity search |
| Embeddings | Cohere embed-v3 | High-quality text vectors |
| Reranking | Cohere Rerank v3 | Precision optimization |
| LLM | Gemini Flash / GPT-4o | Generation & Analysis |
| Code Parsing | Tree-sitter | AST-based code understanding |

---

## 📚 Guide Contents

### Core Architecture

| # | Document | Description |
|---|----------|-------------|
| 01 | [Architecture Overview](./01-ARCHITECTURE-OVERVIEW.md) | System design, component overview, data flow pipelines |
| 02 | [Metadata Schemas](./02-METADATA-SCHEMAS.md) | Rich metadata structures for documents, slides, code |
| 03 | [Chunking Strategies](./03-CHUNKING-STRATEGIES.md) | Content-aware chunking for slides, PDFs, code |

### Advanced Features

| # | Document | Description |
|---|----------|-------------|
| 04 | [Code Preprocessing](./04-CODE-PREPROCESSING.md) | LLM-assisted code understanding & NL bridge generation |
| 05 | [Retrieval Pipeline](./05-RETRIEVAL-PIPELINE.md) | Hybrid search, query expansion, reranking |
| 06 | [Generation & Validation](./06-GENERATION-VALIDATION.md) | Grounded generation with citations, validation framework |

### Implementation

| # | Document | Description |
|---|----------|-------------|
| 07 | [Implementation Templates](./07-IMPLEMENTATION-TEMPLATES.md) | Production-ready code templates, API design |

---

## 🎯 Key Innovations

### 1. LLM-Assisted Code Preprocessing

Traditional code search fails when students ask natural language questions. Our approach:

```
Student Query: "How do I sort a list efficiently?"

Traditional Search: ❌ No match (query has no code keywords)

With NL Bridge: ✅ Matches code with pre-generated metadata:
  - Summary: "Efficiently sorts array using quicksort"
  - NL Queries: ["sort list", "efficient sorting", "arrange elements"]
  - Concepts: ["divide and conquer", "O(n log n)"]
```

### 2. Hybrid Retrieval with Adaptive Reranking

```
Query → Dense Search (semantic) ─┐
                                 ├─→ RRF Fusion → Rerank → Top 10
Query → Sparse Search (BM25) ────┘

Result: 28-48% improvement in retrieval quality
```

### 3. Grounded Generation with Citation Tracking

Every generated statement traces back to source material:

```markdown
## Quicksort Algorithm

According to **[Slide 15]**, quicksort uses a divide-and-conquer approach
where elements are partitioned around a pivot element. The algorithm
achieves O(n log n) average-case complexity **[Slide 16]**.

---
**Sources:**
- [Slide 15]: Lecture 5 - Sorting Algorithms
- [Slide 16]: Lecture 5 - Complexity Analysis
```

### 4. Agentic Validation Workflow

```
Generate → Validate → (Pass) → Output
              ↓
           (Fail)
              ↓
         Regenerate with corrections
```

---

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Python 3.11+
python --version

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Setup

```bash
# .env file
COHERE_API_KEY=your_cohere_key
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key  # Optional fallback
```

### 3. Initialize System

```python
from config.settings import get_settings
from src.storage.vector_store import VectorStore
from src.ingestion.pipeline import IngestionPipeline

settings = get_settings()

# Initialize vector store
vector_store = VectorStore(
    persist_dir=settings.storage.chroma_persist_dir,
    collection_name=settings.storage.collection_name,
    cohere_api_key=settings.embedding.cohere_api_key
)

# Initialize ingestion pipeline
ingestion = IngestionPipeline(vector_store, llm_client, settings)

# Ingest a document
result = await ingestion.ingest(
    file_path="lecture_slides.pptx",
    course_context={
        "course_id": "cs101",
        "course_name": "Introduction to Programming",
        "category": "theory",
        "week_number": 5
    }
)
```

### 4. Query the System

```python
from src.retrieval.pipeline import RetrievalPipeline
from src.generation.pipeline import GenerationPipeline

# Query with RAG
result = await generation_pipeline.generate(
    query="Explain how quicksort works",
    course_id="cs101"
)

print(result['content'])
# → Detailed explanation with citations
```

---

## 📊 Expected Performance

| Metric | Target | Notes |
|--------|--------|-------|
| Retrieval Recall@10 | > 0.85 | With hybrid search |
| Retrieval Precision@10 | > 0.70 | After reranking |
| Citation Accuracy | 100% | Page/slide level |
| Query Latency | < 2s | End-to-end |
| Groundedness Score | > 0.95 | Validated generation |

---

## 🏗️ Project Structure

```
learning-platform/
├── src/
│   ├── agents/                 # Agentic components
│   │   ├── content_analyzer.py
│   │   ├── code_preprocessor.py
│   │   ├── query_router.py
│   │   └── validator.py
│   │
│   ├── ingestion/              # Content processing
│   │   ├── processors/
│   │   │   ├── pptx_processor.py
│   │   │   ├── pdf_processor.py
│   │   │   └── code_processor.py
│   │   ├── chunkers/
│   │   └── enrichers/
│   │
│   ├── retrieval/              # Search & retrieval
│   │   ├── hybrid_retriever.py
│   │   ├── reranker.py
│   │   └── context_assembler.py
│   │
│   ├── generation/             # Content generation
│   │   ├── generator.py
│   │   └── citation_mapper.py
│   │
│   ├── validation/             # Quality assurance
│   │   └── content_validator.py
│   │
│   ├── storage/                # Data persistence
│   │   └── vector_store.py
│   │
│   └── api/                    # API endpoints
│       └── routes.py
│
├── schemas/                    # Pydantic models
├── config/                     # Configuration
│   ├── settings.py
│   └── prompts/
├── tests/
└── docs/                       # This guide
```

---

## 💡 Design Decisions

### Why ChromaDB?
- ✅ Easy setup, good for prototyping
- ✅ Persistent storage
- ✅ Metadata filtering
- ⚠️ Consider Qdrant for production scale

### Why Cohere for Embeddings?
- ✅ High quality embed-v3 model
- ✅ Built-in reranking API
- ✅ Search vs document embedding modes
- ✅ Cost-effective

### Why LLM Preprocessing for Code?
- ✅ Bridges semantic gap (NL → Code)
- ✅ One-time cost at ingestion
- ✅ Dramatically improves code search
- ✅ ~$0.01 per file

### Why Hybrid Search?
- ✅ Dense catches semantic similarity
- ✅ Sparse catches exact terms (function names, etc.)
- ✅ 28-48% quality improvement in research
- ✅ Essential for code search

---

## 📖 Further Reading

- [LlamaIndex Documentation](https://docs.llamaindex.ai/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Cohere Embed v3](https://docs.cohere.com/docs/embed)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Tree-sitter Documentation](https://tree-sitter.github.io/)

---

## 🤝 Contributing

This is a standalone project guide. Feel free to adapt and extend for your specific needs.

---

**Built with ❤️ for better AI-powered education**
