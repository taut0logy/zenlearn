"""
LLM-powered Code Analyzer Agent.

Uses Gemini to generate semantic understanding of code for better searchability.
"""

import json
from typing import Dict, Optional, List
from dataclasses import dataclass, field

from services.gemini_service import gemini_service
from utils.logger import logger


@dataclass
class FunctionAnalysis:
    """LLM-generated analysis for a function."""
    name: str
    summary: str
    what_it_does: str
    how_it_works: str
    when_to_use: str
    example_usage: Optional[str] = None
    time_complexity: Optional[str] = None
    space_complexity: Optional[str] = None
    concepts: List[str] = field(default_factory=list)
    nl_queries: List[str] = field(default_factory=list)


@dataclass
class FileAnalysis:
    """LLM-generated analysis for a file."""
    purpose_summary: str
    algorithms_used: List[str]
    data_structures_used: List[str]
    design_patterns: List[str]
    concepts_demonstrated: List[str]
    learning_goals: List[str]
    common_mistakes: List[str]
    complexity: str  # beginner/intermediate/advanced


class CodeAnalyzerAgent:
    """LLM agent for understanding code semantics."""
    
    FILE_ANALYSIS_PROMPT = """You are an expert code analyst. Analyze this code file for educational searchability.

<code language="{language}" filename="{filename}">
{code}
</code>

<context>
Functions: {functions}
Classes: {classes}
Imports: {imports}
</context>

Respond with JSON ONLY (no markdown):
{{
    "purpose_summary": "2-3 sentences explaining what this code does",
    "algorithms_used": ["list of algorithms used"],
    "data_structures_used": ["list of data structures"],
    "design_patterns": ["design patterns if any"],
    "concepts_demonstrated": ["CS concepts this teaches"],
    "learning_goals": ["what students learn from this"],
    "common_mistakes": ["typical mistakes when writing similar code"],
    "complexity": "beginner|intermediate|advanced"
}}"""

    FUNCTION_ANALYSIS_PROMPT = """Analyze this function for educational searchability.

<function language="{language}">
{function_code}
</function>

<context>
File: {filename}
Class: {parent_class}
</context>

Respond with JSON ONLY (no markdown):
{{
    "summary": "One clear sentence describing what this function does",
    "what_it_does": "Simple explanation (2-3 sentences)",
    "how_it_works": "Brief algorithm/approach explanation",
    "when_to_use": "Scenarios where to use this",
    "example_usage": "Single line showing how to call it",
    "time_complexity": "Big-O time (e.g., O(n))",
    "space_complexity": "Big-O space",
    "concepts": ["CS concepts demonstrated"],
    "nl_queries": ["5-8 natural language questions students might ask that this answers"]
}}"""

    BATCH_FUNCTION_PROMPT = """Analyze these functions from a {language} file.

{functions_text}

For EACH function, provide analysis. Respond with JSON ONLY (no markdown):
{{
    "function_name_1": {{
        "summary": "...",
        "what_it_does": "...",
        "how_it_works": "...",
        "when_to_use": "...",
        "example_usage": "...",
        "time_complexity": "...",
        "space_complexity": "...",
        "concepts": ["..."],
        "nl_queries": ["...", "..."]
    }},
    "function_name_2": {{ ... }}
}}"""

    async def analyze_file(
        self,
        code: str,
        filename: str,
        language: str,
        functions: List[str],
        classes: List[str],
        imports: List[str]
    ) -> FileAnalysis:
        """Generate file-level analysis."""
        prompt = self.FILE_ANALYSIS_PROMPT.format(
            language=language,
            filename=filename,
            code=code[:8000],  # Truncate if too long
            functions=json.dumps(functions),
            classes=json.dumps(classes),
            imports=json.dumps(imports[:10])
        )
        
        try:
            response = await gemini_service.generate_response(prompt)
            data = self._parse_json(response)
            
            return FileAnalysis(
                purpose_summary=data.get('purpose_summary', ''),
                algorithms_used=data.get('algorithms_used', []),
                data_structures_used=data.get('data_structures_used', []),
                design_patterns=data.get('design_patterns', []),
                concepts_demonstrated=data.get('concepts_demonstrated', []),
                learning_goals=data.get('learning_goals', []),
                common_mistakes=data.get('common_mistakes', []),
                complexity=data.get('complexity', 'intermediate')
            )
        except Exception as e:
            logger.error(f"Error in file analysis: {e}")
            return FileAnalysis(
                purpose_summary="Unable to analyze",
                algorithms_used=[],
                data_structures_used=[],
                design_patterns=[],
                concepts_demonstrated=[],
                learning_goals=[],
                common_mistakes=[],
                complexity="intermediate"
            )
    
    async def analyze_function(
        self,
        function_code: str,
        function_name: str,
        language: str,
        filename: str = "",
        parent_class: Optional[str] = None
    ) -> FunctionAnalysis:
        """Generate function-level analysis."""
        prompt = self.FUNCTION_ANALYSIS_PROMPT.format(
            language=language,
            function_code=function_code,
            filename=filename,
            parent_class=parent_class or "None"
        )
        
        try:
            response = await gemini_service.generate_response(prompt)
            data = self._parse_json(response)
            
            return FunctionAnalysis(
                name=function_name,
                summary=data.get('summary', ''),
                what_it_does=data.get('what_it_does', ''),
                how_it_works=data.get('how_it_works', ''),
                when_to_use=data.get('when_to_use', ''),
                example_usage=data.get('example_usage'),
                time_complexity=data.get('time_complexity'),
                space_complexity=data.get('space_complexity'),
                concepts=data.get('concepts', []),
                nl_queries=data.get('nl_queries', [])
            )
        except Exception as e:
            logger.error(f"Error analyzing function {function_name}: {e}")
            return FunctionAnalysis(
                name=function_name,
                summary="Unable to analyze",
                what_it_does="",
                how_it_works="",
                when_to_use=""
            )
    
    async def analyze_functions_batch(
        self,
        functions: List[Dict],
        language: str,
        max_functions: int = 10
    ) -> Dict[str, FunctionAnalysis]:
        """Analyze multiple functions in a single LLM call."""
        functions = functions[:max_functions]
        
        if len(functions) <= 2:
            # For small counts, analyze individually
            results = {}
            for func in functions:
                analysis = await self.analyze_function(
                    function_code=func['code'],
                    function_name=func['name'],
                    language=language,
                    parent_class=func.get('parent_class')
                )
                results[func['name']] = analysis
            return results
        
        # Build batch prompt
        functions_text = ""
        for i, func in enumerate(functions):
            functions_text += f"""
<function_{i} name="{func['name']}" parent_class="{func.get('parent_class', 'None')}">
{func['code']}
</function_{i}>
"""
        
        prompt = self.BATCH_FUNCTION_PROMPT.format(
            language=language,
            functions_text=functions_text
        )
        
        try:
            response = await gemini_service.generate_response(prompt)
            data = self._parse_json(response)
            
            results = {}
            for name, analysis in data.items():
                results[name] = FunctionAnalysis(
                    name=name,
                    summary=analysis.get('summary', ''),
                    what_it_does=analysis.get('what_it_does', ''),
                    how_it_works=analysis.get('how_it_works', ''),
                    when_to_use=analysis.get('when_to_use', ''),
                    example_usage=analysis.get('example_usage'),
                    time_complexity=analysis.get('time_complexity'),
                    space_complexity=analysis.get('space_complexity'),
                    concepts=analysis.get('concepts', []),
                    nl_queries=analysis.get('nl_queries', [])
                )
            return results
        except Exception as e:
            logger.error(f"Error in batch analysis: {e}")
            return {}
    
    def _parse_json(self, response: str) -> dict:
        """Parse JSON from LLM response, handling markdown code blocks."""
        text = response.strip()
        
        # Remove markdown code blocks if present
        if text.startswith('```'):
            lines = text.split('\n')
            text = '\n'.join(lines[1:-1] if lines[-1] == '```' else lines[1:])
        
        return json.loads(text)


# Singleton instance
code_analyzer_agent = CodeAnalyzerAgent()
