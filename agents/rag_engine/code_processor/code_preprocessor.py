"""
Code Preprocessor - Main orchestrator for code analysis pipeline.

Combines static analysis, LLM analysis, and NL bridge generation.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional

from .static_analyzer import StaticAnalyzer, StaticAnalysisResult
from .code_analyzer_agent import CodeAnalyzerAgent, FileAnalysis, FunctionAnalysis
from .nl_bridge_generator import NLBridgeGenerator
from utils.logger import logger


@dataclass
class CodeAnalysisResult:
    """Complete analysis result for a code file."""
    # Static analysis
    static: StaticAnalysisResult
    
    # LLM file-level analysis
    purpose_summary: str
    algorithms_used: List[str]
    data_structures_used: List[str]
    design_patterns: List[str]
    concepts_demonstrated: List[str]
    learning_goals: List[str]
    common_mistakes: List[str]
    complexity: str
    
    # Function-level analysis
    functions: Dict[str, FunctionAnalysis]
    
    # NL bridge
    nl_queries: List[str]
    keywords: List[str]
    related_topics: List[str]


class CodePreprocessor:
    """
    Main code preprocessing pipeline.
    
    Usage:
        preprocessor = CodePreprocessor()
        result = await preprocessor.process(code, filename)
        embedding_text = preprocessor.to_embedding_text(result)
    """
    
    def __init__(self, max_functions: int = 10):
        self.static_analyzer = StaticAnalyzer()
        self.code_agent = CodeAnalyzerAgent()
        self.bridge_generator = NLBridgeGenerator()
        self.max_functions = max_functions
    
    async def process(
        self,
        code: str,
        filename: str
    ) -> CodeAnalysisResult:
        """
        Full preprocessing pipeline for a code file.
        
        Args:
            code: Source code content
            filename: Name of the file
            
        Returns:
            Complete CodeAnalysisResult
        """
        logger.info(f"[1/4] Static analysis: {filename}")
        
        # Step 1: Static Analysis
        static = self.static_analyzer.analyze(code, filename)
        
        # Step 2: File-Level LLM Analysis
        logger.info(f"[2/4] File-level LLM analysis")
        
        file_analysis = await self.code_agent.analyze_file(
            code=code,
            filename=filename,
            language=static.language,
            functions=[f.name for f in static.functions],
            classes=[c.name for c in static.classes],
            imports=static.imports
        )
        
        # Step 3: Function-Level LLM Analysis
        logger.info(f"[3/4] Function-level analysis ({len(static.functions)} functions)")
        
        func_dicts = [
            {'name': f.name, 'code': f.code, 'parent_class': f.parent_class}
            for f in static.functions[:self.max_functions]
        ]
        
        function_analyses = await self.code_agent.analyze_functions_batch(
            functions=func_dicts,
            language=static.language,
            max_functions=self.max_functions
        )
        
        # Step 4: NL Bridge Generation
        logger.info(f"[4/4] Generating NL bridge")
        
        functions_summary = [
            f"{name}: {analysis.summary}"
            for name, analysis in function_analyses.items()
        ]
        
        nl_bridge = await self.bridge_generator.generate_bridge(
            purpose_summary=file_analysis.purpose_summary,
            algorithms=file_analysis.algorithms_used,
            concepts=file_analysis.concepts_demonstrated,
            functions_summary=functions_summary
        )
        
        # Merge all NL queries
        all_nl_queries = self.bridge_generator.merge_all_nl_queries(
            file_bridge=nl_bridge,
            function_analyses=function_analyses
        )
        
        return CodeAnalysisResult(
            static=static,
            purpose_summary=file_analysis.purpose_summary,
            algorithms_used=file_analysis.algorithms_used,
            data_structures_used=file_analysis.data_structures_used,
            design_patterns=file_analysis.design_patterns,
            concepts_demonstrated=file_analysis.concepts_demonstrated,
            learning_goals=file_analysis.learning_goals,
            common_mistakes=file_analysis.common_mistakes,
            complexity=file_analysis.complexity,
            functions=function_analyses,
            nl_queries=all_nl_queries,
            keywords=nl_bridge.get('keywords', []),
            related_topics=nl_bridge.get('related_topics', [])
        )
    
    def to_embedding_text(self, result: CodeAnalysisResult) -> str:
        """
        Convert analysis to text optimized for embedding.
        
        This text is embedded alongside code chunks for better search.
        """
        parts = [
            f"[Purpose] {result.purpose_summary}",
            f"[Algorithms] {', '.join(result.algorithms_used)}",
            f"[Concepts] {', '.join(result.concepts_demonstrated)}",
            f"[This code can help with:]",
        ]
        
        for query in result.nl_queries[:10]:
            parts.append(f"- {query}")
        
        parts.append(f"[Keywords] {', '.join(result.keywords)}")
        
        return "\n".join(parts)
    
    def to_dict(self, result: CodeAnalysisResult) -> dict:
        """Convert result to dictionary for serialization."""
        return {
            'language': result.static.language,
            'imports': result.static.imports,
            'classes': [c.name for c in result.static.classes],
            'functions': {
                name: {
                    'summary': fa.summary,
                    'what_it_does': fa.what_it_does,
                    'concepts': fa.concepts,
                    'nl_queries': fa.nl_queries,
                    'time_complexity': fa.time_complexity,
                    'space_complexity': fa.space_complexity,
                }
                for name, fa in result.functions.items()
            },
            'purpose_summary': result.purpose_summary,
            'algorithms_used': result.algorithms_used,
            'data_structures_used': result.data_structures_used,
            'concepts_demonstrated': result.concepts_demonstrated,
            'nl_queries': result.nl_queries,
            'keywords': result.keywords,
            'complexity': result.complexity,
        }


# Factory function
def get_code_preprocessor(max_functions: int = 10) -> CodePreprocessor:
    """Create a code preprocessor instance."""
    return CodePreprocessor(max_functions=max_functions)
