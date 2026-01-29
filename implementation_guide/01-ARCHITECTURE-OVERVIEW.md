# 🏗️ RAG Learning Platform - Architecture Overview

> **Version**: 2.0 (January 2026)  
> **Stack**: LlamaIndex + LangGraph | ChromaDB | Cohere Embeddings | Gemini/OpenAI  
> **Philosophy**: Agentic RAG with sophisticated preprocessing pipelines

---

## 📋 Table of Contents

1. [System Philosophy](#system-philosophy)
2. [High-Level Architecture](#high-level-architecture)
3. [Component Overview](#component-overview)
4. [Data Flow Pipeline](#data-flow-pipeline)
5. [Agentic Workflow Design](#agentic-workflow-design)
6. [Technology Stack](#technology-stack)

---

## 🎯 System Philosophy

### Core Principles

```
┌─────────────────────────────────────────────────────────────────┐
│                    ACCURACY OVER SPEED                          │
│  "Better to be slow and correct than fast and hallucinating"   │
└─────────────────────────────────────────────────────────────────┘
```

1. **Pre-computation Over Runtime Processing**
   - LLM-assisted metadata generation during ingestion
   - Rich context summaries computed ahead of time
   - Code understanding baked into embeddings

2. **Agentic Preprocessing**
   - Intelligent content analysis before chunking
   - Automatic context enrichment
   - Quality validation at every stage

3. **Citation-First Design**
   - Every retrieved chunk carries provenance
   - Page-level (minimum) citation tracking
   - Audit trail for content validation

4. **Hallucination Prevention**
   - Multi-stage retrieval verification
   - Grounded generation with explicit source mapping
   - Confidence scoring for generated content

---

## 🏛️ High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           LEARNING PLATFORM                                   │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     INGESTION PIPELINE (Agentic)                     │    │
│  │  ┌─────────┐   ┌──────────┐   ┌───────────┐   ┌─────────────────┐  │    │
│  │  │ Content │──▶│ Analyzer │──▶│ Enricher  │──▶│ Vector Store    │  │    │
│  │  │ Upload  │   │  Agent   │   │   Agent   │   │ (ChromaDB)      │  │    │
│  │  └─────────┘   └──────────┘   └───────────┘   └─────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     RETRIEVAL PIPELINE (Hybrid)                      │    │
│  │  ┌─────────┐   ┌──────────┐   ┌───────────┐   ┌─────────────────┐  │    │
│  │  │  Query  │──▶│  Query   │──▶│  Hybrid   │──▶│   Re-Ranker     │  │    │
│  │  │  Input  │   │ Expander │   │ Retriever │   │   (Cohere)      │  │    │
│  │  └─────────┘   └──────────┘   └───────────┘   └─────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     GENERATION PIPELINE (Grounded)                   │    │
│  │  ┌─────────┐   ┌──────────┐   ┌───────────┐   ┌─────────────────┐  │    │
│  │  │Retrieved│──▶│ Context  │──▶│ Generator │──▶│   Validator     │  │    │
│  │  │ Chunks  │   │ Assembler│   │   (LLM)   │   │   (Citation)    │  │    │
│  │  └─────────┘   └──────────┘   └───────────┘   └─────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Component Overview

### 1. Content Management Layer

| Component | Purpose | Technology |
|-----------|---------|------------|
| File Processor | Extract content from PPTX, PDF, Code | python-pptx, PyMuPDF, Tree-sitter |
| Content Analyzer | Classify, summarize, extract structure | Gemini-Flash / GPT-4o-mini |
| Metadata Generator | Create rich searchable metadata | LLM + Rule-based hybrid |

### 2. Embedding & Storage Layer

| Component | Purpose | Technology |
|-----------|---------|------------|
| Text Embeddings | Semantic vectors for theory content | Cohere embed-v3 |
| Code Embeddings | Code-aware vectors for lab content | Cohere + UniXcoder hybrid |
| Vector Store | Similarity search + filtering | ChromaDB |
| Metadata Store | Structured data & relationships | Supabase / SQLite |

### 3. Retrieval Layer

| Component | Purpose | Technology |
|-----------|---------|------------|
| Query Processor | Expand, classify, route queries | LLM Agent |
| Hybrid Retriever | Dense + Sparse search | ChromaDB + BM25 |
| Re-Ranker | Precision optimization | Cohere Rerank |
| Context Assembler | Build coherent context windows | Custom logic |

### 4. Generation Layer

| Component | Purpose | Technology |
|-----------|---------|------------|
| Prompt Builder | Structured prompts with citations | Jinja2 templates |
| Generator | Content creation | Gemini-Flash / GPT-4o |
| Citation Mapper | Track source → output mapping | Custom attribution |
| Validator | Verify grounding & accuracy | LLM-as-judge + rules |

---

## 🔄 Data Flow Pipeline

### Ingestion Flow (Detailed)

```
┌────────────────────────────────────────────────────────────────────────┐
│                        INGESTION PIPELINE                              │
└────────────────────────────────────────────────────────────────────────┘

     ┌──────────┐
     │  Upload  │
     │  (PPTX/  │
     │  PDF/    │
     │  Code)   │
     └────┬─────┘
          │
          ▼
┌─────────────────────┐
│  FORMAT DETECTION   │  ──────▶  Route to appropriate processor
└─────────┬───────────┘
          │
          ├─────────────────────────────────────────────┐
          │                                             │
          ▼                                             ▼
┌─────────────────────┐                    ┌─────────────────────┐
│  THEORY PROCESSOR   │                    │   CODE PROCESSOR    │
│  ├─ PPTX Extractor │                    │   ├─ AST Parser     │
│  ├─ PDF Extractor  │                    │   ├─ Syntax Aware   │
│  └─ Image Handler  │                    │   └─ Dependency Map │
└─────────┬───────────┘                    └─────────┬───────────┘
          │                                          │
          ▼                                          ▼
┌─────────────────────┐                    ┌─────────────────────┐
│  CONTENT ANALYZER   │                    │  CODE ANALYZER      │
│  (LLM Agent)        │                    │  (LLM Agent)        │
│  ├─ Topic Extract  │                    │  ├─ Purpose Summary │
│  ├─ Key Concepts   │                    │  ├─ Algorithm ID    │
│  ├─ Prerequisites  │                    │  ├─ Complexity      │
│  └─ Learning Goals │                    │  └─ Dependencies    │
└─────────┬───────────┘                    └─────────┬───────────┘
          │                                          │
          ▼                                          ▼
┌─────────────────────┐                    ┌─────────────────────┐
│  SEMANTIC CHUNKER   │                    │   AST CHUNKER       │
│  ├─ Slide-aware    │                    │   ├─ Function-level │
│  ├─ Section-aware  │                    │   ├─ Class-level    │
│  └─ Context-aware  │                    │   └─ Block-level    │
└─────────┬───────────┘                    └─────────┬───────────┘
          │                                          │
          └──────────────┬───────────────────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  METADATA ENRICHER  │
              │  (LLM Agent)        │
              │  ├─ Generate tags   │
              │  ├─ Create summary  │
              │  ├─ Extract Q&A     │
              │  └─ Link relations  │
              └─────────┬───────────┘
                        │
                        ▼
              ┌─────────────────────┐
              │    EMBED & STORE    │
              │  ├─ Cohere Embed    │
              │  ├─ ChromaDB Store  │
              │  └─ Metadata Index  │
              └─────────────────────┘
```

### Retrieval Flow (Detailed)

```
┌────────────────────────────────────────────────────────────────────────┐
│                        RETRIEVAL PIPELINE                              │
└────────────────────────────────────────────────────────────────────────┘

     ┌──────────┐
     │  User    │
     │  Query   │
     └────┬─────┘
          │
          ▼
┌─────────────────────┐
│   QUERY ANALYZER    │  ──────▶  Classify: Theory vs Code vs Hybrid
│   (LLM Agent)       │  ──────▶  Detect: Concepts, Languages, Topics
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   QUERY EXPANDER    │
│   ├─ Synonyms       │  "sorting" → "sorting, sort algorithm, quicksort..."
│   ├─ Reformulations │  Generate 2-3 query variants
│   └─ HyDE (optional)│  Generate hypothetical answer for embedding
└─────────┬───────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────┐
│                    HYBRID RETRIEVAL                      │
│  ┌─────────────────┐         ┌─────────────────┐        │
│  │  Dense Search   │         │  Sparse Search  │        │
│  │  (Cohere Embed) │         │  (BM25/Keywords)│        │
│  │  k=50           │         │  k=50           │        │
│  └────────┬────────┘         └────────┬────────┘        │
│           │                           │                  │
│           └───────────┬───────────────┘                  │
│                       ▼                                  │
│            ┌─────────────────────┐                       │
│            │   RRF Fusion        │  Reciprocal Rank      │
│            │   (k=60 parameter)  │  Fusion               │
│            └─────────────────────┘                       │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
               ┌─────────────────────┐
               │   COHERE RERANK     │
               │   ├─ Cross-encoder  │
               │   ├─ Query-doc pair │
               │   └─ Top-k=10       │
               └─────────┬───────────┘
                         │
                         ▼
               ┌─────────────────────┐
               │  CONTEXT ASSEMBLER  │
               │  ├─ Deduplicate     │
               │  ├─ Order by source │
               │  ├─ Add citations   │
               │  └─ Fit to window   │
               └─────────────────────┘
```

---

## 🤖 Agentic Workflow Design

### Agent Architecture

```python
# Conceptual Agent Structure
class LearningPlatformAgents:
    """
    Multi-agent system for intelligent content processing
    """
    
    agents = {
        # Ingestion Agents
        "content_analyzer": ContentAnalyzerAgent,      # Understands document structure
        "code_preprocessor": CodePreprocessorAgent,    # Enriches code with context
        "metadata_generator": MetadataGeneratorAgent,  # Creates rich metadata
        
        # Retrieval Agents  
        "query_router": QueryRouterAgent,              # Routes to appropriate retriever
        "query_expander": QueryExpanderAgent,          # Generates query variants
        
        # Generation Agents
        "context_curator": ContextCuratorAgent,        # Assembles optimal context
        "content_generator": ContentGeneratorAgent,    # Creates learning materials
        "validator": ValidationAgent,                  # Verifies accuracy
    }
```

### Agent Communication Pattern

```
┌────────────────────────────────────────────────────────────────┐
│                    AGENTIC ORCHESTRATION                       │
│                      (LangGraph Style)                         │
└────────────────────────────────────────────────────────────────┘

                    ┌───────────────┐
                    │  Supervisor   │
                    │    Agent      │
                    └───────┬───────┘
                            │
           ┌────────────────┼────────────────┐
           │                │                │
           ▼                ▼                ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │   Analyzer   │ │  Retriever   │ │  Generator   │
    │    Agent     │ │    Agent     │ │    Agent     │
    └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
           │                │                │
           └────────────────┼────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   Validator   │
                    │     Agent     │
                    └───────────────┘
```

---

## 🛠️ Technology Stack

### Core Stack

```yaml
Framework:
  RAG_Framework: LlamaIndex  # Primary for indexing & retrieval
  Orchestration: LangGraph   # For agentic workflows
  
Storage:
  Vector_DB: ChromaDB        # Local/Supabase hosted
  Metadata_DB: Supabase      # PostgreSQL for structured data
  File_Storage: Local/Supabase Storage
  
Embeddings:
  Primary: Cohere embed-english-v3.0
  Code_Aware: Cohere + custom code preprocessing
  
LLM:
  Primary: Gemini-2.0-Flash  # Fast, cost-effective
  Fallback: GPT-4o-mini      # Alternative
  Validation: Same as primary
  
Reranking:
  Service: Cohere Rerank v3

Processing:
  PPTX: python-pptx
  PDF: PyMuPDF (fitz)
  Code: Tree-sitter (AST parsing)
  Chunking: LlamaIndex + custom semantic
```

### Infrastructure

```yaml
Development:
  Language: Python 3.11+
  Package_Manager: uv / pip
  Environment: venv / conda

API_Clients:
  - cohere>=5.0
  - google-generativeai>=0.8
  - openai>=1.0
  - chromadb>=0.5
  - llama-index>=0.11

Content_Processing:
  - python-pptx>=1.0
  - pymupdf>=1.24
  - tree-sitter>=0.22
  - tree-sitter-languages>=1.10
```

---

## 📁 Project Structure

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
│   │   │   ├── semantic_chunker.py
│   │   │   └── ast_chunker.py
│   │   └── enrichers/
│   │       └── metadata_enricher.py
│   │
│   ├── retrieval/              # Search & retrieval
│   │   ├── hybrid_retriever.py
│   │   ├── reranker.py
│   │   └── context_assembler.py
│   │
│   ├── generation/             # Content generation
│   │   ├── prompt_builder.py
│   │   ├── generator.py
│   │   └── citation_mapper.py
│   │
│   ├── validation/             # Quality assurance
│   │   ├── content_validator.py
│   │   └── code_validator.py
│   │
│   └── storage/                # Data persistence
│       ├── vector_store.py
│       └── metadata_store.py
│
├── schemas/                    # Data models
│   ├── document.py
│   ├── chunk.py
│   └── metadata.py
│
├── config/                     # Configuration
│   ├── settings.py
│   └── prompts/
│       ├── analysis_prompts.yaml
│       ├── generation_prompts.yaml
│       └── validation_prompts.yaml
│
├── tests/                      # Test suite
└── docs/                       # Documentation
```

---

## 🔗 Next Steps

Continue to the following guides:

1. **[02-METADATA-SCHEMAS.md](./02-METADATA-SCHEMAS.md)** - Rich metadata structures for each content type
2. **[03-CHUNKING-STRATEGIES.md](./03-CHUNKING-STRATEGIES.md)** - Intelligent chunking approaches
3. **[04-CODE-PREPROCESSING.md](./04-CODE-PREPROCESSING.md)** - LLM-assisted code enrichment
4. **[05-RETRIEVAL-PIPELINE.md](./05-RETRIEVAL-PIPELINE.md)** - Hybrid search implementation
5. **[06-GENERATION-VALIDATION.md](./06-GENERATION-VALIDATION.md)** - Grounded generation with citations
6. **[07-IMPLEMENTATION-TEMPLATES.md](./07-IMPLEMENTATION-TEMPLATES.md)** - Code templates and patterns
