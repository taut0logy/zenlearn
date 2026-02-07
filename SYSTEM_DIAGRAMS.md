# ZenLearn System Diagrams

This document contains visual representations of the ZenLearn architecture.

## 1. Overall System Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                        Client Layer (Next.js)                      │
│  React Components • TypeScript • Tailwind • Shadcn UI             │
└───────────────────────────┬────────────────────────────────────────┘
                            │ HTTP/REST + SSE
                            ▼
┌────────────────────────────────────────────────────────────────────┐
│                    API Gateway (FastAPI)                           │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Middleware Stack                                            │ │
│  │  • CORS                                                      │ │
│  │  • Rate Limiting (SlowAPI + Redis)                          │ │
│  │  • Request ID Tracing                                       │ │
│  │  • Global Exception Handler                                 │ │
│  └──────────────────────────────────────────────────────────────┘ │
└───────────────────────────┬────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Chat Agent   │    │  CMS Agent   │    │ Community    │
│              │    │              │    │ Agent        │
│ /chat        │    │ /cms         │    │ /community   │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       │                   └───────┬───────────┘
       │                           │
       ▼                           ▼
┌──────────────────┐      ┌──────────────────┐
│   RAG Engine     │      │ Content Gen      │
│                  │◄─────┤ Engine           │
│ • Hybrid Search  │      │ • Theory Writer  │
│ • Reranking      │      │ • Code Writer    │
│ • Context Asm    │      │ • Video Gen      │
└────────┬─────────┘      └──────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│        Data Layer                           │
│  ┌──────────────┐      ┌─────────────────┐ │
│  │ PostgreSQL   │      │   ChromaDB      │ │
│  │              │      │                 │ │
│  │ • Users      │      │ • Embeddings    │ │
│  │ • Chats      │      │ • Memory        │ │
│  │ • Messages   │      │ • Documents     │ │
│  │ • Courses    │      │                 │ │
│  └──────────────┘      └─────────────────┘ │
│  ┌──────────────┐                          │
│  │   Redis      │                          │
│  │ • Rate Limit │                          │
│  │ • Cache      │                          │
│  └──────────────┘                          │
└─────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│        External Services                    │
│  • Google Gemini 2.5 Flash (LLM)           │
│  • Cohere (Embeddings + Rerank)            │
│  • Gemini Imagen (Image Generation)        │
└─────────────────────────────────────────────┘
```

## 2. Chat Agent State Machine (LangGraph)

```
                    ┌──────────────────┐
                    │   User Message   │
                    └────────┬─────────┘
                             │
                             ▼
            ┌────────────────────────────────┐
            │     Load Context               │
            │  • Chat history from DB        │
            │  • Relevant memories (Mem0)    │
            │  • System prompt              │
            └────────────┬───────────────────┘
                         │
                         ▼
            ┌────────────────────────────────┐
            │      Agent Node                │
            │  ┌──────────────────────────┐  │
            │  │  Gemini 2.5 Flash LLM    │  │
            │  │  with Tool Binding       │  │
            │  └──────────────────────────┘  │
            └────────────┬───────────────────┘
                         │
                         ▼
            ┌────────────────────────────────┐
            │    Decision Point              │
            │    Has Tool Calls?             │
            └────────┬───────────────────┬───┘
                     │                   │
                 Yes │                   │ No
                     │                   │
                     ▼                   ▼
        ┌────────────────────┐    ┌──────────────┐
        │   Tool Node        │    │  Response    │
        │                    │    │  to User     │
        │  Execute Tools:    │    └──────────────┘
        │  1. RAG Search     │
        │  2. Content Gen    │
        │  3. Code Gen       │
        │  4. Wikipedia      │
        │  5. Web Search     │
        └────────┬───────────┘
                 │
                 │ Tool Results
                 │
                 └──────────┐
                            │
                            ▼
            ┌───────────────────────────────┐
            │   Back to Agent Node          │
            │   (Process Tool Results)      │
            └───────────────────────────────┘
```

## 3. RAG Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                  STAGE 1: Query Processing                      │
├─────────────────────────────────────────────────────────────────┤
│  Input: "Explain quicksort algorithm"                           │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Intent Classifier                                          │ │
│  │ → Intent: CONCEPTUAL                                       │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Query Expander                                             │ │
│  │ → "quicksort", "quick sort", "sorting algorithm"          │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ HyDE Generator                                             │ │
│  │ → "Quicksort is a divide-and-conquer sorting..."          │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Filter Extractor                                           │ │
│  │ → course_id, content_type, etc.                           │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  STAGE 2: Hybrid Retrieval                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────┐  ┌────────────────────────────┐ │
│  │  Dense Retrieval          │  │  Sparse Retrieval          │ │
│  │  (Semantic)               │  │  (Keyword)                 │ │
│  │                           │  │                            │ │
│  │  1. Generate embedding    │  │  1. Tokenize query         │ │
│  │     Cohere API            │  │     + bigrams              │ │
│  │                           │  │                            │ │
│  │  2. Search ChromaDB       │  │  2. BM25 scoring           │ │
│  │     Cosine similarity     │  │     TF-IDF variant         │ │
│  │                           │  │                            │ │
│  │  3. Top-50 results        │  │  3. Top-50 results         │ │
│  │     Score: 0.85, 0.82...  │  │     Score: 12.5, 10.2...   │ │
│  └───────────────────────────┘  └────────────────────────────┘ │
│                    │                        │                   │
│                    └────────────┬───────────┘                   │
│                                 │                               │
│                    ┌────────────▼──────────┐                    │
│                    │  RRF Fusion           │                    │
│                    │  Score(doc) = Σ w_i / │                    │
│                    │             (k + r_i) │                    │
│                    │  Top-30 results       │                    │
│                    └───────────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   STAGE 3: Reranking                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Cohere Rerank v3.5 API                                     │ │
│  │                                                            │ │
│  │ Query: "Explain quicksort algorithm"                       │ │
│  │                                                            │ │
│  │ Documents: [30 chunks with metadata]                       │ │
│  │                                                            │ │
│  │ → Cross-encoder scores:                                    │ │
│  │   Doc 1: 0.92 ✓                                           │ │
│  │   Doc 2: 0.88 ✓                                           │ │
│  │   Doc 3: 0.85 ✓                                           │ │
│  │   ...                                                      │ │
│  │   Doc 15: 0.18 ✗ (below threshold 0.2)                   │ │
│  │                                                            │ │
│  │ Output: Top-10 most relevant                              │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 STAGE 4: Context Assembly                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Format Results                                             │ │
│  │                                                            │ │
│  │ Context:                                                   │ │
│  │                                                            │ │
│  │ [1] Quicksort Algorithm (slides.pptx, Slide 12)           │ │
│  │ Quicksort is a divide-and-conquer algorithm that works     │ │
│  │ by selecting a 'pivot' element...                          │ │
│  │                                                            │ │
│  │ [2] Quicksort Implementation (lab3.py, lines 45-67)        │ │
│  │ ```python                                                  │ │
│  │ def quicksort(arr):                                        │ │
│  │     if len(arr) <= 1: return arr                           │ │
│  │     ...                                                    │ │
│  │ ```                                                        │ │
│  │                                                            │ │
│  │ [3] Complexity Analysis (lecture_notes.pdf, page 23)       │ │
│  │ Time Complexity: O(n log n) average case...                │ │
│  │                                                            │ │
│  │ → Send to LLM for response generation                     │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 4. Document Ingestion Pipeline

```
┌────────────────┐
│  File Upload   │
│  via CMS API   │
└───────┬────────┘
        │
        ▼
┌──────────────────────────────────────────┐
│  File Type Detection                     │
│  ┌────────────────────────────────────┐  │
│  │ .pdf    → PDFChunker              │  │
│  │ .pptx   → SlideChunker            │  │
│  │ .py     → CodeChunker             │  │
│  │ .txt    → TextChunker             │  │
│  └────────────────────────────────────┘  │
└───────┬──────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────┐
│  Content Extraction                      │
│  ┌────────────────────────────────────┐  │
│  │ PDF:  PyMuPDF (text + layout)     │  │
│  │ PPTX: python-pptx (text + notes)  │  │
│  │ Code: AST parsing                 │  │
│  │ Text: Direct reading              │  │
│  └────────────────────────────────────┘  │
└───────┬──────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────┐
│  Intelligent Chunking                    │
│  ┌────────────────────────────────────┐  │
│  │ PDF:  Paragraph boundaries        │  │
│  │       300-800 tokens              │  │
│  │       50 token overlap            │  │
│  │                                   │  │
│  │ PPTX: Per-slide chunking          │  │
│  │       Merge if < 200 tokens       │  │
│  │                                   │  │
│  │ Code: Function/class level        │  │
│  │       Include docstrings          │  │
│  │                                   │  │
│  │ Text: Fixed-size windows          │  │
│  │       With overlap                │  │
│  └────────────────────────────────────┘  │
└───────┬──────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────┐
│  Metadata Enrichment                     │
│  ┌────────────────────────────────────┐  │
│  │ LLM-powered:                      │  │
│  │ • Auto-generate summary           │  │
│  │ • Extract keywords                │  │
│  │ • Identify topics                 │  │
│  │ • Generate NL queries (for code)  │  │
│  │                                   │  │
│  │ Structural:                       │  │
│  │ • course_id, material_id          │  │
│  │ • page/slide/line numbers         │  │
│  │ • content_type, chunk_type        │  │
│  └────────────────────────────────────┘  │
└───────┬──────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────┐
│  Embedding Generation                    │
│  ┌────────────────────────────────────┐  │
│  │ Cohere embed-english-v3.0         │  │
│  │ • 1024-dimensional vectors        │  │
│  │ • Batch processing (50 at a time) │  │
│  │ • Input type: "search_document"   │  │
│  └────────────────────────────────────┘  │
└───────┬──────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────┐
│  Dual Storage                            │
│  ┌──────────────┐  ┌─────────────────┐  │
│  │  ChromaDB    │  │  BM25 Index     │  │
│  │              │  │                 │  │
│  │ • Vector     │  │ • In-memory     │  │
│  │   search     │  │ • Tokenized     │  │
│  │ • Metadata   │  │ • TF-IDF stats  │  │
│  │   filtering  │  │                 │  │
│  └──────────────┘  └─────────────────┘  │
└──────────────────────────────────────────┘
```

## 5. Content Generation Pipeline

```
┌──────────────────┐
│  User Request    │
│  "Create notes   │
│   on quicksort"  │
└────────┬─────────┘
         │
         ▼
┌────────────────────────────────────────────┐
│  PHASE 1: Planning                         │
│  ┌──────────────────────────────────────┐  │
│  │ Content Planner Agent                │  │
│  │                                      │  │
│  │ Input: Topic + RAG context          │  │
│  │                                      │  │
│  │ Output:                              │  │
│  │ • Hierarchical outline               │  │
│  │ • Section objectives                 │  │
│  │ • Diagram requirements               │  │
│  │ • Code example specs                 │  │
│  └──────────────────────────────────────┘  │
└────────┬───────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────┐
│  PHASE 2: Content Writing                  │
│  ┌──────────────────────────────────────┐  │
│  │ Theory Writer Agent                  │  │
│  │                                      │  │
│  │ For each section:                    │  │
│  │ • Generate explanation text          │  │
│  │ • Add examples                       │  │
│  │ • Create exercises                   │  │
│  │ • Link to prior concepts             │  │
│  │                                      │  │
│  │ Uses: Gemini + RAG context           │  │
│  └──────────────────────────────────────┘  │
│  ┌──────────────────────────────────────┐  │
│  │ Code Writer Agent                    │  │
│  │                                      │  │
│  │ • Generate implementation code       │  │
│  │ • Create starter templates           │  │
│  │ • Write test cases                   │  │
│  │ • Add inline comments                │  │
│  └──────────────────────────────────────┘  │
└────────┬───────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────┐
│  PHASE 3: Asset Generation                 │
│  ┌──────────────────────────────────────┐  │
│  │ Diagram Generator (Mermaid)          │  │
│  │ • Flowcharts                         │  │
│  │ • Sequence diagrams                  │  │
│  │ • Class diagrams                     │  │
│  └──────────────────────────────────────┘  │
│  ┌──────────────────────────────────────┐  │
│  │ Image Generator (Gemini Imagen)      │  │
│  │ • Conceptual illustrations           │  │
│  │ • Algorithm visualizations           │  │
│  └──────────────────────────────────────┘  │
└────────┬───────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────┐
│  PHASE 4: Validation                       │
│  ┌──────────────────────────────────────┐  │
│  │ Syntax Checker                       │  │
│  │ • AST parsing                        │  │
│  │ • Compile-time checks                │  │
│  └──────────────────────────────────────┘  │
│  ┌──────────────────────────────────────┐  │
│  │ Code Executor (Sandbox)              │  │
│  │ • Run unit tests                     │  │
│  │ • Check outputs                      │  │
│  │ • Isolated environment               │  │
│  └──────────────────────────────────────┘  │
│  ┌──────────────────────────────────────┐  │
│  │ Content Validator                    │  │
│  │ • Fact checking vs RAG context       │  │
│  │ • Coherence checking                 │  │
│  └──────────────────────────────────────┘  │
└────────┬───────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────┐
│  PHASE 5: Output Generation                │
│  ┌──────────────────────────────────────┐  │
│  │ Markdown Generator (always)          │  │
│  └──────────────────────────────────────┘  │
│  ┌──────────────────────────────────────┐  │
│  │ PDF Generator (optional)             │  │
│  │ • markdown → HTML → PDF              │  │
│  │ • xhtml2pdf                          │  │
│  └──────────────────────────────────────┘  │
│  ┌──────────────────────────────────────┐  │
│  │ Video Generator (optional)           │  │
│  │ • Script → Scenes → Assets → Render  │  │
│  │ • Manim + TTS + FFmpeg               │  │
│  └──────────────────────────────────────┘  │
└────────────────────────────────────────────┘
```

## 6. Memory System Architecture (Mem0)

```
┌─────────────────────────────────────────┐
│        Conversation Turn                │
│  User: "I prefer Python over C++"       │
│  Assistant: "Got it! I'll use Python..."│
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────┐
│    Memory Extraction (Gemini LLM)        │
│  ┌────────────────────────────────────┐  │
│  │ Analyze conversation for:          │  │
│  │ • User preferences                 │  │
│  │ • Facts about user knowledge       │  │
│  │ • Learning patterns                │  │
│  │ • Context to remember              │  │
│  └────────────────────────────────────┘  │
│                                          │
│  Extracted:                              │
│  {                                       │
│    "type": "preference",                 │
│    "content": "User prefers Python",     │
│    "context": "programming language"     │
│  }                                       │
└──────────────────┬───────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────┐
│    Embedding + Storage                   │
│  ┌────────────────────────────────────┐  │
│  │ Cohere Embeddings                  │  │
│  │ • Convert memory to vector         │  │
│  └────────────────────────────────────┘  │
│  ┌────────────────────────────────────┐  │
│  │ ChromaDB (mem0_chat_memories)      │  │
│  │ • Store vector + metadata          │  │
│  │ • Index: user_id, chat_id, type    │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘

Later Query: "Show me a sorting example"
                   │
                   ▼
┌──────────────────────────────────────────┐
│    Memory Retrieval                      │
│  ┌────────────────────────────────────┐  │
│  │ 1. Embed query                     │  │
│  │ 2. Search mem0 collection          │  │
│  │ 3. Filter by user_id               │  │
│  │ 4. Top-k relevant memories         │  │
│  └────────────────────────────────────┘  │
│                                          │
│  Retrieved:                              │
│  • "User prefers Python"                 │
│  • "User is learning sorting algorithms" │
│  • "User struggled with recursion"       │
└──────────────────┬───────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────┐
│    Context Assembly                      │
│  System Prompt:                          │
│  "You are helping a student who:         │
│   - Prefers Python                       │
│   - Is learning sorting                  │
│   - May need extra help with recursion   │
│   ...provide Python sorting example..."  │
└──────────────────────────────────────────┘
```

## 7. Deployment Architecture

```
┌────────────────────────────────────────────────────┐
│              Internet / Load Balancer              │
└────────────────────┬───────────────────────────────┘
                     │
         ┌───────────┴──────────┐
         │                      │
         ▼                      ▼
┌─────────────────┐    ┌─────────────────┐
│  Next.js Client │    │  FastAPI Agent  │
│  (Port 3000)    │    │  (Port 8000)    │
│                 │    │                 │
│  • React        │    │  • Multiple     │
│  • TypeScript   │    │    instances    │
│  • Tailwind     │    │  • Load balanced│
└─────────────────┘    └────────┬────────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
                    ▼           ▼           ▼
         ┌──────────────┐ ┌──────────┐ ┌──────────┐
         │  PostgreSQL  │ │ ChromaDB │ │  Redis   │
         │              │ │          │ │          │
         │ • Primary DB │ │ • Vectors│ │ • Cache  │
         │ • Read       │ │ • Memory │ │ • Rate   │
         │   replicas   │ │          │ │   limit  │
         └──────────────┘ └──────────┘ └──────────┘
                    │
                    ▼
         ┌──────────────────────────┐
         │   External AI Services   │
         │  • Google Gemini         │
         │  • Cohere                │
         └──────────────────────────┘

Docker Compose Stack:
┌────────────────────────────────────────┐
│  docker-compose.yml                    │
│  ┌──────────────────────────────────┐  │
│  │ services:                        │  │
│  │   agents:                        │  │
│  │     build: ./agents              │  │
│  │     ports: 8000:8000             │  │
│  │     depends_on: [redis]          │  │
│  │                                  │  │
│  │   client:                        │  │
│  │     build: ./client              │  │
│  │     ports: 3000:3000             │  │
│  │                                  │  │
│  │   redis:                         │  │
│  │     image: redis:7-alpine        │  │
│  │     ports: 6379:6379             │  │
│  │     volumes: redis_data:/data    │  │
│  └──────────────────────────────────┘  │
└────────────────────────────────────────┘
```

---

## Legend

- **→** : Data flow
- **▼** : Process flow
- **◄─** : Feedback / Return
- **├─** : Branch / Option
- **✓** : Success / Pass
- **✗** : Failure / Reject

---

**Generated:** February 7, 2026  
**Repository:** taut0logy/zenlearn
