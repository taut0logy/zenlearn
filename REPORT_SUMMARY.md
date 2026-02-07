# ZenLearn Architecture Report - Executive Summary

## 📊 Project Overview

**ZenLearn** is a production-grade AI-powered supplementary learning platform built for university students. The system consists of:

1. **Intelligent Chatbot** - LangGraph-based conversational agent with tool-calling
2. **Hybrid RAG Pipeline** - 3-stage retrieval system (semantic + keyword + reranking)
3. **Content Generation Engine** - Multi-agent system for creating educational materials
4. **Video Generation** - Automated educational video synthesis

---

## 🏗️ Architecture Highlights

### Technology Stack
- **Backend:** FastAPI + Python 3.10+
- **LLM:** Google Gemini 2.5 Flash
- **Embeddings:** Cohere embed-english-v3.0 (1024-dim)
- **Vector Store:** ChromaDB
- **Database:** PostgreSQL + pgvector
- **Agent Framework:** LangGraph + LangChain
- **Memory:** Mem0 with ChromaDB

### Key Metrics
- **114 Python files** in backend
- **~1.0 MB** backend codebase
- **223 total files** (Python + TypeScript)
- **5 specialized tools** for chatbot
- **4-stage RAG pipeline**

---

## 💬 Chatbot Architecture

### Core Components
```
LangGraph Agent → Tools → Memory → Database
     ↓              ↓        ↓         ↓
   Gemini    Course Search  Mem0    PostgreSQL
   2.5 Flash    (RAG)      (ChromaDB)
```

### Agent Tools (Priority Order)
1. **course_materials_search** - RAG integration (PRIMARY)
2. **content_gen_tool** - Generate learning materials
3. **generate_validated_code** - Code generation with validation
4. **wikipedia_tool** - External knowledge base
5. **duckduckgo_search** - Web search fallback

### Key Features
✅ **Streaming Responses** - Server-Sent Events (SSE)  
✅ **Conversation Memory** - Mem0-based context retention  
✅ **Tool Calling** - Structured multi-step workflows  
✅ **Rate Limiting** - 100 req/min (Redis-backed)  
✅ **Request Tracing** - UUID-based debugging  

---

## 🔍 RAG Pipeline Architecture

### 4-Stage Retrieval Process

```
1. Query Processing
   ├─ Intent classification (7 types)
   ├─ Query expansion (synonyms, related terms)
   ├─ HyDE (hypothetical document generation)
   └─ Filter extraction (course_id, content_type, etc.)

2. Hybrid Retrieval
   ├─ Dense (Semantic): Cohere embeddings + ChromaDB
   └─ Sparse (Keyword): Custom BM25 with bigrams

3. RRF Fusion
   └─ Reciprocal Rank Fusion combines results

4. Reranking
   └─ Cohere Rerank v3.5 (cross-encoder)
```

### Chunking Strategies

| Type | Strategy | Tool | Chunk Size |
|------|----------|------|------------|
| **PDF** | Semantic paragraphs | PyMuPDF | 300-800 tokens |
| **Slides** | Slide-aware | python-pptx | Per slide |
| **Code** | AST-based | Python ast | Per function/class |
| **Text** | Overlap splitting | Custom | 400-600 tokens |

### Metadata Enrichment
- Auto-generated summaries
- Keyword extraction
- Natural language query generation
- Topic categorization
- Structure preservation (page/slide/function context)

---

## 📦 System Architecture

```
┌─────────────────────────────────────────┐
│         FastAPI Backend (main.py)       │
│  • CORS, Rate Limiting, Tracing         │
└────┬────────────────────────────────────┘
     │
     ├─────────────────┬──────────────────┐
     │                 │                  │
┌────▼─────┐   ┌──────▼──────┐   ┌──────▼───────┐
│  Chat    │   │   CMS       │   │  Community   │
│  Agent   │   │   Agent     │   │  Agent       │
└────┬─────┘   └──────┬──────┘   └──────┬───────┘
     │                │                  │
     └────────────────┴──────────────────┘
                      │
          ┌───────────┴──────────┐
          │                      │
     ┌────▼─────┐        ┌──────▼────────┐
     │   RAG    │        │   Content     │
     │  Engine  │◄───────┤   Generation  │
     └──────────┘        └───────────────┘
```

---

## 💾 Database Schema

### PostgreSQL Tables
- **users** - User accounts
- **chats** - Chat sessions
- **messages** - Chat messages with feedback
- **courses** - Course information
- **materials** - Uploaded course files
- **posts** - Q&A forum posts
- **replies** - Forum replies (including AI-generated)

### ChromaDB Collections
- **zenlearn** - Main document embeddings (~10M vector capacity)
- **mem0_chat_memories** - Conversation memory

---

## 🎯 Content Generation Pipeline

```
Planning → Writing → Asset Gen → Validation → Output
   ↓         ↓          ↓           ↓          ↓
Planner   Theory    Diagrams    Syntax     Markdown
Agent     Writer    (Mermaid)   Check      PDF
          Code      Images      Execute    Video
          Writer    (Gemini)    Tests
```

### Capabilities
- **Theory Notes** - Explanatory text with examples
- **Coding Labs** - Exercises with starter code + tests
- **Educational Videos** - Manim animations + TTS + FFmpeg

---

## 📈 Performance Characteristics

| Operation | Average Latency | Notes |
|-----------|----------------|-------|
| Chat message | 2-4s | With RAG search |
| RAG search | 800ms | Full pipeline, 5 results |
| Embedding | 50ms | Per document (Cohere) |
| Reranking | 200ms | 30 documents (Cohere) |
| Content generation | 30-60s | 5-page document |

---

## ✅ Strengths

1. **🏛️ Clean Architecture**
   - Modular design with clear separation
   - Dependency injection pattern
   - Factory pattern for services

2. **🔍 Advanced RAG**
   - Hybrid retrieval (dense + sparse)
   - Cross-encoder reranking
   - Intent-aware processing
   - Metadata-rich chunking

3. **🤖 Sophisticated Agent**
   - LangGraph structured workflows
   - Multiple specialized tools
   - Conversation memory
   - Streaming responses

4. **🎓 Content Generation**
   - Multi-agent validation
   - Code execution sandbox
   - Automated asset creation

---

## ⚠️ Weaknesses & Recommendations

### Current Limitations

1. **Scalability**
   - ❌ Single ChromaDB instance (not clustered)
   - ❌ In-memory BM25 per instance
   - ❌ No horizontal scaling strategy

2. **Security**
   - ❌ JWT auth incomplete
   - ❌ No secrets rotation
   - ❌ Missing API key management

3. **Testing**
   - ❌ No visible test suite
   - ❌ Missing integration tests
   - ❌ No load testing

4. **Observability**
   - ❌ No metrics (Prometheus)
   - ❌ No distributed tracing
   - ❌ Limited alerting

### Recommended Improvements

#### Short-term (1-3 months)
1. **Add comprehensive test suite** (unit, integration, E2E)
2. **Complete JWT authentication** with refresh tokens
3. **Implement observability** (Prometheus, Sentry, Jaeger)
4. **Add API documentation** beyond OpenAPI

#### Long-term (3-6 months)
1. **Scale vector store** - ChromaDB cluster or migrate to Pinecone
2. **Implement sharding** - By course_id for isolation
3. **Add caching layer** - Redis cluster for distributed caching
4. **Enhance RAG** - Graph-based retrieval, multi-hop reasoning
5. **Multi-modal support** - Image and diagram search

---

## 🎯 Production Readiness

### Current Status
✅ **Ready for pilot deployment** (< 10,000 users)  
⚠️ **Requires hardening** for production scale (> 10,000 users)

### Deployment Checklist
- [x] Docker containerization
- [x] Health checks
- [x] Rate limiting
- [x] Error handling
- [ ] JWT authentication (partial)
- [ ] Secrets management
- [ ] Horizontal scaling config
- [ ] Monitoring & alerting
- [ ] Load balancer setup
- [ ] Database read replicas

---

## 📚 Documentation

### Reports Generated
1. **ARCHITECTURAL_REPORT.md** - Complete technical deep-dive (1100+ lines)
   - Full architecture diagrams
   - Code examples
   - Performance benchmarks
   - Security analysis
   - Deployment guide

2. **REPORT_SUMMARY.md** - This executive summary

### Key Sections in Full Report
- System Architecture Overview
- Chatbot Architecture (LangGraph, Memory, Tools)
- RAG Pipeline (Chunking, Retrieval, Reranking)
- Content Generation Engine
- Database Schema
- Engineering Practices
- Performance Characteristics
- Recommendations

---

## 🚀 Next Steps

1. **Review the full report** - See `ARCHITECTURAL_REPORT.md`
2. **Prioritize improvements** - Focus on security and testing first
3. **Plan scaling strategy** - Before hitting 10K users
4. **Add monitoring** - Essential for production operations
5. **Document deployment** - Create runbooks and playbooks

---

## 📞 Contact

**Team:** ZenBit  
**Repository:** https://github.com/taut0logy/zenlearn  
**Report Date:** February 7, 2026

---

**Note:** This report is based on static code analysis as of February 2026. Performance metrics are estimates based on typical usage patterns. Actual production performance may vary based on workload and infrastructure.
