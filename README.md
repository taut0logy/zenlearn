# ZenLearn - AI-Powered Learning Platform

---
## Team ZenBit

### Members
- [Md. Faysal Mahmud](https://github.com/faysal-star)
- [Raufun Ahsan](https://github.com/taut0logy)
- [Md. Sakibur Rahman](https://github.com/sakiburrahman07)

> **BCF Hackathon 2026:** ZenLearn - Intelligent course content generation and personalized learning
---

## System Architecture

```mermaid
graph TB
    subgraph API["FastAPI Backend"]
        direction TB
        A[API Endpoints]
    end
    
    subgraph Services["Core Services"]
        S1[Gemini LLM]
        S2[Embeddings]
        S3[Vector Store]
        S4[Image Gen]
    end
    
    subgraph RAG["RAG Engine"]
        R1[Chunker]
        R2[Semantic Search]
        R3[Hybrid Retrieval]
        R4[Code Processor]
    end
    
    subgraph Content["Content Gen Engine"]
        C1[Theory Generation]
        C2[Lab Generation]
        C3[Validation]
        C4[Video Generation]
    end
    
    A --> Services
    A --> RAG
    A --> Content
    RAG --> Services
    Content --> Services
    Content --> RAG
```

---

## Project Requirements → Module Mapping

This section maps each project requirement to the module(s) that implement it.

```mermaid
flowchart LR
    subgraph Parts["Project Requirements"]
        P1[Part 1: CMS]
        P2[Part 2: Search]
        P3[Part 3: Content Gen]
        P4[Part 4: Validation]
        P5[Part 5: Chat]
        B1[Bonus: Notes]
        B2[Bonus: Video]
        B3[Bonus: Community]
    end
    
    subgraph Modules["Backend Modules"]
        M1[cms_agent/]
        M2[rag_engine/]
        M3[content_gen_engine/]
        M4[validators/]
        M5[chat-agent/]
        M6[notes_agent/]
        M7[video_gen/]
        M8[community_agent/]
    end
    
    P1 --> M1
    P2 --> M2
    P3 --> M3
    P4 --> M4
    P5 --> M5
    B1 --> M6
    B2 --> M7
    B3 --> M8
```

| Requirement | Module | Key Components | Status |
|-------------|--------|----------------|--------|
| **Part 1: CMS** | `cms_agent/` | `service.py`, `rag_integration.py`, `models.py` | ✅ |
| **Part 2: Intelligent Search** | `rag_engine/` | `retriever/`, `chunker/`, `code_processor/` | ✅ |
| **Part 3: AI Content Generation** | `content_gen_engine/` | `agents/`, `generators/`, `pipeline.py` | ✅ |
| **Part 4: Validation** | `content_gen_engine/validators/` | `SyntaxChecker`, `CodeExecutor`, `ContentValidator` | ✅ |
| **Part 5: Chat Interface** | `chat-agent/` | `agent.py`, `context.py`, `memory.py`, `tools/` | ✅ |
| **Bonus: Handwritten Notes** | `notes_agent/` | `vision.py`, `latex_generator.py`, `agent.py` | ✅ |
| **Bonus: Video Generation** | `content_gen_engine/video_gen/` | `pipeline.py`, Manim, TTS, FFmpeg | ✅ |
| **Bonus: Community & Bot** | `community_agent/` | `service.py`, `bot.py`, `schemas.py` | ✅ |

---

## Agent Modules

### CMS Agent (`cms_agent/`)

Handles content management system operations for course materials.

| File | Purpose |
|------|---------|
| `service.py` | CRUD operations for courses, materials, metadata management |
| `rag_integration.py` | Auto-index uploaded content into RAG pipeline |
| `models.py` | SQLAlchemy/Pydantic models for courses, materials |
| `router.py` | FastAPI endpoints for CMS operations |

### Chat Agent (`chat-agent/`)

Conversational AI interface with multi-turn memory and tool orchestration.

| Component | Purpose |
|-----------|---------|
| `agent.py` | Main chat agent with Gemini integration |
| `context.py` | Context window management, retrieval integration |
| `memory.py` | Conversation history, session persistence |
| `service.py` | Orchestrates RAG search, content gen calls |
| `tools/` | Function calling tools (search, generate, explain) |

### Community Agent (`community_agent/`)

Social learning features with AI-powered bot support.

| Component | Purpose |
|-----------|---------|
| `service.py` | Post/comment CRUD, voting, notifications |
| `bot.py` | Auto-reply bot using RAG for grounded answers |
| `schemas.py` | Pydantic models for posts, comments, reactions |

### Notes Agent (`notes_agent/`)

Handwritten notes digitization with vision AI.

| Component | Purpose |
|-----------|---------|
| `vision.py` | Gemini Vision for handwriting OCR |
| `latex_generator.py` | Convert extracted text to LaTeX/Markdown |
| `agent.py` | Orchestrates vision → LaTeX pipeline |

---

## Core Services (`services/`)

### Gemini Service
- **Model**: `gemini-3-pro-preview` via `google-genai` SDK
- **Features**: Text generation, JSON mode, streaming, structured output with JSON schema enforcement
- **Config**: Temperature, top-p/k, max tokens, system instructions

### Embedding Service
- **Model**: Gemini text embeddings
- **Purpose**: Convert text chunks to dense vectors for semantic search
- **Batching**: Efficient batch embedding with rate limiting

### Vector Store Service
- **Backend**: ChromaDB (local) / PGVector (production)
- **Operations**: Upsert, similarity search, filtered queries, metadata handling
- **Collections**: Separate collections per course/content type

### Image Generation Service
- **Model**: Imagen 4.0 via Gemini API
- **Use Case**: Generate diagrams, illustrations, concept visualizations
- **Fallback**: Mermaid diagrams for flowcharts

---

## RAG Engine (`rag_engine/`)

### RAG Pipeline Flow

```mermaid
flowchart LR
    subgraph Ingestion
        D1[PDF] --> C[Chunker]
        D2[PPTX] --> C
        D3[Code] --> C
        C --> E[Embeddings]
        E --> V[(Vector DB)]
    end
    
    subgraph Retrieval
        Q[Query] --> QP[Query Processor]
        QP --> |Expand| HB[Hybrid Retriever]
        HB --> |Dense| V
        HB --> |Sparse| BM[BM25 Index]
        V --> RRF[RRF Fusion]
        BM --> RRF
        RRF --> RR[Reranker]
        RR --> CA[Context Assembler]
    end
    
    CA --> LLM[Gemini LLM]
```

### Chunking Module (`chunker/`)

| Chunker | Source | Technique |
|---------|--------|-----------|
| **PDFChunker** | PDF documents | PyMuPDF extraction, semantic paragraph splitting, overlap windows |
| **SlideChunker** | PPTX files | python-pptx, slide-aware boundaries, speaker notes extraction |
| **CodeChunker** | Source code | AST-based splitting at function/class boundaries, docstring preservation |

**Base Chunker Features**:
- Configurable chunk size (tokens/chars)
- Overlap for context continuity
- Metadata enrichment (source, page, section)
- tiktoken for accurate token counting

### Code Processor (`code_processor/`)

```mermaid
flowchart LR
    Code[Source Code] --> PP[Preprocessor]
    PP --> AST[AST Parser]
    AST --> Extract[Extract Functions/Classes]
    Extract --> NL[NL Bridge Generator]
    NL --> |Summaries| Embed[Embeddings]
    Extract --> Analyze[Code Analyzer Agent]
    Analyze --> |Explanations| Embed
```

| Component | Purpose |
|-----------|---------|
| **CodePreprocessor** | Clean, normalize, extract structure from source files |
| **CodeAnalyzerAgent** | LLM-powered code explanation, complexity analysis |
| **NLBridgeGenerator** | Generate natural language descriptions for code search |

### Retrieval Pipeline (`retriever/`)

| Component | Technique |
|-----------|-----------|
| **QueryProcessor** | Query expansion, intent classification, keyword extraction |
| **HybridRetriever** | Combines dense (semantic) + sparse (BM25) retrieval |
| **Reranker** | Cross-encoder reranking using Cohere Rerank API |
| **ContextAssembler** | Dedupe, order, format retrieved chunks for LLM context |

---

## Content Generation Engine (`content_gen_engine/`)

### Content Generation Flow

```mermaid
flowchart TB
    Topic[Topic + Syllabus] --> Planner[Content Planner]
    Planner --> |Outline| TW[Theory Writer]
    Planner --> |Labs| CW[Code Writer]
    
    subgraph RAG["RAG Context"]
        R[Retrieved Chunks]
    end
    
    RAG --> TW
    RAG --> CW
    
    TW --> MG[Markdown Generator]
    TW --> DG[Diagram Generator]
    CW --> SC[Syntax Checker]
    SC --> CE[Code Executor]
    
    MG --> V[Content Validator]
    DG --> V
    CE --> V
    
    V --> Output[Theory + Labs + Diagrams]
```

### Agents (`agents/`)

| Agent | Role |
|-------|------|
| **ContentPlanner** | Create course outlines, learning objectives, module structure |
| **TheoryWriter** | Generate explanatory content with examples, analogies |
| **CodeWriter** | Generate executable code with comments, test cases |

### Validators (`validators/`)

| Validator | Purpose |
|-----------|---------|
| **SyntaxChecker** | AST validation for generated code (Python/JS/Java) |
| **CodeExecutor** | Sandbox execution, test runner, output verification |
| **ContentValidator** | Factual accuracy check via LLM grounding |

---

## Video Generation (`video_gen/`)

### Video Pipeline Architecture

```mermaid
flowchart LR
    subgraph Input
        T[Topic]
        C[RAG Context]
    end
    
    subgraph Agents
        T --> SW[Script Writer]
        C --> SW
        SW --> |Script| SP[Scene Planner]
    end
    
    subgraph Generators
        SP --> |Static| SR[Slide Renderer]
        SP --> |Animated| MG[Manim Generator]
        SP --> |Audio| TTS[TTS Engine]
    end
    
    subgraph Composition
        SR --> VC[Video Composer]
        MG --> VC
        TTS --> VC
        VC --> MP4[Final Video]
    end
```

### Manim Generation with Fix Loop

```mermaid
flowchart TB
    Desc[Scene Description] --> LLM[Gemini LLM]
    LLM --> |Code| Val{Syntax Valid?}
    Val --> |No| Fix[LLM Fix Code]
    Fix --> Val
    Val --> |Yes| Render[Manim Render]
    Render --> |Error| Fix
    Render --> |Success| Video[Animation MP4]
    
    Fix --> |3 Fails| Fallback[Static Slide]
```

### Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| **ScriptWriter** | Gemini structured output | Generate engaging narration scripts |
| **ScenePlanner** | Gemini + heuristics | Plan visual scenes (static/animated/code) |
| **SlideRenderer** | Pillow | Generate 1080p slide images |
| **ManimGenerator** | Manim CE + LLM | Mathematical/algorithmic animations |
| **TTSEngine** | Edge-TTS | Neural text-to-speech synthesis |
| **VideoComposer** | FFmpeg | Assemble slides, audio, animations |

---

## Tech Stack

| Category | Technologies |
|----------|-------------|
| **LLM** | Gemini 3 Pro, Cohere Rerank |
| **Embeddings** | Gemini Embeddings |
| **Vector DB** | ChromaDB, PGVector |
| **Document Processing** | PyMuPDF, python-pptx, tiktoken |
| **Video** | Manim CE, Edge-TTS, FFmpeg, Pillow |
| **API** | FastAPI, Pydantic, asyncio |
| **Code Analysis** | Python AST, tree-sitter |

---

## Quick Start

```bash
cd agents
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt

# Set environment
cp .env.example .env
# Add GOOGLE_API_KEY, COHERE_API_KEY

# Run
uvicorn main:app --reload
```

## Testing

```bash
python -m pytest tests/ -v
python -m tests.test_video_gen  # Video pipeline
```



