# 🛠️ Implementation Templates - Production-Ready Code

> **Purpose**: Ready-to-use code templates for building the RAG learning platform  
> **Note**: These are framework templates - adapt to your specific needs

---

## 📋 Table of Contents

1. [Project Setup](#project-setup)
2. [Configuration Management](#configuration-management)
3. [Content Processors](#content-processors)
4. [Embedding & Storage](#embedding--storage)
5. [Complete Ingestion Pipeline](#complete-ingestion-pipeline)
6. [Query & Retrieval](#query--retrieval)
7. [API Endpoints](#api-endpoints)
8. [Agentic Workflows with LangGraph](#agentic-workflows-with-langgraph)

---

## 🚀 Project Setup

### Requirements

```txt
# requirements.txt

# Core Framework
llama-index>=0.11.0
langchain>=0.3.0
langgraph>=0.2.0

# Vector Database
chromadb>=0.5.0

# Embeddings & LLM
cohere>=5.0.0
google-generativeai>=0.8.0
openai>=1.0.0

# Document Processing
python-pptx>=1.0.0
pymupdf>=1.24.0
tree-sitter>=0.22.0
tree-sitter-languages>=1.10.0

# Utilities
pydantic>=2.0.0
tiktoken>=0.7.0
rank-bm25>=0.2.2

# API
fastapi>=0.111.0
uvicorn>=0.30.0

# Database (optional - for metadata)
supabase>=2.0.0
```

### Project Structure

```bash
#!/bin/bash
# setup_project.sh

mkdir -p learning-platform/{src/{agents,ingestion/{processors,chunkers,enrichers},retrieval,generation,validation,storage},schemas,config/prompts,tests,docs}

# Create __init__.py files
find learning-platform/src -type d -exec touch {}/__init__.py \;

# Create main config files
touch learning-platform/config/settings.py
touch learning-platform/config/prompts/{analysis,generation,validation}.yaml

echo "Project structure created!"
```

---

## ⚙️ Configuration Management

### Settings Module

```python
# config/settings.py

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class LLMSettings(BaseSettings):
    """LLM Configuration"""
    
    # Primary LLM (Gemini)
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    gemini_model: str = "gemini-2.0-flash"
    
    # Fallback LLM (OpenAI)
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    openai_model: str = "gpt-4o-mini"
    
    # Generation settings
    default_temperature: float = 0.3
    max_tokens: int = 2000


class EmbeddingSettings(BaseSettings):
    """Embedding Configuration"""
    
    cohere_api_key: str = Field(..., env="COHERE_API_KEY")
    embed_model: str = "embed-english-v3.0"
    rerank_model: str = "rerank-english-v3.0"


class StorageSettings(BaseSettings):
    """Storage Configuration"""
    
    # ChromaDB
    chroma_persist_dir: str = "./data/chroma"
    collection_name: str = "learning_platform"
    
    # File storage
    upload_dir: str = "./data/uploads"
    processed_dir: str = "./data/processed"
    
    # Supabase (optional)
    supabase_url: Optional[str] = Field(None, env="SUPABASE_URL")
    supabase_key: Optional[str] = Field(None, env="SUPABASE_KEY")


class RetrievalSettings(BaseSettings):
    """Retrieval Configuration"""
    
    # Hybrid search weights
    dense_weight: float = 0.6
    sparse_weight: float = 0.4
    
    # Retrieval counts
    initial_k: int = 50
    rerank_k: int = 10
    
    # Context assembly
    max_context_tokens: int = 6000
    
    # Relevance threshold
    min_relevance_score: float = 0.3


class ChunkingSettings(BaseSettings):
    """Chunking Configuration"""
    
    # Text chunks
    text_min_tokens: int = 150
    text_max_tokens: int = 800
    text_overlap_tokens: int = 50
    
    # Code chunks
    code_min_tokens: int = 50
    code_max_tokens: int = 600


class Settings(BaseSettings):
    """Main Settings"""
    
    app_name: str = "Learning Platform RAG"
    debug: bool = False
    
    llm: LLMSettings = LLMSettings()
    embedding: EmbeddingSettings = EmbeddingSettings()
    storage: StorageSettings = StorageSettings()
    retrieval: RetrievalSettings = RetrievalSettings()
    chunking: ChunkingSettings = ChunkingSettings()
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

---

## 📄 Content Processors

### PPTX Processor

```python
# src/ingestion/processors/pptx_processor.py

from pptx import Presentation
from pptx.util import Inches
from dataclasses import dataclass
from typing import List, Optional, Tuple
import io


@dataclass
class SlideContent:
    """Extracted content from a single slide."""
    slide_number: int
    title: Optional[str]
    body_text: str
    speaker_notes: Optional[str]
    has_images: bool
    has_tables: bool
    has_code: bool
    image_data: List[bytes]  # Raw image bytes for later processing


class PPTXProcessor:
    """
    Extracts content from PowerPoint presentations.
    """
    
    def __init__(self, llm_client=None):
        self.llm = llm_client  # For image description
    
    def process(self, file_path: str) -> Tuple[dict, List[SlideContent]]:
        """
        Process a PPTX file.
        
        Returns:
            Tuple of (presentation_metadata, list of slide contents)
        """
        
        prs = Presentation(file_path)
        
        # Extract presentation-level metadata
        metadata = {
            'total_slides': len(prs.slides),
            'slide_width': prs.slide_width,
            'slide_height': prs.slide_height,
        }
        
        slides = []
        
        for idx, slide in enumerate(prs.slides, 1):
            slide_content = self._extract_slide(slide, idx)
            slides.append(slide_content)
        
        # Detect sections from slide titles
        metadata['sections'] = self._detect_sections(slides)
        
        return metadata, slides
    
    def _extract_slide(self, slide, slide_number: int) -> SlideContent:
        """Extract content from a single slide."""
        
        title = None
        body_parts = []
        speaker_notes = None
        images = []
        has_tables = False
        has_code = False
        
        # Extract shapes
        for shape in slide.shapes:
            # Title
            if shape.is_placeholder:
                if shape.placeholder_format.type == 1:  # Title
                    if shape.has_text_frame:
                        title = shape.text_frame.text.strip()
            
            # Text content
            if shape.has_text_frame:
                text = self._extract_text_frame(shape.text_frame)
                if text and text != title:
                    body_parts.append(text)
                    
                    # Check for code indicators
                    if self._looks_like_code(text):
                        has_code = True
            
            # Tables
            if shape.has_table:
                has_tables = True
                table_text = self._extract_table(shape.table)
                body_parts.append(table_text)
            
            # Images
            if hasattr(shape, 'image'):
                images.append(shape.image.blob)
        
        # Speaker notes
        if slide.has_notes_slide:
            notes_frame = slide.notes_slide.notes_text_frame
            if notes_frame:
                speaker_notes = notes_frame.text.strip()
        
        return SlideContent(
            slide_number=slide_number,
            title=title,
            body_text="\n\n".join(body_parts),
            speaker_notes=speaker_notes,
            has_images=len(images) > 0,
            has_tables=has_tables,
            has_code=has_code,
            image_data=images
        )
    
    def _extract_text_frame(self, text_frame) -> str:
        """Extract text from a text frame, preserving structure."""
        
        paragraphs = []
        
        for para in text_frame.paragraphs:
            text = para.text.strip()
            if text:
                # Add bullet indicator for lists
                if para.level > 0:
                    indent = "  " * para.level
                    text = f"{indent}• {text}"
                paragraphs.append(text)
        
        return "\n".join(paragraphs)
    
    def _extract_table(self, table) -> str:
        """Extract table as markdown."""
        
        rows = []
        
        for row_idx, row in enumerate(table.rows):
            cells = [cell.text.strip() for cell in row.cells]
            rows.append("| " + " | ".join(cells) + " |")
            
            # Add header separator after first row
            if row_idx == 0:
                separator = "|" + "|".join(["---"] * len(cells)) + "|"
                rows.append(separator)
        
        return "\n".join(rows)
    
    def _looks_like_code(self, text: str) -> bool:
        """Heuristic check if text looks like code."""
        
        code_indicators = [
            'def ', 'class ', 'import ', 'from ',  # Python
            'function ', 'const ', 'let ', 'var ',  # JavaScript
            'public ', 'private ', 'void ',  # Java/C++
            '= {', '=> ', '();', '[]', '->'
        ]
        
        return any(indicator in text for indicator in code_indicators)
    
    def _detect_sections(self, slides: List[SlideContent]) -> List[dict]:
        """Detect sections based on slide titles."""
        
        sections = []
        current_section = None
        
        for slide in slides:
            if slide.title:
                # Check if this looks like a section header
                if self._is_section_header(slide):
                    if current_section:
                        sections.append(current_section)
                    current_section = {
                        'name': slide.title,
                        'start_slide': slide.slide_number,
                        'end_slide': slide.slide_number
                    }
                elif current_section:
                    current_section['end_slide'] = slide.slide_number
        
        if current_section:
            sections.append(current_section)
        
        return sections
    
    def _is_section_header(self, slide: SlideContent) -> bool:
        """Check if a slide is a section header."""
        
        # Section headers typically have title but minimal body text
        if not slide.title:
            return False
        
        body_words = len(slide.body_text.split()) if slide.body_text else 0
        
        return body_words < 20


### PDF Processor

```python
# src/ingestion/processors/pdf_processor.py

import fitz  # PyMuPDF
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class PDFPage:
    """Extracted content from a PDF page."""
    page_number: int
    text: str
    headers: List[Tuple[int, str]]  # (level, text)
    has_images: bool
    has_tables: bool


class PDFProcessor:
    """
    Extracts content from PDF documents.
    """
    
    def __init__(self):
        pass
    
    def process(self, file_path: str) -> Tuple[dict, List[PDFPage]]:
        """
        Process a PDF file.
        
        Returns:
            Tuple of (document_metadata, list of page contents)
        """
        
        doc = fitz.open(file_path)
        
        # Extract metadata
        metadata = {
            'total_pages': len(doc),
            'title': doc.metadata.get('title', ''),
            'author': doc.metadata.get('author', ''),
            'subject': doc.metadata.get('subject', ''),
        }
        
        pages = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_content = self._extract_page(page, page_num + 1)
            pages.append(page_content)
        
        # Extract TOC if available
        toc = doc.get_toc()
        if toc:
            metadata['table_of_contents'] = [
                {'level': item[0], 'title': item[1], 'page': item[2]}
                for item in toc
            ]
        
        doc.close()
        
        return metadata, pages
    
    def _extract_page(self, page, page_number: int) -> PDFPage:
        """Extract content from a single page."""
        
        # Extract text with structure
        blocks = page.get_text("dict")["blocks"]
        
        text_parts = []
        headers = []
        has_images = False
        
        for block in blocks:
            if block["type"] == 0:  # Text block
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if text:
                            font_size = span.get("size", 12)
                            
                            # Detect headers by font size
                            if font_size > 14:
                                level = 1 if font_size > 18 else 2
                                headers.append((level, text))
                            
                            text_parts.append(text)
            
            elif block["type"] == 1:  # Image block
                has_images = True
        
        # Join text
        full_text = "\n".join(text_parts)
        
        # Detect tables (simple heuristic)
        has_tables = self._detect_tables(full_text)
        
        return PDFPage(
            page_number=page_number,
            text=full_text,
            headers=headers,
            has_images=has_images,
            has_tables=has_tables
        )
    
    def _detect_tables(self, text: str) -> bool:
        """Simple table detection heuristic."""
        
        lines = text.split('\n')
        
        # Look for lines with multiple tab/space separations
        potential_table_rows = 0
        
        for line in lines:
            # Count separators
            if line.count('\t') >= 2 or line.count('  ') >= 3:
                potential_table_rows += 1
        
        return potential_table_rows >= 3
```

### Code Processor (AST-Based)

```python
# src/ingestion/processors/code_processor.py

import tree_sitter_languages as tsl
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class CodeFunction:
    """Extracted function/method from code."""
    name: str
    qualified_name: str
    signature: str
    code: str
    docstring: Optional[str]
    start_line: int
    end_line: int
    parent_class: Optional[str]
    calls: List[str]
    parameters: List[Dict[str, Any]]


@dataclass
class CodeFile:
    """Extracted content from a code file."""
    language: str
    imports: List[str]
    classes: List[str]
    functions: List[CodeFunction]
    global_code: str


class CodeProcessor:
    """
    Extracts structured content from source code using AST parsing.
    """
    
    LANGUAGE_MAP = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.rs': 'rust',
        '.go': 'go',
    }
    
    def __init__(self):
        pass
    
    def process(self, file_path: str, content: str = None) -> CodeFile:
        """
        Process a code file.
        
        Args:
            file_path: Path to the file (for language detection)
            content: Optional content (if already loaded)
        """
        
        # Detect language
        ext = '.' + file_path.split('.')[-1].lower()
        language = self.LANGUAGE_MAP.get(ext, 'python')
        
        # Load content if not provided
        if content is None:
            with open(file_path, 'r') as f:
                content = f.read()
        
        # Parse with tree-sitter
        parser = tsl.get_parser(language)
        tree = parser.parse(content.encode())
        
        # Extract components
        imports = self._extract_imports(tree, content, language)
        classes = self._extract_class_names(tree, content, language)
        functions = self._extract_functions(tree, content, language)
        
        return CodeFile(
            language=language,
            imports=imports,
            classes=classes,
            functions=functions,
            global_code=content
        )
    
    def _extract_imports(
        self,
        tree,
        source: str,
        language: str
    ) -> List[str]:
        """Extract import statements."""
        
        imports = []
        
        import_types = {
            'python': ['import_statement', 'import_from_statement'],
            'javascript': ['import_statement', 'import_declaration'],
            'java': ['import_declaration'],
        }
        
        types = import_types.get(language, [])
        
        def walk(node):
            if node.type in types:
                imports.append(source[node.start_byte:node.end_byte])
            for child in node.children:
                walk(child)
        
        walk(tree.root_node)
        return imports
    
    def _extract_class_names(
        self,
        tree,
        source: str,
        language: str
    ) -> List[str]:
        """Extract class names."""
        
        classes = []
        
        class_types = {
            'python': ['class_definition'],
            'javascript': ['class_declaration'],
            'java': ['class_declaration'],
        }
        
        types = class_types.get(language, [])
        
        def walk(node):
            if node.type in types:
                # Find name child
                for child in node.children:
                    if child.type == 'identifier':
                        classes.append(source[child.start_byte:child.end_byte])
                        break
            for child in node.children:
                walk(child)
        
        walk(tree.root_node)
        return classes
    
    def _extract_functions(
        self,
        tree,
        source: str,
        language: str
    ) -> List[CodeFunction]:
        """Extract functions and methods."""
        
        functions = []
        
        func_types = {
            'python': ['function_definition'],
            'javascript': ['function_declaration', 'arrow_function', 'method_definition'],
            'java': ['method_declaration'],
        }
        
        types = func_types.get(language, [])
        
        def walk(node, parent_class=None):
            if node.type in types:
                func = self._parse_function(node, source, language, parent_class)
                if func:
                    functions.append(func)
            
            # Track class context
            if node.type in ['class_definition', 'class_declaration']:
                class_name = None
                for child in node.children:
                    if child.type == 'identifier':
                        class_name = source[child.start_byte:child.end_byte]
                        break
                
                for child in node.children:
                    walk(child, class_name)
            else:
                for child in node.children:
                    walk(child, parent_class)
        
        walk(tree.root_node)
        return functions
    
    def _parse_function(
        self,
        node,
        source: str,
        language: str,
        parent_class: Optional[str]
    ) -> Optional[CodeFunction]:
        """Parse a function node into CodeFunction."""
        
        # Extract name
        name = None
        for child in node.children:
            if child.type == 'identifier':
                name = source[child.start_byte:child.end_byte]
                break
        
        if not name:
            return None
        
        # Extract full code
        code = source[node.start_byte:node.end_byte]
        
        # Extract docstring (Python)
        docstring = None
        if language == 'python':
            docstring = self._extract_python_docstring(node, source)
        
        # Extract signature (first line)
        lines = code.split('\n')
        signature = lines[0].strip()
        
        # Extract function calls
        calls = self._extract_calls(node, source)
        
        # Build qualified name
        qualified_name = f"{parent_class}.{name}" if parent_class else name
        
        return CodeFunction(
            name=name,
            qualified_name=qualified_name,
            signature=signature,
            code=code,
            docstring=docstring,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            parent_class=parent_class,
            calls=calls,
            parameters=[]  # Could be extended
        )
    
    def _extract_python_docstring(self, node, source: str) -> Optional[str]:
        """Extract Python docstring from function."""
        
        for child in node.children:
            if child.type == 'block':
                for block_child in child.children:
                    if block_child.type == 'expression_statement':
                        for expr_child in block_child.children:
                            if expr_child.type == 'string':
                                docstring = source[expr_child.start_byte:expr_child.end_byte]
                                # Remove quotes
                                return docstring.strip('"""').strip("'''").strip()
        return None
    
    def _extract_calls(self, node, source: str) -> List[str]:
        """Extract function calls within a function."""
        
        calls = set()
        
        def walk(n):
            if n.type == 'call':
                # Get the function being called
                for child in n.children:
                    if child.type in ['identifier', 'attribute']:
                        calls.add(source[child.start_byte:child.end_byte])
                        break
            
            for child in n.children:
                walk(child)
        
        walk(node)
        return list(calls)
```

---

## 💾 Embedding & Storage

### ChromaDB Integration

```python
# src/storage/vector_store.py

import chromadb
from chromadb.config import Settings
import cohere
from typing import List, Dict, Any, Optional
import hashlib


class VectorStore:
    """
    ChromaDB-based vector store with Cohere embeddings.
    """
    
    def __init__(
        self,
        persist_dir: str,
        collection_name: str,
        cohere_api_key: str
    ):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        
        # Initialize Cohere client
        self.cohere = cohere.Client(cohere_api_key)
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of text content
            metadatas: List of metadata dicts
            ids: Optional list of IDs (generated if not provided)
            
        Returns:
            List of document IDs
        """
        
        if ids is None:
            ids = [self._generate_id(doc) for doc in documents]
        
        # Generate embeddings with Cohere
        embeddings = self._embed_documents(documents)
        
        # Sanitize metadata (ChromaDB only accepts certain types)
        clean_metadatas = [
            self._sanitize_metadata(m) for m in metadatas
        ]
        
        # Add to collection
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=clean_metadatas,
            ids=ids
        )
        
        return ids
    
    def search(
        self,
        query: str,
        k: int = 10,
        where: Optional[Dict] = None,
        include_embeddings: bool = False
    ) -> List[Dict]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            k: Number of results
            where: Optional filter conditions
            include_embeddings: Whether to return embeddings
            
        Returns:
            List of results with id, document, metadata, distance
        """
        
        # Embed query
        query_embedding = self._embed_query(query)
        
        # Search
        include = ["documents", "metadatas", "distances"]
        if include_embeddings:
            include.append("embeddings")
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=where,
            include=include
        )
        
        # Format results
        formatted = []
        for i in range(len(results['ids'][0])):
            result = {
                'id': results['ids'][0][i],
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i],
                'score': 1 / (1 + results['distances'][0][i])
            }
            if include_embeddings:
                result['embedding'] = results['embeddings'][0][i]
            formatted.append(result)
        
        return formatted
    
    def delete(self, ids: List[str]) -> None:
        """Delete documents by ID."""
        self.collection.delete(ids=ids)
    
    def get_by_filter(
        self,
        where: Dict,
        limit: int = 100
    ) -> List[Dict]:
        """Get documents matching a filter."""
        
        results = self.collection.get(
            where=where,
            limit=limit,
            include=["documents", "metadatas"]
        )
        
        formatted = []
        for i in range(len(results['ids'])):
            formatted.append({
                'id': results['ids'][i],
                'content': results['documents'][i],
                'metadata': results['metadatas'][i]
            })
        
        return formatted
    
    def _embed_documents(self, documents: List[str]) -> List[List[float]]:
        """Embed documents for storage."""
        
        response = self.cohere.embed(
            texts=documents,
            model="embed-english-v3.0",
            input_type="search_document"
        )
        
        return response.embeddings
    
    def _embed_query(self, query: str) -> List[float]:
        """Embed a query for search."""
        
        response = self.cohere.embed(
            texts=[query],
            model="embed-english-v3.0",
            input_type="search_query"
        )
        
        return response.embeddings[0]
    
    def _generate_id(self, content: str) -> str:
        """Generate a unique ID for content."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _sanitize_metadata(self, metadata: Dict) -> Dict:
        """
        Sanitize metadata for ChromaDB.
        
        ChromaDB only accepts str, int, float, bool values.
        """
        
        clean = {}
        
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                clean[key] = value
            elif isinstance(value, list):
                # Convert lists to comma-separated strings
                if all(isinstance(v, str) for v in value):
                    clean[key] = ",".join(value)
                else:
                    clean[key] = str(value)
            elif value is None:
                clean[key] = ""
            else:
                clean[key] = str(value)
        
        return clean
```

---

## 🔄 Complete Ingestion Pipeline

```python
# src/ingestion/pipeline.py

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import asyncio
import json

from .processors.pptx_processor import PPTXProcessor
from .processors.pdf_processor import PDFProcessor
from .processors.code_processor import CodeProcessor
from ..storage.vector_store import VectorStore


@dataclass
class IngestionResult:
    """Result of document ingestion."""
    document_id: str
    filename: str
    chunk_count: int
    status: str
    errors: List[str]


class IngestionPipeline:
    """
    Complete pipeline for ingesting documents into the RAG system.
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        llm_client,
        config: dict
    ):
        self.vector_store = vector_store
        self.llm = llm_client
        self.config = config
        
        # Initialize processors
        self.pptx_processor = PPTXProcessor(llm_client)
        self.pdf_processor = PDFProcessor()
        self.code_processor = CodeProcessor()
    
    async def ingest(
        self,
        file_path: str,
        course_context: dict
    ) -> IngestionResult:
        """
        Ingest a single document.
        
        Args:
            file_path: Path to the file
            course_context: Course metadata (course_id, name, week, etc.)
            
        Returns:
            IngestionResult
        """
        
        import uuid
        
        document_id = str(uuid.uuid4())
        filename = file_path.split('/')[-1]
        errors = []
        
        try:
            # Determine file type
            ext = filename.split('.')[-1].lower()
            
            # Process based on type
            if ext == 'pptx':
                chunks = await self._process_pptx(
                    file_path, document_id, course_context
                )
            elif ext == 'pdf':
                chunks = await self._process_pdf(
                    file_path, document_id, course_context
                )
            elif ext in ['py', 'js', 'java', 'cpp', 'c', 'ts']:
                chunks = await self._process_code(
                    file_path, document_id, course_context
                )
            else:
                raise ValueError(f"Unsupported file type: {ext}")
            
            # Add to vector store
            documents = [c['content'] for c in chunks]
            metadatas = [c['metadata'] for c in chunks]
            ids = [c['id'] for c in chunks]
            
            self.vector_store.add_documents(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            return IngestionResult(
                document_id=document_id,
                filename=filename,
                chunk_count=len(chunks),
                status="success",
                errors=[]
            )
        
        except Exception as e:
            return IngestionResult(
                document_id=document_id,
                filename=filename,
                chunk_count=0,
                status="failed",
                errors=[str(e)]
            )
    
    async def _process_pptx(
        self,
        file_path: str,
        document_id: str,
        course_context: dict
    ) -> List[dict]:
        """Process PPTX file into chunks."""
        
        # Extract content
        metadata, slides = self.pptx_processor.process(file_path)
        
        # Generate LLM enrichment for the presentation
        enrichment = await self._enrich_presentation(slides, course_context)
        
        # Chunk slides
        chunks = []
        
        for slide in slides:
            # Build chunk content with context
            content = self._format_slide_chunk(
                slide, enrichment, course_context
            )
            
            chunk_metadata = {
                'document_id': document_id,
                'source_file': file_path.split('/')[-1],
                'chunk_type': 'slide',
                'slide_number': slide.slide_number,
                'title': slide.title or '',
                'course_id': course_context.get('course_id', ''),
                'course_name': course_context.get('course_name', ''),
                'category': course_context.get('category', 'theory'),
                'week_number': course_context.get('week_number', 0),
                'has_code': slide.has_code,
                'topics': ','.join(enrichment.get('topics', [])),
            }
            
            chunks.append({
                'id': f"{document_id}_slide_{slide.slide_number}",
                'content': content,
                'metadata': chunk_metadata
            })
        
        return chunks
    
    async def _process_code(
        self,
        file_path: str,
        document_id: str,
        course_context: dict
    ) -> List[dict]:
        """Process code file into chunks."""
        
        # Read file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Parse code
        code_file = self.code_processor.process(file_path, content)
        
        # Get LLM enrichment
        enrichment = await self._enrich_code(
            code_file, content, course_context
        )
        
        chunks = []
        filename = file_path.split('/')[-1]
        
        # Create overview chunk
        overview_content = self._format_code_overview(
            code_file, enrichment, course_context
        )
        
        chunks.append({
            'id': f"{document_id}_overview",
            'content': overview_content,
            'metadata': {
                'document_id': document_id,
                'source_file': filename,
                'chunk_type': 'code_overview',
                'language': code_file.language,
                'course_id': course_context.get('course_id', ''),
                'category': 'lab',
                'is_overview': True,
                'concepts': ','.join(enrichment.get('concepts_demonstrated', [])),
                'nl_queries': ','.join(enrichment.get('nl_queries', [])[:5]),
            }
        })
        
        # Create function-level chunks
        for func in code_file.functions:
            func_enrichment = enrichment.get('functions', {}).get(func.name, {})
            
            func_content = self._format_function_chunk(
                func, func_enrichment, code_file.language
            )
            
            chunks.append({
                'id': f"{document_id}_func_{func.name}",
                'content': func_content,
                'metadata': {
                    'document_id': document_id,
                    'source_file': filename,
                    'chunk_type': 'code',
                    'language': code_file.language,
                    'function_name': func.name,
                    'line_start': func.start_line,
                    'line_end': func.end_line,
                    'course_id': course_context.get('course_id', ''),
                    'category': 'lab',
                    'summary': func_enrichment.get('summary', ''),
                    'purpose': func_enrichment.get('what_it_does', ''),
                }
            })
        
        return chunks
    
    async def _enrich_code(
        self,
        code_file,
        content: str,
        course_context: dict
    ) -> dict:
        """Generate LLM enrichment for code."""
        
        prompt = f"""
Analyze this {code_file.language} code file for educational purposes.

```{code_file.language}
{content[:6000]}
```

Course: {course_context.get('course_name', '')}

Return JSON with:
{{
    "purpose_summary": "What this code does (2-3 sentences)",
    "algorithms_used": ["Named algorithms"],
    "data_structures_used": ["Data structures"],
    "concepts_demonstrated": ["CS concepts"],
    "nl_queries": ["10 natural language questions this code answers"],
    "functions": {{
        "function_name": {{
            "summary": "One sentence description",
            "what_it_does": "Simple explanation",
            "time_complexity": "Big-O",
            "concepts": ["concepts"]
        }}
    }}
}}
"""
        
        response = await self.llm.generate(
            prompt=prompt,
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        return json.loads(response)
    
    def _format_function_chunk(
        self,
        func,
        enrichment: dict,
        language: str
    ) -> str:
        """Format a function chunk with enrichment."""
        
        parts = [
            f"[Language: {language}]",
        ]
        
        if summary := enrichment.get('summary'):
            parts.append(f"[Purpose: {summary}]")
        
        if concepts := enrichment.get('concepts'):
            parts.append(f"[Concepts: {', '.join(concepts)}]")
        
        if func.docstring:
            parts.append(f"[Documentation: {func.docstring}]")
        
        parts.append(f"\n```{language}\n{func.code}\n```")
        
        return "\n".join(parts)
```

---

## 🤖 Agentic Workflows with LangGraph

```python
# src/agents/rag_workflow.py

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import TypedDict, Annotated, List
from operator import add


class RAGState(TypedDict):
    """State for the RAG workflow."""
    
    # Input
    query: str
    course_id: str
    
    # Processing
    query_analysis: dict
    expanded_queries: List[str]
    
    # Retrieval
    retrieved_chunks: List[dict]
    reranked_chunks: List[dict]
    
    # Generation
    context_string: str
    generated_content: str
    citations: List[dict]
    
    # Validation
    validation_result: dict
    is_valid: bool
    
    # Output
    final_response: str
    errors: Annotated[List[str], add]


def create_rag_workflow(
    query_processor,
    retriever,
    reranker,
    generator,
    validator
):
    """
    Create the RAG workflow graph.
    """
    
    # Define nodes
    async def analyze_query(state: RAGState) -> dict:
        """Analyze and classify the query."""
        
        analysis = await query_processor.process(state['query'])
        
        return {
            'query_analysis': {
                'intent': analysis.intent.value,
                'entities': analysis.entities,
                'filters': analysis.filters
            },
            'expanded_queries': analysis.expanded_queries
        }
    
    async def retrieve_context(state: RAGState) -> dict:
        """Retrieve relevant chunks."""
        
        chunks = await retriever.retrieve(
            queries=state['expanded_queries'],
            filters={'course_id': state['course_id']},
            k=50
        )
        
        return {'retrieved_chunks': chunks}
    
    async def rerank_chunks(state: RAGState) -> dict:
        """Rerank retrieved chunks."""
        
        reranked = await reranker.rerank(
            query=state['query'],
            documents=state['retrieved_chunks'],
            top_k=10
        )
        
        return {'reranked_chunks': reranked}
    
    async def generate_response(state: RAGState) -> dict:
        """Generate response with citations."""
        
        result = await generator.generate(
            query=state['query'],
            chunks=state['reranked_chunks'],
            intent=state['query_analysis']['intent']
        )
        
        return {
            'generated_content': result.content,
            'citations': result.citations,
            'context_string': result.context_string
        }
    
    async def validate_response(state: RAGState) -> dict:
        """Validate the generated response."""
        
        validation = await validator.validate(
            content=state['generated_content'],
            sources=state['reranked_chunks']
        )
        
        return {
            'validation_result': validation,
            'is_valid': validation['overall_score'] >= 0.8
        }
    
    def should_regenerate(state: RAGState) -> str:
        """Decide if we should regenerate."""
        
        if state['is_valid']:
            return "finalize"
        else:
            return "regenerate"
    
    async def regenerate_response(state: RAGState) -> dict:
        """Regenerate with corrections."""
        
        corrections = state['validation_result'].get('suggested_corrections', [])
        
        result = await generator.generate_with_corrections(
            query=state['query'],
            previous_content=state['generated_content'],
            corrections=corrections,
            chunks=state['reranked_chunks']
        )
        
        return {
            'generated_content': result.content,
            'is_valid': True  # Skip re-validation
        }
    
    async def finalize_response(state: RAGState) -> dict:
        """Prepare final response."""
        
        return {
            'final_response': state['generated_content']
        }
    
    # Build graph
    workflow = StateGraph(RAGState)
    
    # Add nodes
    workflow.add_node("analyze_query", analyze_query)
    workflow.add_node("retrieve_context", retrieve_context)
    workflow.add_node("rerank_chunks", rerank_chunks)
    workflow.add_node("generate_response", generate_response)
    workflow.add_node("validate_response", validate_response)
    workflow.add_node("regenerate_response", regenerate_response)
    workflow.add_node("finalize_response", finalize_response)
    
    # Add edges
    workflow.set_entry_point("analyze_query")
    workflow.add_edge("analyze_query", "retrieve_context")
    workflow.add_edge("retrieve_context", "rerank_chunks")
    workflow.add_edge("rerank_chunks", "generate_response")
    workflow.add_edge("generate_response", "validate_response")
    
    # Conditional edge for validation
    workflow.add_conditional_edges(
        "validate_response",
        should_regenerate,
        {
            "finalize": "finalize_response",
            "regenerate": "regenerate_response"
        }
    )
    
    workflow.add_edge("regenerate_response", "finalize_response")
    workflow.add_edge("finalize_response", END)
    
    return workflow.compile()
```

---

## 🌐 API Endpoints

```python
# src/api/routes.py

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
import shutil
import os


app = FastAPI(title="Learning Platform RAG API")


# ═══════════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════

class QueryRequest(BaseModel):
    query: str
    course_id: str
    include_citations: bool = True
    max_results: int = 10


class QueryResponse(BaseModel):
    content: str
    citations: List[dict]
    sources_used: int
    confidence_score: float


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    chunks_created: int
    status: str


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.post("/api/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    """
    Query the knowledge base and get AI-generated response.
    """
    
    try:
        # Run the RAG workflow
        result = await rag_workflow.ainvoke({
            'query': request.query,
            'course_id': request.course_id,
            'errors': []
        })
        
        return QueryResponse(
            content=result['final_response'],
            citations=result.get('citations', []),
            sources_used=len(result.get('reranked_chunks', [])),
            confidence_score=result.get('validation_result', {}).get('overall_score', 0.0)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search")
async def search_documents(
    query: str,
    course_id: str,
    category: Optional[str] = None,
    k: int = 10
):
    """
    Search documents without generation.
    """
    
    filters = {'course_id': course_id}
    if category:
        filters['category'] = category
    
    results = await retrieval_pipeline.search(
        query=query,
        filters=filters,
        k=k
    )
    
    return {
        'results': results,
        'total': len(results)
    }


@app.post("/api/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    course_id: str = Form(...),
    course_name: str = Form(...),
    category: str = Form(...),
    week_number: Optional[int] = Form(None)
):
    """
    Upload and process a document.
    """
    
    # Save file temporarily
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Process document
        result = await ingestion_pipeline.ingest(
            file_path=temp_path,
            course_context={
                'course_id': course_id,
                'course_name': course_name,
                'category': category,
                'week_number': week_number
            }
        )
        
        return UploadResponse(
            document_id=result.document_id,
            filename=result.filename,
            chunks_created=result.chunk_count,
            status=result.status
        )
    
    finally:
        # Clean up
        os.remove(temp_path)


@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document and its chunks.
    """
    
    # Get all chunks for this document
    chunks = vector_store.get_by_filter(
        where={'document_id': document_id}
    )
    
    if not chunks:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete chunks
    chunk_ids = [c['id'] for c in chunks]
    vector_store.delete(ids=chunk_ids)
    
    return {'deleted': len(chunk_ids), 'document_id': document_id}


@app.get("/api/courses/{course_id}/documents")
async def list_course_documents(course_id: str):
    """
    List all documents in a course.
    """
    
    chunks = vector_store.get_by_filter(
        where={'course_id': course_id},
        limit=1000
    )
    
    # Group by document
    documents = {}
    for chunk in chunks:
        doc_id = chunk['metadata']['document_id']
        if doc_id not in documents:
            documents[doc_id] = {
                'document_id': doc_id,
                'filename': chunk['metadata'].get('source_file', ''),
                'category': chunk['metadata'].get('category', ''),
                'chunk_count': 0
            }
        documents[doc_id]['chunk_count'] += 1
    
    return {'documents': list(documents.values())}


# ═══════════════════════════════════════════════════════════════
# STARTUP
# ═══════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup():
    """Initialize services on startup."""
    
    global vector_store, ingestion_pipeline, retrieval_pipeline, rag_workflow
    
    from config.settings import get_settings
    
    settings = get_settings()
    
    # Initialize vector store
    vector_store = VectorStore(
        persist_dir=settings.storage.chroma_persist_dir,
        collection_name=settings.storage.collection_name,
        cohere_api_key=settings.embedding.cohere_api_key
    )
    
    # Initialize pipelines
    # ... (initialize other components)
    
    print("🚀 Learning Platform RAG API started!")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 📁 Summary

This guide provides a comprehensive foundation for building your sophisticated RAG-powered learning platform. The key components are:

1. **Architecture** (01): System overview and design principles
2. **Metadata Schemas** (02): Rich metadata for enhanced retrieval
3. **Chunking Strategies** (03): Content-aware chunking
4. **Code Preprocessing** (04): LLM-assisted code understanding
5. **Retrieval Pipeline** (05): Hybrid search with reranking
6. **Generation & Validation** (06): Grounded generation with citations
7. **Implementation Templates** (07): Production-ready code

**Next Steps:**
1. Set up the project structure
2. Configure API keys and environment
3. Start with ingestion pipeline for your content
4. Build the retrieval system
5. Add generation with validation
6. Deploy API endpoints

Good luck with your AI learning platform! 🎓
