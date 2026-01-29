# 📊 Metadata Schemas - Context Engineering for RAG

> **Purpose**: Define rich, searchable metadata structures that enhance retrieval accuracy  
> **Philosophy**: "Metadata is the secret weapon of RAG - invest in it during ingestion"

---

## 📋 Table of Contents

1. [Metadata Philosophy](#metadata-philosophy)
2. [Base Document Schema](#base-document-schema)
3. [Theory Content Schemas](#theory-content-schemas)
4. [Code Content Schemas](#code-content-schemas)
5. [Chunk-Level Metadata](#chunk-level-metadata)
6. [LLM-Generated Metadata](#llm-generated-metadata)
7. [Citation & Provenance](#citation--provenance)

---

## 🎯 Metadata Philosophy

### Why Rich Metadata Matters

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     METADATA-ENHANCED RETRIEVAL                         │
│                                                                         │
│   Traditional RAG:                                                      │
│   Query ──▶ Embed ──▶ Vector Search ──▶ Top-K Results                  │
│                                                                         │
│   Metadata-Enhanced RAG:                                                │
│   Query ──▶ Analyze ──▶ Filter by Metadata ──▶ Vector Search ──▶       │
│         ──▶ Re-rank with Metadata ──▶ Context-Aware Results            │
│                                                                         │
│   Result: 30-50% improvement in retrieval precision                    │
└─────────────────────────────────────────────────────────────────────────┘
```

### Metadata Categories

| Category | Purpose | Examples |
|----------|---------|----------|
| **Structural** | Document organization | Page, slide, section, hierarchy |
| **Semantic** | Content meaning | Topics, concepts, keywords |
| **Pedagogical** | Learning context | Prerequisites, difficulty, goals |
| **Technical** | Code-specific | Language, complexity, dependencies |
| **Relational** | Cross-references | Links, dependencies, related content |
| **Provenance** | Source tracking | File, page, timestamp, author |

---

## 📄 Base Document Schema

### Document-Level Metadata

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum

class ContentType(str, Enum):
    SLIDES = "slides"           # PPTX presentations
    DOCUMENT = "document"       # PDF documents
    CODE = "code"               # Source code files
    NOTES = "notes"             # Supplementary notes

class ContentCategory(str, Enum):
    THEORY = "theory"
    LAB = "lab"
    REFERENCE = "reference"
    EXERCISE = "exercise"

class DocumentMetadata(BaseModel):
    """
    Base metadata for all uploaded documents.
    Populated during initial ingestion.
    """
    
    # ═══════════════════════════════════════════════════════════════
    # IDENTIFICATION
    # ═══════════════════════════════════════════════════════════════
    document_id: str = Field(
        description="Unique identifier (UUID)"
    )
    filename: str = Field(
        description="Original filename with extension"
    )
    file_hash: str = Field(
        description="SHA-256 hash for deduplication"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # CLASSIFICATION
    # ═══════════════════════════════════════════════════════════════
    content_type: ContentType = Field(
        description="Type of content (slides, document, code)"
    )
    category: ContentCategory = Field(
        description="Course category (theory, lab)"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # COURSE CONTEXT
    # ═══════════════════════════════════════════════════════════════
    course_id: str = Field(
        description="Parent course identifier"
    )
    course_name: str = Field(
        description="Human-readable course name"
    )
    week_number: Optional[int] = Field(
        default=None,
        description="Week in course schedule (1-16)"
    )
    module_name: Optional[str] = Field(
        default=None,
        description="Module or unit name"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # TEMPORAL
    # ═══════════════════════════════════════════════════════════════
    uploaded_at: datetime = Field(
        default_factory=datetime.utcnow
    )
    processed_at: Optional[datetime] = Field(
        default=None,
        description="When preprocessing completed"
    )
    version: int = Field(
        default=1,
        description="Document version for updates"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════
    total_pages: Optional[int] = Field(
        default=None,
        description="Number of pages/slides"
    )
    total_chunks: Optional[int] = Field(
        default=None,
        description="Number of chunks generated"
    )
    word_count: Optional[int] = Field(
        default=None,
        description="Approximate word count"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # ADMIN TAGS
    # ═══════════════════════════════════════════════════════════════
    tags: List[str] = Field(
        default_factory=list,
        description="Admin-assigned tags"
    )
    is_active: bool = Field(
        default=True,
        description="Whether document is searchable"
    )
```

---

## 📑 Theory Content Schemas

### Slide Presentation (PPTX) Metadata

```python
class SlideMetadata(BaseModel):
    """
    Metadata for individual slides within a presentation.
    Rich structure enables slide-level retrieval.
    """
    
    # ═══════════════════════════════════════════════════════════════
    # SLIDE IDENTIFICATION
    # ═══════════════════════════════════════════════════════════════
    slide_id: str = Field(
        description="Unique slide identifier"
    )
    document_id: str = Field(
        description="Parent document ID"
    )
    slide_number: int = Field(
        description="1-indexed slide position"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # CONTENT EXTRACTION
    # ═══════════════════════════════════════════════════════════════
    title: Optional[str] = Field(
        default=None,
        description="Slide title text"
    )
    subtitle: Optional[str] = Field(
        default=None,
        description="Slide subtitle if present"
    )
    body_text: str = Field(
        description="All text content from slide"
    )
    speaker_notes: Optional[str] = Field(
        default=None,
        description="Speaker notes (valuable context!)"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # STRUCTURAL ANALYSIS
    # ═══════════════════════════════════════════════════════════════
    slide_type: Literal[
        "title",           # Title slide
        "section_header",  # Section divider
        "content",         # Regular content
        "two_column",      # Comparison layout
        "image_focused",   # Primarily visual
        "code_slide",      # Contains code
        "summary",         # Summary/recap slide
        "references"       # Bibliography/references
    ] = Field(
        description="Classified slide type"
    )
    
    has_images: bool = Field(
        default=False,
        description="Contains images/diagrams"
    )
    has_tables: bool = Field(
        default=False,
        description="Contains tables"
    )
    has_code: bool = Field(
        default=False,
        description="Contains code snippets"
    )
    has_equations: bool = Field(
        default=False,
        description="Contains mathematical notation"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # IMAGE DESCRIPTIONS (LLM-Generated)
    # ═══════════════════════════════════════════════════════════════
    image_descriptions: List[str] = Field(
        default_factory=list,
        description="LLM-generated descriptions of visual elements"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # HIERARCHICAL POSITION
    # ═══════════════════════════════════════════════════════════════
    section_name: Optional[str] = Field(
        default=None,
        description="Current section/topic"
    )
    section_number: Optional[int] = Field(
        default=None,
        description="Section index"
    )
    is_section_start: bool = Field(
        default=False,
        description="First slide of a section"
    )


class PresentationMetadata(DocumentMetadata):
    """
    Extended metadata for PPTX presentations.
    Includes LLM-generated semantic enrichment.
    """
    
    # ═══════════════════════════════════════════════════════════════
    # PRESENTATION STRUCTURE
    # ═══════════════════════════════════════════════════════════════
    presentation_title: str = Field(
        description="Main title from title slide"
    )
    sections: List[str] = Field(
        default_factory=list,
        description="List of section headings"
    )
    table_of_contents: List[dict] = Field(
        default_factory=list,
        description="Structured TOC with slide numbers"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # LLM-GENERATED SEMANTIC METADATA
    # ═══════════════════════════════════════════════════════════════
    main_topics: List[str] = Field(
        description="Primary topics covered (LLM extracted)"
    )
    key_concepts: List[str] = Field(
        description="Important concepts/terms defined"
    )
    learning_objectives: List[str] = Field(
        description="What students should learn"
    )
    prerequisites: List[str] = Field(
        default_factory=list,
        description="Required prior knowledge"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # SEARCHABILITY ENHANCEMENT
    # ═══════════════════════════════════════════════════════════════
    summary: str = Field(
        description="2-3 sentence overview (LLM generated)"
    )
    keywords: List[str] = Field(
        description="Searchable keywords and synonyms"
    )
    questions_addressed: List[str] = Field(
        default_factory=list,
        description="Questions this content can answer"
    )


class PDFDocumentMetadata(DocumentMetadata):
    """
    Metadata for PDF documents (textbooks, papers, notes).
    """
    
    # ═══════════════════════════════════════════════════════════════
    # DOCUMENT STRUCTURE
    # ═══════════════════════════════════════════════════════════════
    document_title: str = Field(
        description="Document title"
    )
    authors: List[str] = Field(
        default_factory=list,
        description="Document authors"
    )
    has_toc: bool = Field(
        default=False,
        description="Has table of contents"
    )
    chapters: List[dict] = Field(
        default_factory=list,
        description="Chapter/section structure with page numbers"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # PAGE-LEVEL TRACKING
    # ═══════════════════════════════════════════════════════════════
    page_labels: dict = Field(
        default_factory=dict,
        description="Map of page index to label (e.g., 'iv', '1', 'A-1')"
    )
    content_pages: List[int] = Field(
        default_factory=list,
        description="Pages with actual content (not TOC, etc.)"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # LLM-GENERATED ENRICHMENT
    # ═══════════════════════════════════════════════════════════════
    abstract: Optional[str] = Field(
        default=None,
        description="Document abstract or executive summary"
    )
    main_topics: List[str] = Field(
        default_factory=list,
        description="Primary topics covered"
    )
    key_concepts: List[str] = Field(
        default_factory=list,
        description="Important concepts defined"
    )
    summary: str = Field(
        description="LLM-generated overview"
    )
```

---

## 💻 Code Content Schemas

### Source Code File Metadata

```python
class CodeComplexity(str, Enum):
    BEGINNER = "beginner"           # Simple, introductory
    INTERMEDIATE = "intermediate"    # Standard patterns
    ADVANCED = "advanced"           # Complex algorithms
    EXPERT = "expert"               # Optimization, edge cases

class CodePurpose(str, Enum):
    DEMONSTRATION = "demonstration"  # Teaching a concept
    EXERCISE = "exercise"           # Student practice
    SOLUTION = "solution"           # Reference solution
    UTILITY = "utility"             # Helper/utility code
    TEST = "test"                   # Test cases


class CodeFileMetadata(DocumentMetadata):
    """
    Rich metadata for source code files.
    Combines static analysis with LLM-generated understanding.
    """
    
    # ═══════════════════════════════════════════════════════════════
    # LANGUAGE & ENVIRONMENT
    # ═══════════════════════════════════════════════════════════════
    language: str = Field(
        description="Programming language (python, java, cpp, etc.)"
    )
    language_version: Optional[str] = Field(
        default=None,
        description="Language version if specified"
    )
    framework: Optional[str] = Field(
        default=None,
        description="Framework used (django, react, etc.)"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # CODE CLASSIFICATION
    # ═══════════════════════════════════════════════════════════════
    purpose: CodePurpose = Field(
        description="Why this code exists"
    )
    complexity: CodeComplexity = Field(
        description="Difficulty level"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # STATIC ANALYSIS (Extracted via AST)
    # ═══════════════════════════════════════════════════════════════
    imports: List[str] = Field(
        default_factory=list,
        description="Import statements"
    )
    classes: List[str] = Field(
        default_factory=list,
        description="Class names defined"
    )
    functions: List[str] = Field(
        default_factory=list,
        description="Function/method names defined"
    )
    global_variables: List[str] = Field(
        default_factory=list,
        description="Global variable names"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # DEPENDENCY GRAPH
    # ═══════════════════════════════════════════════════════════════
    external_dependencies: List[str] = Field(
        default_factory=list,
        description="External packages required"
    )
    internal_dependencies: List[str] = Field(
        default_factory=list,
        description="Other course files this depends on"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # LLM-GENERATED UNDERSTANDING (Critical for NL→Code search)
    # ═══════════════════════════════════════════════════════════════
    purpose_summary: str = Field(
        description="What this code does in plain English"
    )
    algorithms_used: List[str] = Field(
        default_factory=list,
        description="Named algorithms implemented"
    )
    data_structures_used: List[str] = Field(
        default_factory=list,
        description="Key data structures"
    )
    design_patterns: List[str] = Field(
        default_factory=list,
        description="Design patterns applied"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # PEDAGOGICAL CONTEXT
    # ═══════════════════════════════════════════════════════════════
    concepts_demonstrated: List[str] = Field(
        description="CS concepts this code teaches"
    )
    learning_goals: List[str] = Field(
        description="What students learn from this"
    )
    common_mistakes: List[str] = Field(
        default_factory=list,
        description="Mistakes students might make"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # NATURAL LANGUAGE SEARCH ENHANCEMENT
    # ═══════════════════════════════════════════════════════════════
    nl_queries: List[str] = Field(
        description="Natural language questions this code answers"
    )
    keywords: List[str] = Field(
        description="Searchable terms"
    )
    related_topics: List[str] = Field(
        description="Related CS topics"
    )


class CodeFunctionMetadata(BaseModel):
    """
    Metadata for individual functions/methods.
    Enables function-level retrieval.
    """
    
    # ═══════════════════════════════════════════════════════════════
    # IDENTIFICATION
    # ═══════════════════════════════════════════════════════════════
    function_id: str = Field(
        description="Unique identifier"
    )
    document_id: str = Field(
        description="Parent file ID"
    )
    name: str = Field(
        description="Function name"
    )
    qualified_name: str = Field(
        description="Full path (e.g., ClassName.method_name)"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # LOCATION
    # ═══════════════════════════════════════════════════════════════
    start_line: int = Field(
        description="Starting line number"
    )
    end_line: int = Field(
        description="Ending line number"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # SIGNATURE
    # ═══════════════════════════════════════════════════════════════
    signature: str = Field(
        description="Function signature"
    )
    parameters: List[dict] = Field(
        default_factory=list,
        description="Parameters with types if available"
    )
    return_type: Optional[str] = Field(
        default=None,
        description="Return type if specified"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # DOCUMENTATION
    # ═══════════════════════════════════════════════════════════════
    docstring: Optional[str] = Field(
        default=None,
        description="Original docstring"
    )
    inline_comments: List[str] = Field(
        default_factory=list,
        description="Inline comments extracted"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # LLM-GENERATED (The Magic Sauce)
    # ═══════════════════════════════════════════════════════════════
    summary: str = Field(
        description="Plain English explanation"
    )
    what_it_does: str = Field(
        description="Simple description of behavior"
    )
    how_it_works: str = Field(
        description="Brief explanation of approach"
    )
    when_to_use: str = Field(
        description="Use cases for this function"
    )
    example_usage: Optional[str] = Field(
        default=None,
        description="Example of how to call this"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # COMPLEXITY ANALYSIS
    # ═══════════════════════════════════════════════════════════════
    time_complexity: Optional[str] = Field(
        default=None,
        description="Big-O time complexity"
    )
    space_complexity: Optional[str] = Field(
        default=None,
        description="Big-O space complexity"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # RELATIONSHIPS
    # ═══════════════════════════════════════════════════════════════
    calls: List[str] = Field(
        default_factory=list,
        description="Functions this function calls"
    )
    called_by: List[str] = Field(
        default_factory=list,
        description="Functions that call this"
    )
```

---

## 📦 Chunk-Level Metadata

### Universal Chunk Schema

```python
class ChunkType(str, Enum):
    TEXT = "text"                   # Regular text content
    CODE = "code"                   # Source code
    TABLE = "table"                 # Tabular data
    LIST = "list"                   # Bullet/numbered list
    DEFINITION = "definition"       # Term definition
    EXAMPLE = "example"             # Example/illustration
    EQUATION = "equation"           # Mathematical content


class ChunkMetadata(BaseModel):
    """
    Metadata attached to every chunk for precise retrieval.
    This is what gets stored alongside embeddings in ChromaDB.
    """
    
    # ═══════════════════════════════════════════════════════════════
    # CHUNK IDENTIFICATION
    # ═══════════════════════════════════════════════════════════════
    chunk_id: str = Field(
        description="Unique chunk identifier"
    )
    document_id: str = Field(
        description="Parent document ID"
    )
    chunk_index: int = Field(
        description="Position in document's chunk sequence"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # CONTENT CLASSIFICATION
    # ═══════════════════════════════════════════════════════════════
    chunk_type: ChunkType = Field(
        description="Type of content in chunk"
    )
    content_category: ContentCategory = Field(
        description="Theory or Lab"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # PRECISE LOCATION (Critical for Citations)
    # ═══════════════════════════════════════════════════════════════
    source_file: str = Field(
        description="Original filename"
    )
    page_number: Optional[int] = Field(
        default=None,
        description="Page number (for PDFs/slides)"
    )
    slide_number: Optional[int] = Field(
        default=None,
        description="Slide number (for PPTX)"
    )
    section_title: Optional[str] = Field(
        default=None,
        description="Section this chunk belongs to"
    )
    line_start: Optional[int] = Field(
        default=None,
        description="Starting line (for code)"
    )
    line_end: Optional[int] = Field(
        default=None,
        description="Ending line (for code)"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # HIERARCHICAL CONTEXT
    # ═══════════════════════════════════════════════════════════════
    parent_title: Optional[str] = Field(
        default=None,
        description="Title of containing section"
    )
    breadcrumb: List[str] = Field(
        default_factory=list,
        description="Hierarchical path to this chunk"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # COURSE CONTEXT (Inherited from document)
    # ═══════════════════════════════════════════════════════════════
    course_id: str = Field(
        description="Course identifier"
    )
    course_name: str = Field(
        description="Course name"
    )
    week_number: Optional[int] = Field(
        default=None,
        description="Week number"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # SEMANTIC ENRICHMENT
    # ═══════════════════════════════════════════════════════════════
    topics: List[str] = Field(
        default_factory=list,
        description="Topics this chunk covers"
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Searchable keywords"
    )
    summary: Optional[str] = Field(
        default=None,
        description="Brief summary of chunk content"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # CODE-SPECIFIC (When chunk_type == CODE)
    # ═══════════════════════════════════════════════════════════════
    language: Optional[str] = Field(
        default=None,
        description="Programming language"
    )
    function_name: Optional[str] = Field(
        default=None,
        description="Function/class name if applicable"
    )
    code_purpose: Optional[str] = Field(
        default=None,
        description="What this code does"
    )
    
    # ═══════════════════════════════════════════════════════════════
    # RETRIEVAL OPTIMIZATION
    # ═══════════════════════════════════════════════════════════════
    token_count: int = Field(
        description="Approximate token count"
    )
    has_context_overlap: bool = Field(
        default=False,
        description="Whether chunk has overlap with neighbors"
    )
    
    class Config:
        """Enable storage as ChromaDB metadata"""
        extra = "allow"
```

---

## 🤖 LLM-Generated Metadata

### Metadata Generation Prompts

```python
# ═══════════════════════════════════════════════════════════════════════════
# DOCUMENT ANALYSIS PROMPT
# ═══════════════════════════════════════════════════════════════════════════

DOCUMENT_ANALYSIS_PROMPT = """
Analyze this educational document and extract structured metadata.

<document>
{document_content}
</document>

<document_info>
Filename: {filename}
Type: {content_type}
Course: {course_name}
</document_info>

Extract the following information in JSON format:

{{
    "main_topics": ["list of 3-5 main topics covered"],
    "key_concepts": ["important terms/concepts defined or explained"],
    "learning_objectives": ["what students should be able to do after"],
    "prerequisites": ["prior knowledge needed to understand this"],
    "summary": "2-3 sentence overview of the content",
    "keywords": ["searchable terms including synonyms"],
    "questions_addressed": ["questions this content can answer"],
    "difficulty_level": "beginner|intermediate|advanced"
}}

Focus on accuracy and educational relevance.
"""


# ═══════════════════════════════════════════════════════════════════════════
# CODE ANALYSIS PROMPT
# ═══════════════════════════════════════════════════════════════════════════

CODE_ANALYSIS_PROMPT = """
Analyze this code file for educational purposes. Your analysis will help students
find this code when searching with natural language queries.

<code language="{language}">
{code_content}
</code>

<context>
Course: {course_name}
Category: {category}
Filename: {filename}
</context>

Provide analysis in JSON format:

{{
    "purpose_summary": "What this code does in 2-3 sentences, written for students",
    
    "algorithms_used": ["named algorithms like 'binary search', 'BFS', etc."],
    "data_structures_used": ["list", "dictionary", "tree", etc.],
    "design_patterns": ["singleton", "factory", etc. if applicable"],
    
    "concepts_demonstrated": ["CS concepts this teaches"],
    "learning_goals": ["what students learn from studying this"],
    "common_mistakes": ["mistakes students might make with similar code"],
    
    "nl_queries": [
        "Natural language questions this code could answer",
        "Example: 'how to implement binary search in python'",
        "Include 5-8 varied phrasings students might use"
    ],
    
    "keywords": ["searchable terms, including synonyms and related concepts"],
    
    "complexity": "beginner|intermediate|advanced|expert",
    "time_complexity": "O(n), O(log n), etc. for main algorithm",
    "space_complexity": "O(1), O(n), etc."
}}

Be specific and accurate. These will be used for semantic search.
"""


# ═══════════════════════════════════════════════════════════════════════════
# FUNCTION ANALYSIS PROMPT
# ═══════════════════════════════════════════════════════════════════════════

FUNCTION_ANALYSIS_PROMPT = """
Analyze this function for educational searchability.

<function>
{function_code}
</function>

<context>
Language: {language}
File: {filename}
Course: {course_name}
</context>

Provide JSON analysis:

{{
    "summary": "One sentence description in plain English",
    "what_it_does": "Simple explanation of behavior",
    "how_it_works": "Brief explanation of the approach used",
    "when_to_use": "Situations where you'd use this function",
    "example_usage": "Single line showing how to call this",
    "time_complexity": "Big-O notation",
    "space_complexity": "Big-O notation"
}}
"""
```

---

## 📍 Citation & Provenance

### Citation Schema

```python
class CitationMetadata(BaseModel):
    """
    Comprehensive provenance tracking for every piece of content.
    Enables precise citations in generated materials.
    """
    
    # ═══════════════════════════════════════════════════════════════
    # SOURCE IDENTIFICATION
    # ═══════════════════════════════════════════════════════════════
    document_id: str
    document_title: str
    source_file: str
    
    # ═══════════════════════════════════════════════════════════════
    # PRECISE LOCATION
    # ═══════════════════════════════════════════════════════════════
    page_number: Optional[int] = None
    slide_number: Optional[int] = None
    section_title: Optional[str] = None
    
    # For code
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    function_name: Optional[str] = None
    
    # ═══════════════════════════════════════════════════════════════
    # FORMATTED CITATION
    # ═══════════════════════════════════════════════════════════════
    @property
    def formatted_citation(self) -> str:
        """Generate human-readable citation"""
        parts = [self.document_title]
        
        if self.slide_number:
            parts.append(f"Slide {self.slide_number}")
        elif self.page_number:
            parts.append(f"Page {self.page_number}")
        
        if self.section_title:
            parts.append(f'"{self.section_title}"')
        
        if self.function_name:
            parts.append(f"function `{self.function_name}`")
        elif self.line_start:
            parts.append(f"lines {self.line_start}-{self.line_end}")
        
        return " → ".join(parts)
    
    @property
    def citation_key(self) -> str:
        """Short citation key for inline references"""
        if self.slide_number:
            return f"[{self.source_file}:slide{self.slide_number}]"
        elif self.page_number:
            return f"[{self.source_file}:p{self.page_number}]"
        elif self.line_start:
            return f"[{self.source_file}:L{self.line_start}]"
        return f"[{self.source_file}]"
```

### Citation in Retrieved Chunks

```python
class RetrievedChunk(BaseModel):
    """
    A chunk as returned from retrieval, with full provenance.
    """
    content: str
    metadata: ChunkMetadata
    citation: CitationMetadata
    relevance_score: float
    
    def to_context_string(self) -> str:
        """Format for inclusion in LLM context"""
        return f"""
<source citation="{self.citation.citation_key}">
{self.content}
</source>
"""
```

---

## 🔄 Metadata Update Flow

```
┌────────────────────────────────────────────────────────────────────┐
│                     METADATA LIFECYCLE                             │
└────────────────────────────────────────────────────────────────────┘

  Upload          Parse           Analyze          Chunk           Store
    │               │                │               │               │
    ▼               ▼                ▼               ▼               ▼
┌───────┐      ┌────────┐       ┌────────┐      ┌────────┐      ┌────────┐
│Basic  │ ───▶ │Extract │ ───▶  │LLM     │ ───▶ │Per-    │ ───▶ │ChromaDB│
│Meta   │      │Content │       │Enrich  │      │Chunk   │      │+Supa-  │
│       │      │        │       │        │      │Meta    │      │base    │
└───────┘      └────────┘       └────────┘      └────────┘      └────────┘
    │               │                │               │               │
    │               │                │               │               │
 filename       structure        topics          citations        vectors
 course_id      text             concepts        location         metadata
 type           images           keywords        breadcrumb       searchable
```

---

## 📁 Related Files

- **[03-CHUNKING-STRATEGIES.md](./03-CHUNKING-STRATEGIES.md)** - How chunks inherit and use this metadata
- **[04-CODE-PREPROCESSING.md](./04-CODE-PREPROCESSING.md)** - Code-specific metadata generation
- **[07-IMPLEMENTATION-TEMPLATES.md](./07-IMPLEMENTATION-TEMPLATES.md)** - Code for metadata extraction
