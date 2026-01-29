"""
Code Processor Module - LLM-assisted code understanding for RAG.

Public API:
    - CodePreprocessor: Main preprocessing pipeline
    - get_code_preprocessor(): Factory function
    - StaticAnalyzer: AST-based static analysis
    - CodeAnalysisResult: Complete analysis output
"""

from .code_preprocessor import (
    CodePreprocessor,
    CodeAnalysisResult,
    get_code_preprocessor,
)
from .static_analyzer import (
    StaticAnalyzer,
    StaticAnalysisResult,
    FunctionInfo,
    ClassInfo,
    static_analyzer,
)
from .code_analyzer_agent import (
    CodeAnalyzerAgent,
    FileAnalysis,
    FunctionAnalysis,
    code_analyzer_agent,
)
from .nl_bridge_generator import (
    NLBridgeGenerator,
    nl_bridge_generator,
)

__all__ = [
    # Main API
    'CodePreprocessor',
    'get_code_preprocessor',
    'CodeAnalysisResult',
    
    # Static analysis
    'StaticAnalyzer',
    'StaticAnalysisResult',
    'FunctionInfo',
    'ClassInfo',
    'static_analyzer',
    
    # LLM analysis
    'CodeAnalyzerAgent',
    'FileAnalysis',
    'FunctionAnalysis',
    'code_analyzer_agent',
    
    # NL bridge
    'NLBridgeGenerator',
    'nl_bridge_generator',
]
