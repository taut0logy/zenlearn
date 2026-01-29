"""
Code Chunker - AST-based chunking for source code.
"""

from typing import List, Dict, Any, Optional

from .base import BaseChunker, Chunk, ChunkingConfig, count_tokens
from rag_engine.code_processor import (
    StaticAnalyzer,
    CodePreprocessor,
    CodeAnalysisResult,
    FunctionInfo
)


class CodeChunker(BaseChunker):
    """
    Chunker for source code files.
    
    Strategy:
    - Use AST to identify function/class boundaries
    - Each function/class is a chunk
    - Enrich with LLM-generated metadata for search
    - Create file overview chunk
    """
    
    def __init__(self, config: Optional[ChunkingConfig] = None):
        default_config = ChunkingConfig(
            min_tokens=50,
            max_tokens=600,
            target_tokens=300,
            overlap_tokens=0  # AST-based, no overlap needed
        )
        super().__init__(config or default_config)
        self.static_analyzer = StaticAnalyzer()
    
    def chunk(
        self,
        content: Any,
        metadata: Dict[str, Any]
    ) -> List[Chunk]:
        """
        Chunk a code file using AST analysis.
        
        Args:
            content: Source code string or file path
            metadata: Base metadata including 'filename'
            
        Returns:
            List of chunks
        """
        # Handle file path or code string
        if isinstance(content, str) and '\n' not in content and content.endswith(('.py', '.js', '.ts', '.java')):
            with open(content, 'r', encoding='utf-8') as f:
                code = f.read()
            filename = content.split('\\')[-1].split('/')[-1]
        else:
            code = content
            filename = metadata.get('filename', 'unknown.py')
        
        # Static analysis
        static = self.static_analyzer.analyze(code, filename)
        
        return self._chunk_code(code, static, metadata)
    
    def chunk_with_llm_metadata(
        self,
        content: str,
        metadata: Dict[str, Any],
        llm_analysis: CodeAnalysisResult
    ) -> List[Chunk]:
        """
        Chunk code with pre-computed LLM analysis.
        
        Args:
            content: Source code
            metadata: Base metadata
            llm_analysis: Pre-computed CodeAnalysisResult
            
        Returns:
            List of chunks enriched with LLM metadata
        """
        return self._chunk_code_with_llm(content, llm_analysis, metadata)
    
    def _chunk_code(
        self,
        code: str,
        static,
        base_metadata: Dict[str, Any]
    ) -> List[Chunk]:
        """Chunk code based on AST analysis."""
        chunks = []
        filename = base_metadata.get('filename', 'unknown')
        
        # File overview chunk
        overview = self._create_overview_chunk(code, static, base_metadata)
        chunks.append(overview)
        
        # Function chunks
        for func in static.functions:
            chunk = self._create_function_chunk(func, static, base_metadata)
            chunks.append(chunk)
        
        # Class chunks (without methods - methods are separate)
        for cls in static.classes:
            chunk = self._create_class_chunk(cls, static, base_metadata)
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_code_with_llm(
        self,
        code: str,
        analysis: CodeAnalysisResult,
        base_metadata: Dict[str, Any]
    ) -> List[Chunk]:
        """Chunk code with LLM metadata enrichment."""
        chunks = []
        
        # Overview chunk with LLM insights
        overview = self._create_enriched_overview(code, analysis, base_metadata)
        chunks.append(overview)
        
        # Function chunks with LLM metadata
        for func in analysis.static.functions:
            func_analysis = analysis.functions.get(func.name)
            chunk = self._create_enriched_function_chunk(
                func, 
                func_analysis,
                analysis.static,
                base_metadata
            )
            chunks.append(chunk)
        
        return chunks
    
    def _create_overview_chunk(
        self,
        code: str,
        static,
        base_metadata: Dict[str, Any]
    ) -> Chunk:
        """Create file overview chunk."""
        filename = base_metadata.get('filename', 'unknown')
        
        content_parts = [
            f"[File Overview: {filename}]",
            f"[Language: {static.language}]",
            f"[Functions: {', '.join(f.name for f in static.functions)}]",
            f"[Classes: {', '.join(c.name for c in static.classes)}]",
        ]
        
        if static.imports:
            content_parts.append(f"[Imports: {', '.join(static.imports[:5])}]")
        
        content = "\n".join(content_parts)
        
        chunk_metadata = self._merge_metadata(base_metadata, {
            "chunk_type": "code_overview",
            "language": static.language,
            "is_overview": True,
            "functions": [f.name for f in static.functions],
            "classes": [c.name for c in static.classes],
        })
        
        return Chunk(
            content=content,
            metadata=chunk_metadata,
            token_count=count_tokens(content)
        )
    
    def _create_enriched_overview(
        self,
        code: str,
        analysis: CodeAnalysisResult,
        base_metadata: Dict[str, Any]
    ) -> Chunk:
        """Create enriched overview with LLM insights."""
        filename = base_metadata.get('filename', 'unknown')
        
        content_parts = [
            f"[File Overview: {filename}]",
            f"[Language: {analysis.static.language}]",
            f"[Purpose: {analysis.purpose_summary}]",
            f"[Algorithms: {', '.join(analysis.algorithms_used)}]",
            f"[Concepts: {', '.join(analysis.concepts_demonstrated)}]",
        ]
        
        if analysis.nl_queries:
            content_parts.append("[This file can answer:]")
            for q in analysis.nl_queries[:5]:
                content_parts.append(f"- {q}")
        
        content = "\n".join(content_parts)
        
        chunk_metadata = self._merge_metadata(base_metadata, {
            "chunk_type": "code_overview",
            "language": analysis.static.language,
            "is_overview": True,
            "purpose": analysis.purpose_summary,
            "algorithms": analysis.algorithms_used,
            "concepts": analysis.concepts_demonstrated,
            "nl_queries": analysis.nl_queries,
            "keywords": analysis.keywords,
        })
        
        return Chunk(
            content=content,
            metadata=chunk_metadata,
            token_count=count_tokens(content)
        )
    
    def _create_function_chunk(
        self,
        func: FunctionInfo,
        static,
        base_metadata: Dict[str, Any]
    ) -> Chunk:
        """Create chunk for a function."""
        content_parts = [
            f"[Language: {static.language}]",
        ]
        
        if func.docstring:
            content_parts.append(f"[Docstring: {func.docstring}]")
        
        if func.parent_class:
            content_parts.append(f"[Class: {func.parent_class}]")
        
        # Add code
        content_parts.append(f"```{static.language}\n{func.code}\n```")
        
        content = "\n\n".join(content_parts)
        
        chunk_metadata = self._merge_metadata(base_metadata, {
            "chunk_type": "code",
            "language": static.language,
            "unit_type": "method" if func.parent_class else "function",
            "unit_name": func.name,
            "qualified_name": func.qualified_name,
            "line_start": func.start_line,
            "line_end": func.end_line,
            "parent_class": func.parent_class,
        })
        
        return Chunk(
            content=content,
            metadata=chunk_metadata,
            token_count=count_tokens(content)
        )
    
    def _create_enriched_function_chunk(
        self,
        func: FunctionInfo,
        func_analysis,
        static,
        base_metadata: Dict[str, Any]
    ) -> Chunk:
        """Create enriched function chunk with LLM metadata."""
        content_parts = [
            f"[Language: {static.language}]",
        ]
        
        if func_analysis:
            content_parts.append(f"[Purpose: {func_analysis.summary}]")
            if func_analysis.concepts:
                content_parts.append(f"[Concepts: {', '.join(func_analysis.concepts)}]")
            if func_analysis.time_complexity:
                content_parts.append(f"[Complexity: {func_analysis.time_complexity}]")
        
        if func.parent_class:
            content_parts.append(f"[Class: {func.parent_class}]")
        
        content_parts.append(f"```{static.language}\n{func.code}\n```")
        
        content = "\n\n".join(content_parts)
        
        chunk_metadata = self._merge_metadata(base_metadata, {
            "chunk_type": "code",
            "language": static.language,
            "unit_type": "method" if func.parent_class else "function",
            "unit_name": func.name,
            "qualified_name": func.qualified_name,
            "line_start": func.start_line,
            "line_end": func.end_line,
            "summary": func_analysis.summary if func_analysis else "",
            "concepts": func_analysis.concepts if func_analysis else [],
            "nl_queries": func_analysis.nl_queries if func_analysis else [],
        })
        
        return Chunk(
            content=content,
            metadata=chunk_metadata,
            token_count=count_tokens(content)
        )
    
    def _create_class_chunk(
        self,
        cls,
        static,
        base_metadata: Dict[str, Any]
    ) -> Chunk:
        """Create chunk for a class (signature only, methods are separate)."""
        # Extract just the class definition line
        lines = cls.code.split('\n')
        class_def = lines[0] if lines else cls.code
        
        content = f"[Language: {static.language}]\n\n[Class Definition]\n```{static.language}\n{class_def}\n```\n\n[Methods: {', '.join(cls.methods)}]"
        
        chunk_metadata = self._merge_metadata(base_metadata, {
            "chunk_type": "code",
            "language": static.language,
            "unit_type": "class",
            "unit_name": cls.name,
            "line_start": cls.start_line,
            "methods": cls.methods,
        })
        
        return Chunk(
            content=content,
            metadata=chunk_metadata,
            token_count=count_tokens(content)
        )


# Factory function
def get_code_chunker(config: Optional[ChunkingConfig] = None) -> CodeChunker:
    return CodeChunker(config)
