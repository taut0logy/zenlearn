# 🔪 Chunking Strategies - Intelligent Content Segmentation

> **Goal**: Create semantically coherent, context-rich chunks optimized for retrieval  
> **Key Insight**: "Chunk by meaning, not by size"

---

## 📋 Table of Contents

1. [Chunking Philosophy](#chunking-philosophy)
2. [Content-Aware Chunking Decision Tree](#content-aware-chunking-decision-tree)
3. [Slide (PPTX) Chunking](#slide-pptx-chunking)
4. [PDF Document Chunking](#pdf-document-chunking)
5. [Code (AST-Based) Chunking](#code-ast-based-chunking)
6. [Context Enrichment Strategies](#context-enrichment-strategies)
7. [Chunk Size Optimization](#chunk-size-optimization)

---

## 🎯 Chunking Philosophy

### The Fundamental Tradeoff

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      CHUNKING TRADEOFFS                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  SMALL CHUNKS                        LARGE CHUNKS                       │
│  ├─ ✅ Precise matching              ├─ ✅ Rich context                 │
│  ├─ ✅ Less noise                    ├─ ✅ Coherent answers             │
│  ├─ ❌ Lost context                  ├─ ❌ Diluted relevance            │
│  └─ ❌ Fragmented answers            └─ ❌ May miss specific info       │
│                                                                         │
│                    OPTIMAL: Content-Aware Semantic Chunking             │
│                    ─────────────────────────────────────                │
│                    Chunk by meaning, preserve context,                  │
│                    enrich with surrounding information                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Core Principles

1. **Semantic Coherence**: Each chunk should express a complete thought
2. **Context Preservation**: Include enough surrounding context
3. **Retrieval Optimization**: Optimize for how users will search
4. **Citation Accuracy**: Maintain precise source mapping

---

## 🌳 Content-Aware Chunking Decision Tree

```
                              ┌─────────────────┐
                              │  Content Type?  │
                              └────────┬────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              │                        │                        │
              ▼                        ▼                        ▼
       ┌────────────┐          ┌────────────┐          ┌────────────┐
       │   SLIDES   │          │    PDF     │          │    CODE    │
       │   (PPTX)   │          │            │          │            │
       └─────┬──────┘          └─────┬──────┘          └─────┬──────┘
             │                       │                       │
             ▼                       ▼                       ▼
    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
    │ Slide-Aware     │    │ Section-Aware   │    │ AST-Based       │
    │ Chunking        │    │ Chunking        │    │ Chunking        │
    │                 │    │                 │    │                 │
    │ • 1 slide = 1   │    │ • Headings as   │    │ • Functions     │
    │   base chunk    │    │   boundaries    │    │ • Classes       │
    │ • Merge small   │    │ • Paragraph     │    │ • Logical       │
    │   slides        │    │   grouping      │    │   blocks        │
    │ • Split large   │    │ • Semantic      │    │ • With context  │
    │   slides        │    │   similarity    │    │   window        │
    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 📊 Slide (PPTX) Chunking

### Strategy: Slide-Aware Semantic Chunking

Slides have natural boundaries but vary wildly in content density.

### Chunking Rules

```python
class SlideChunkingStrategy:
    """
    Intelligent slide chunking with context preservation.
    """
    
    # ═══════════════════════════════════════════════════════════════
    # CONFIGURATION
    # ═══════════════════════════════════════════════════════════════
    
    MIN_CHUNK_TOKENS = 100      # Minimum viable chunk
    MAX_CHUNK_TOKENS = 800      # Maximum for embedding quality
    TARGET_CHUNK_TOKENS = 400   # Ideal chunk size
    OVERLAP_TOKENS = 50         # Context overlap
    
    # ═══════════════════════════════════════════════════════════════
    # SLIDE TYPE HANDLING
    # ═══════════════════════════════════════════════════════════════
    
    CHUNKING_RULES = {
        "title": "merge_with_next",       # Title slides merge with intro
        "section_header": "standalone",    # Section headers standalone
        "content": "smart_chunk",          # Main content - smart handling
        "code_slide": "code_aware",        # Code slides - preserve code blocks
        "summary": "standalone",           # Summary slides standalone
        "references": "skip_or_meta"       # References → metadata only
    }
```

### Slide Chunking Algorithm

```python
from dataclasses import dataclass
from typing import List, Optional
import tiktoken

@dataclass
class SlideContent:
    slide_number: int
    title: str
    body_text: str
    speaker_notes: Optional[str]
    slide_type: str
    has_code: bool
    image_descriptions: List[str]

@dataclass  
class Chunk:
    content: str
    metadata: dict
    token_count: int


def chunk_presentation(slides: List[SlideContent]) -> List[Chunk]:
    """
    Chunk a presentation with slide-awareness.
    
    Strategy:
    1. Process slides in order
    2. Merge small adjacent slides of same topic
    3. Split large slides at semantic boundaries
    4. Preserve code blocks intact
    5. Include speaker notes as context
    """
    
    chunks = []
    buffer = []
    buffer_tokens = 0
    current_section = None
    
    encoder = tiktoken.get_encoding("cl100k_base")
    
    for i, slide in enumerate(slides):
        slide_text = format_slide_content(slide)
        slide_tokens = len(encoder.encode(slide_text))
        
        # ─────────────────────────────────────────────────────────
        # RULE 1: Skip reference/bibliography slides
        # ─────────────────────────────────────────────────────────
        if slide.slide_type == "references":
            continue
        
        # ─────────────────────────────────────────────────────────
        # RULE 2: Section headers start new sections
        # ─────────────────────────────────────────────────────────
        if slide.slide_type == "section_header":
            # Flush buffer
            if buffer:
                chunks.append(create_chunk(buffer, current_section))
                buffer = []
                buffer_tokens = 0
            
            current_section = slide.title
            # Section headers can be their own chunk or merge with next
            if slide_tokens >= MIN_CHUNK_TOKENS:
                chunks.append(create_chunk([slide], current_section))
            else:
                buffer.append(slide)
                buffer_tokens = slide_tokens
            continue
        
        # ─────────────────────────────────────────────────────────
        # RULE 3: Code slides stay intact
        # ─────────────────────────────────────────────────────────
        if slide.has_code:
            # Flush non-code buffer
            if buffer and not any(s.has_code for s in buffer):
                chunks.append(create_chunk(buffer, current_section))
                buffer = []
                buffer_tokens = 0
            
            # Code slides get their own chunk (preserve code integrity)
            if slide_tokens > MAX_CHUNK_TOKENS:
                # Large code slide - chunk by code blocks
                code_chunks = chunk_code_slide(slide)
                chunks.extend(code_chunks)
            else:
                chunks.append(create_chunk([slide], current_section))
            continue
        
        # ─────────────────────────────────────────────────────────
        # RULE 4: Regular content - buffer and merge
        # ─────────────────────────────────────────────────────────
        if buffer_tokens + slide_tokens <= MAX_CHUNK_TOKENS:
            # Add to buffer
            buffer.append(slide)
            buffer_tokens += slide_tokens
        else:
            # Flush buffer and start new
            if buffer:
                chunks.append(create_chunk(buffer, current_section))
            
            if slide_tokens > MAX_CHUNK_TOKENS:
                # Large slide - split semantically
                split_chunks = split_large_slide(slide)
                chunks.extend(split_chunks)
                buffer = []
                buffer_tokens = 0
            else:
                buffer = [slide]
                buffer_tokens = slide_tokens
    
    # Don't forget the last buffer
    if buffer:
        chunks.append(create_chunk(buffer, current_section))
    
    return chunks


def format_slide_content(slide: SlideContent) -> str:
    """
    Format slide for embedding with rich context.
    """
    parts = []
    
    # Title with slide number for citation
    parts.append(f"## Slide {slide.slide_number}: {slide.title}")
    
    # Body text
    if slide.body_text:
        parts.append(slide.body_text)
    
    # Image descriptions (valuable for search!)
    if slide.image_descriptions:
        parts.append("\n[Visual content:]")
        for desc in slide.image_descriptions:
            parts.append(f"- {desc}")
    
    # Speaker notes (often contain the real explanation)
    if slide.speaker_notes:
        parts.append(f"\n[Speaker notes:]\n{slide.speaker_notes}")
    
    return "\n\n".join(parts)


def create_chunk(
    slides: List[SlideContent], 
    section: Optional[str]
) -> Chunk:
    """
    Create a chunk from one or more slides with full metadata.
    """
    content = "\n\n---\n\n".join(
        format_slide_content(s) for s in slides
    )
    
    # Determine slide range for citation
    if len(slides) == 1:
        slide_ref = f"Slide {slides[0].slide_number}"
    else:
        slide_ref = f"Slides {slides[0].slide_number}-{slides[-1].slide_number}"
    
    metadata = {
        "chunk_type": "slides",
        "slide_numbers": [s.slide_number for s in slides],
        "slide_range": slide_ref,
        "section": section,
        "titles": [s.title for s in slides if s.title],
        "has_code": any(s.has_code for s in slides),
        "has_images": any(s.image_descriptions for s in slides),
    }
    
    encoder = tiktoken.get_encoding("cl100k_base")
    
    return Chunk(
        content=content,
        metadata=metadata,
        token_count=len(encoder.encode(content))
    )
```

### Slide Chunking Visualization

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SLIDE CHUNKING EXAMPLE                               │
└─────────────────────────────────────────────────────────────────────────┘

Original Slides:
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│ S1   │ │ S2   │ │ S3   │ │ S4   │ │ S5   │ │ S6   │ │ S7   │
│Title │ │Intro │ │Topic │ │Detail│ │CODE  │ │More  │ │Summary│
│ 50t  │ │ 80t  │ │ 200t │ │ 250t │ │ 400t │ │ 150t │ │ 180t │
└──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘

After Chunking:
┌─────────────────────┐ ┌─────────────────────┐ ┌──────┐ ┌────────────────┐
│      CHUNK 1        │ │      CHUNK 2        │ │CHUNK3│ │    CHUNK 4     │
│  S1 + S2 merged     │ │  S3 + S4 merged     │ │ S5   │ │  S6 + S7       │
│  (small slides)     │ │  (same topic)       │ │ CODE │ │  merged        │
│      130 tokens     │ │     450 tokens      │ │ 400t │ │   330 tokens   │
└─────────────────────┘ └─────────────────────┘ └──────┘ └────────────────┘
                                                   │
                                          Code preserved intact!
```

---

## 📄 PDF Document Chunking

### Strategy: Section-Aware Semantic Chunking

```python
class PDFChunkingStrategy:
    """
    PDF chunking that respects document structure.
    """
    
    # ═══════════════════════════════════════════════════════════════
    # CONFIGURATION
    # ═══════════════════════════════════════════════════════════════
    
    MIN_CHUNK_TOKENS = 150
    MAX_CHUNK_TOKENS = 1000
    TARGET_CHUNK_TOKENS = 500
    OVERLAP_SENTENCES = 2       # Sentence overlap for context
    
    # ═══════════════════════════════════════════════════════════════
    # HIERARCHY DETECTION
    # ═══════════════════════════════════════════════════════════════
    
    # Headers are natural chunk boundaries
    HEADER_PATTERNS = [
        r'^#{1,6}\s+',           # Markdown headers
        r'^\d+\.\d*\s+[A-Z]',    # Numbered sections (1.2 Introduction)
        r'^Chapter\s+\d+',       # Chapter markers
        r'^[A-Z][^.!?]*:$',      # Title-case lines ending with colon
    ]
```

### PDF Chunking Algorithm

```python
from dataclasses import dataclass
from typing import List, Tuple
import re

@dataclass
class PDFPage:
    page_number: int
    text: str
    headers: List[Tuple[int, str]]  # (level, text)


def chunk_pdf(pages: List[PDFPage]) -> List[Chunk]:
    """
    Chunk PDF with section awareness and page tracking.
    
    Strategy:
    1. Detect section boundaries via headers
    2. Chunk within sections using semantic similarity
    3. Track page numbers for precise citations
    4. Add sentence overlap for context continuity
    """
    
    # First pass: identify all sections
    sections = identify_sections(pages)
    
    chunks = []
    
    for section in sections:
        section_chunks = chunk_section(
            text=section.text,
            page_range=section.page_range,
            section_title=section.title,
            parent_sections=section.breadcrumb
        )
        chunks.extend(section_chunks)
    
    # Add overlap between adjacent chunks
    chunks = add_context_overlap(chunks)
    
    return chunks


def chunk_section(
    text: str,
    page_range: Tuple[int, int],
    section_title: str,
    parent_sections: List[str]
) -> List[Chunk]:
    """
    Chunk a section using semantic similarity.
    
    Uses embedding similarity to find natural break points.
    """
    
    # Split into sentences
    sentences = split_into_sentences(text)
    
    if not sentences:
        return []
    
    # For small sections, keep as single chunk
    total_tokens = count_tokens(" ".join(sentences))
    if total_tokens <= MAX_CHUNK_TOKENS:
        return [Chunk(
            content=format_section_chunk(
                text, section_title, parent_sections
            ),
            metadata={
                "chunk_type": "text",
                "page_start": page_range[0],
                "page_end": page_range[1],
                "section": section_title,
                "breadcrumb": parent_sections,
            },
            token_count=total_tokens
        )]
    
    # For larger sections, use semantic chunking
    return semantic_chunk_text(
        sentences=sentences,
        page_range=page_range,
        section_title=section_title,
        parent_sections=parent_sections
    )


def semantic_chunk_text(
    sentences: List[str],
    page_range: Tuple[int, int],
    section_title: str,
    parent_sections: List[str]
) -> List[Chunk]:
    """
    Chunk text using semantic similarity between sentences.
    
    Algorithm (Max-Min Semantic Chunking):
    1. Embed all sentences
    2. Compute similarity between adjacent sentences  
    3. Find valleys (low similarity = topic change)
    4. Split at valleys while respecting size limits
    """
    
    from sentence_transformers import SentenceTransformer
    import numpy as np
    
    # Use a lightweight model for chunking decisions
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Embed sentences
    embeddings = model.encode(sentences)
    
    # Compute similarity between adjacent sentences
    similarities = []
    for i in range(len(embeddings) - 1):
        sim = np.dot(embeddings[i], embeddings[i + 1])
        similarities.append(sim)
    
    # Find split points (local minima in similarity)
    split_points = find_split_points(
        similarities=similarities,
        sentences=sentences,
        min_tokens=MIN_CHUNK_TOKENS,
        max_tokens=MAX_CHUNK_TOKENS
    )
    
    # Create chunks at split points
    chunks = []
    start_idx = 0
    
    for split_idx in split_points + [len(sentences)]:
        chunk_sentences = sentences[start_idx:split_idx]
        chunk_text = " ".join(chunk_sentences)
        
        chunks.append(Chunk(
            content=format_section_chunk(
                chunk_text, section_title, parent_sections
            ),
            metadata={
                "chunk_type": "text",
                "page_start": page_range[0],
                "page_end": page_range[1],
                "section": section_title,
                "breadcrumb": parent_sections,
                "sentence_range": (start_idx, split_idx),
            },
            token_count=count_tokens(chunk_text)
        ))
        
        start_idx = split_idx
    
    return chunks


def find_split_points(
    similarities: List[float],
    sentences: List[str],
    min_tokens: int,
    max_tokens: int
) -> List[int]:
    """
    Find optimal split points based on semantic valleys
    while respecting token limits.
    """
    
    split_points = []
    current_tokens = 0
    last_split = 0
    
    for i, sentence in enumerate(sentences):
        sent_tokens = count_tokens(sentence)
        
        if current_tokens + sent_tokens > max_tokens:
            # Must split - find best point since last split
            if i > last_split:
                # Find lowest similarity in valid range
                valid_range = similarities[last_split:i]
                if valid_range:
                    min_idx = last_split + np.argmin(valid_range) + 1
                    split_points.append(min_idx)
                    last_split = min_idx
                    current_tokens = sum(
                        count_tokens(s) 
                        for s in sentences[min_idx:i+1]
                    )
                else:
                    split_points.append(i)
                    last_split = i
                    current_tokens = sent_tokens
        else:
            current_tokens += sent_tokens
            
            # Check if we're at a semantic boundary
            if i < len(similarities):
                if (similarities[i] < 0.3 and  # Low similarity
                    current_tokens >= min_tokens):
                    split_points.append(i + 1)
                    last_split = i + 1
                    current_tokens = 0
    
    return split_points


def format_section_chunk(
    text: str, 
    section: str, 
    breadcrumb: List[str]
) -> str:
    """
    Format chunk with section context for better embeddings.
    """
    context_header = " > ".join(breadcrumb + [section])
    return f"[Section: {context_header}]\n\n{text}"
```

---

## 💻 Code (AST-Based) Chunking

### Strategy: Syntax-Aware Semantic Units

```python
class ASTChunkingStrategy:
    """
    Code chunking that respects program structure.
    
    Key insight: Code has natural semantic boundaries
    (functions, classes) that should be preserved.
    """
    
    # ═══════════════════════════════════════════════════════════════
    # CONFIGURATION
    # ═══════════════════════════════════════════════════════════════
    
    MIN_CHUNK_TOKENS = 50
    MAX_CHUNK_TOKENS = 600      # Smaller than text - code is dense
    INCLUDE_CONTEXT = True      # Add imports, class context
    
    # ═══════════════════════════════════════════════════════════════
    # CHUNKABLE UNITS BY LANGUAGE
    # ═══════════════════════════════════════════════════════════════
    
    AST_CHUNK_NODES = {
        "python": [
            "function_definition",
            "class_definition", 
            "decorated_definition",
        ],
        "javascript": [
            "function_declaration",
            "class_declaration",
            "arrow_function",
            "method_definition",
        ],
        "java": [
            "method_declaration",
            "class_declaration",
            "constructor_declaration",
        ],
        "cpp": [
            "function_definition",
            "class_specifier",
            "struct_specifier",
        ],
    }
```

### AST Chunking Implementation

```python
import tree_sitter_languages as tsl
from dataclasses import dataclass
from typing import List, Optional, Tuple

@dataclass
class CodeUnit:
    """A semantic unit of code (function, class, etc.)"""
    name: str
    unit_type: str           # function, class, method
    code: str
    start_line: int
    end_line: int
    docstring: Optional[str]
    parent_class: Optional[str]
    dependencies: List[str]  # imports/calls


def chunk_code_file(
    code: str,
    language: str,
    filename: str,
    llm_metadata: dict = None  # Pre-generated by Code Preprocessor Agent
) -> List[Chunk]:
    """
    Chunk code using AST analysis.
    
    Strategy:
    1. Parse code into AST
    2. Extract semantic units (functions, classes)
    3. Add context (imports, class signatures)
    4. Enrich with LLM-generated metadata
    """
    
    # Parse with tree-sitter
    parser = tsl.get_parser(language)
    tree = parser.parse(code.encode())
    
    # Extract file-level context
    imports = extract_imports(tree, language)
    
    # Extract semantic units
    units = extract_code_units(tree, code, language)
    
    chunks = []
    
    for unit in units:
        # Build chunk content with context
        chunk_content = build_code_chunk_content(
            unit=unit,
            imports=imports,
            language=language,
            llm_metadata=llm_metadata
        )
        
        # Get LLM-generated metadata for this unit if available
        unit_llm_meta = {}
        if llm_metadata and unit.name in llm_metadata.get("functions", {}):
            unit_llm_meta = llm_metadata["functions"][unit.name]
        
        chunk = Chunk(
            content=chunk_content,
            metadata={
                "chunk_type": "code",
                "language": language,
                "source_file": filename,
                "unit_type": unit.unit_type,
                "unit_name": unit.name,
                "qualified_name": f"{unit.parent_class}.{unit.name}" 
                                  if unit.parent_class else unit.name,
                "line_start": unit.start_line,
                "line_end": unit.end_line,
                "dependencies": unit.dependencies,
                
                # LLM-enriched metadata for search
                "summary": unit_llm_meta.get("summary", ""),
                "purpose": unit_llm_meta.get("what_it_does", ""),
                "concepts": unit_llm_meta.get("concepts_demonstrated", []),
                "nl_queries": unit_llm_meta.get("nl_queries", []),
            },
            token_count=count_tokens(chunk_content)
        )
        
        chunks.append(chunk)
    
    # Also create a file-level overview chunk
    if llm_metadata:
        overview_chunk = create_file_overview_chunk(
            code=code,
            filename=filename,
            language=language,
            llm_metadata=llm_metadata
        )
        chunks.insert(0, overview_chunk)
    
    return chunks


def extract_code_units(
    tree,
    source: str,
    language: str
) -> List[CodeUnit]:
    """
    Walk AST and extract semantic units.
    """
    
    node_types = AST_CHUNK_NODES.get(language, [])
    units = []
    
    def walk(node, parent_class=None):
        # Check if this is a chunkable node
        if node.type in node_types:
            unit = parse_code_unit(node, source, language, parent_class)
            if unit:
                units.append(unit)
                
                # If it's a class, walk children with class context
                if "class" in node.type:
                    for child in node.children:
                        walk(child, parent_class=unit.name)
                return
        
        # Recursively walk children
        for child in node.children:
            walk(child, parent_class)
    
    walk(tree.root_node)
    return units


def parse_code_unit(
    node,
    source: str,
    language: str,
    parent_class: Optional[str]
) -> Optional[CodeUnit]:
    """
    Parse a tree-sitter node into a CodeUnit.
    """
    
    # Extract code text
    code = source[node.start_byte:node.end_byte]
    
    # Get name (language-specific)
    name = extract_name(node, language)
    if not name:
        return None
    
    # Get docstring
    docstring = extract_docstring(node, source, language)
    
    # Determine unit type
    if "class" in node.type:
        unit_type = "class"
    elif "method" in node.type or parent_class:
        unit_type = "method"
    else:
        unit_type = "function"
    
    # Extract dependencies (function calls)
    dependencies = extract_dependencies(node, source)
    
    return CodeUnit(
        name=name,
        unit_type=unit_type,
        code=code,
        start_line=node.start_point[0] + 1,
        end_line=node.end_point[0] + 1,
        docstring=docstring,
        parent_class=parent_class,
        dependencies=dependencies
    )


def build_code_chunk_content(
    unit: CodeUnit,
    imports: List[str],
    language: str,
    llm_metadata: dict = None
) -> str:
    """
    Build chunk content with rich context for embedding.
    
    Format designed to embed well for natural language search.
    """
    
    parts = []
    
    # Language marker
    parts.append(f"[Language: {language}]")
    
    # Add LLM-generated summary (CRUCIAL for NL search)
    if llm_metadata:
        func_meta = llm_metadata.get("functions", {}).get(unit.name, {})
        if summary := func_meta.get("summary"):
            parts.append(f"[Purpose: {summary}]")
        if concepts := func_meta.get("concepts_demonstrated"):
            parts.append(f"[Concepts: {', '.join(concepts)}]")
    
    # Add relevant imports for context
    relevant_imports = filter_relevant_imports(imports, unit.dependencies)
    if relevant_imports:
        parts.append(f"# Imports:\n{chr(10).join(relevant_imports)}")
    
    # Add class context if method
    if unit.parent_class:
        parts.append(f"# Class: {unit.parent_class}")
    
    # The actual code
    parts.append(f"```{language}\n{unit.code}\n```")
    
    return "\n\n".join(parts)


def create_file_overview_chunk(
    code: str,
    filename: str,
    language: str,
    llm_metadata: dict
) -> Chunk:
    """
    Create an overview chunk for the entire file.
    
    This helps with queries like "show me code that does X"
    where X matches the file's overall purpose.
    """
    
    content_parts = [
        f"[File Overview: {filename}]",
        f"[Language: {language}]",
        f"\n[Purpose: {llm_metadata.get('purpose_summary', '')}]",
        f"\n[Algorithms: {', '.join(llm_metadata.get('algorithms_used', []))}]",
        f"[Data Structures: {', '.join(llm_metadata.get('data_structures_used', []))}]",
        f"[Concepts: {', '.join(llm_metadata.get('concepts_demonstrated', []))}]",
        f"\n[This file can answer questions like:]",
    ]
    
    for query in llm_metadata.get("nl_queries", [])[:5]:
        content_parts.append(f"- {query}")
    
    content = "\n".join(content_parts)
    
    return Chunk(
        content=content,
        metadata={
            "chunk_type": "code_overview",
            "language": language,
            "source_file": filename,
            "is_overview": True,
            "functions": llm_metadata.get("functions", {}).keys(),
            "concepts": llm_metadata.get("concepts_demonstrated", []),
            "nl_queries": llm_metadata.get("nl_queries", []),
        },
        token_count=count_tokens(content)
    )
```

### Code Chunking Visualization

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CODE CHUNKING EXAMPLE                                │
└─────────────────────────────────────────────────────────────────────────┘

Original File (sorting_algorithms.py):
┌─────────────────────────────────────────────────────────────────────────┐
│  1 │ import random                                                      │
│  2 │                                                                    │
│  3 │ def bubble_sort(arr):                                              │
│  4 │     """Sort using bubble sort algorithm."""                        │
│  5 │     n = len(arr)                                                   │
│  6 │     for i in range(n):                                             │
│  7 │         for j in range(0, n-i-1):                                  │
│  8 │             if arr[j] > arr[j+1]:                                  │
│  9 │                 arr[j], arr[j+1] = arr[j+1], arr[j]                │
│ 10 │     return arr                                                     │
│ 11 │                                                                    │
│ 12 │ def quick_sort(arr):                                               │
│ 13 │     """Sort using quicksort algorithm."""                          │
│ ... │     ...                                                           │
└─────────────────────────────────────────────────────────────────────────┘

After AST + LLM-Enhanced Chunking:

┌───────────────────────────────────────┐
│           CHUNK 0: Overview           │
│ [File Overview: sorting_algorithms.py]│
│ [Purpose: Demonstrates comparison-    │
│  based sorting algorithms]            │
│ [Algorithms: bubble sort, quicksort]  │
│ [Can answer: "how to sort a list",    │
│  "simple sorting algorithm", ...]     │
└───────────────────────────────────────┘

┌───────────────────────────────────────┐
│        CHUNK 1: bubble_sort           │
│ [Purpose: Sorts array by repeatedly   │
│  swapping adjacent elements]          │
│ [Concepts: nested loops, comparison]  │
│                                       │
│ ```python                             │
│ def bubble_sort(arr):                 │
│     ...                               │
│ ```                                   │
│                                       │
│ metadata:                             │
│   line_start: 3                       │
│   line_end: 10                        │
│   time_complexity: O(n²)              │
│   nl_queries: ["simple sort", ...]    │
└───────────────────────────────────────┘
```

---

## 🔗 Context Enrichment Strategies

### Contextual Headers

```python
def add_contextual_header(chunk: Chunk, document_meta: dict) -> Chunk:
    """
    Prepend contextual information to improve embedding quality.
    
    Research shows context headers improve retrieval by 10-15%.
    """
    
    header_parts = []
    
    # Course context
    header_parts.append(f"[Course: {document_meta['course_name']}]")
    
    if week := document_meta.get('week_number'):
        header_parts.append(f"[Week {week}]")
    
    # Content type
    header_parts.append(f"[{document_meta['category'].title()} Content]")
    
    # Section breadcrumb
    if breadcrumb := chunk.metadata.get('breadcrumb'):
        header_parts.append(f"[{' > '.join(breadcrumb)}]")
    
    header = " ".join(header_parts)
    
    chunk.content = f"{header}\n\n{chunk.content}"
    return chunk
```

### Parent-Child Relationships

```python
def add_parent_context(
    chunks: List[Chunk],
    parent_summaries: dict  # section_title -> summary
) -> List[Chunk]:
    """
    Add parent section summaries for hierarchical context.
    
    Helps with queries that span multiple chunks.
    """
    
    for chunk in chunks:
        if section := chunk.metadata.get('section'):
            if summary := parent_summaries.get(section):
                chunk.metadata['section_summary'] = summary
                
                # Also prepend to content for embedding
                chunk.content = f"[Section Overview: {summary}]\n\n{chunk.content}"
    
    return chunks
```

### Sibling Awareness

```python
def add_sibling_previews(chunks: List[Chunk]) -> List[Chunk]:
    """
    Add previews of adjacent chunks.
    
    Helps with questions that span chunk boundaries.
    """
    
    for i, chunk in enumerate(chunks):
        # Previous chunk preview
        if i > 0:
            prev = chunks[i - 1]
            preview = prev.content[:200] + "..."
            chunk.metadata['prev_chunk_preview'] = preview
        
        # Next chunk preview  
        if i < len(chunks) - 1:
            next_chunk = chunks[i + 1]
            preview = next_chunk.content[:200] + "..."
            chunk.metadata['next_chunk_preview'] = preview
    
    return chunks
```

---

## 📏 Chunk Size Optimization

### Size Recommendations by Content Type

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    OPTIMAL CHUNK SIZES (2025 Research)                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Content Type          │ Min Tokens │ Target │ Max Tokens │ Overlap    │
│  ──────────────────────┼────────────┼────────┼────────────┼──────────  │
│  Lecture Slides        │    100     │  400   │    800     │  50 (13%)  │
│  Technical Documents   │    150     │  500   │   1000     │  75 (15%)  │
│  Code (Functions)      │     50     │  300   │    600     │  0 (AST)   │
│  Code (Classes)        │    100     │  500   │   1000     │  0 (AST)   │
│  Definitions/Terms     │     50     │  150   │    300     │  0         │
│                                                                         │
│  Notes:                                                                 │
│  • Cohere embed-v3 optimal range: 256-512 tokens                       │
│  • Factual lookup: prefer smaller chunks                                │
│  • Conceptual understanding: prefer larger chunks                       │
│  • Code: respect AST boundaries over size limits                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Dynamic Size Selection

```python
def determine_chunk_size(
    content_type: str,
    query_patterns: List[str]  # Historical query types
) -> dict:
    """
    Dynamically determine optimal chunk size based on content
    and expected query patterns.
    """
    
    # Default sizes
    sizes = {
        "slides": {"min": 100, "target": 400, "max": 800, "overlap": 50},
        "pdf": {"min": 150, "target": 500, "max": 1000, "overlap": 75},
        "code": {"min": 50, "target": 300, "max": 600, "overlap": 0},
    }
    
    base = sizes.get(content_type, sizes["pdf"])
    
    # Adjust based on query patterns
    factual_keywords = ["what is", "define", "when", "who", "list"]
    conceptual_keywords = ["explain", "how does", "why", "compare"]
    
    factual_count = sum(
        1 for q in query_patterns 
        if any(kw in q.lower() for kw in factual_keywords)
    )
    conceptual_count = sum(
        1 for q in query_patterns
        if any(kw in q.lower() for kw in conceptual_keywords)
    )
    
    if factual_count > conceptual_count * 1.5:
        # Prefer smaller chunks for factual queries
        base["target"] = int(base["target"] * 0.8)
        base["max"] = int(base["max"] * 0.8)
    elif conceptual_count > factual_count * 1.5:
        # Prefer larger chunks for conceptual queries
        base["target"] = int(base["target"] * 1.2)
        base["min"] = int(base["min"] * 1.2)
    
    return base
```

---

## 📁 Related Files

- **[02-METADATA-SCHEMAS.md](./02-METADATA-SCHEMAS.md)** - Metadata attached to chunks
- **[04-CODE-PREPROCESSING.md](./04-CODE-PREPROCESSING.md)** - LLM enrichment before chunking
- **[05-RETRIEVAL-PIPELINE.md](./05-RETRIEVAL-PIPELINE.md)** - How chunks are searched
