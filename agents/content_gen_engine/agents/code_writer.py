"""
Code Writer Agent.

Generates lab code with test cases.
"""

from typing import Optional, List
import json

from services.gemini_service import GeminiService, GenerationConfig, get_gemini_service
from content_gen_engine.schemas.content_tags import LabSpec, CodeSpec, TestCase
from utils.logger import logger


class CodeWriter:
    """
    Generates code-centric learning materials.
    
    Produces:
    - Starter code templates
    - Solution code
    - Test cases with I/O
    - Documentation
    """
    
    SUPPORTED_LANGUAGES = ["python", "javascript", "java", "cpp", "c"]
    
    CODE_PROMPT = '''You are an expert programming instructor. Generate code for a lab exercise.

<topic>
{topic}
</topic>

<language>
{language}
</language>

<requirements>
{requirements}
</requirements>

<context>
{context}
</context>

Generate a complete lab exercise. Return JSON:

{{
    "title": "Lab title",
    "description": "What the lab teaches",
    "objectives": ["Learning objective 1", "Learning objective 2"],
    "difficulty": "easy|medium|hard",
    "starter_code": {{
        "filename": "solution.{ext}",
        "code": "# Starter code with TODOs for student to complete",
        "description": "Template for students"
    }},
    "solution_code": {{
        "filename": "solution.{ext}",
        "code": "# Complete working solution",
        "description": "Reference solution"
    }},
    "test_cases": [
        {{
            "input": "test input",
            "expected_output": "expected output",
            "description": "What this tests",
            "is_hidden": false
        }}
    ],
    "hints": ["Hint 1", "Hint 2"]
}}
'''
    
    def __init__(self, llm: Optional[GeminiService] = None):
        """Initialize code writer."""
        self.llm = llm or get_gemini_service("pro")
    
    async def generate_lab(
        self,
        topic: str,
        language: str = "python",
        requirements: Optional[List[str]] = None,
        context: Optional[str] = None,
        difficulty: str = "medium"
    ) -> LabSpec:
        """
        Generate a complete lab exercise.
        
        Args:
            topic: Programming topic/problem
            language: Target programming language
            requirements: Specific requirements
            context: Optional retrieved context
            difficulty: easy/medium/hard
            
        Returns:
            LabSpec with code and tests
        """
        if language.lower() not in self.SUPPORTED_LANGUAGES:
            logger.warning(f"Language {language} may have limited support")
        
        ext_map = {
            "python": "py",
            "javascript": "js",
            "java": "java",
            "cpp": "cpp",
            "c": "c"
        }
        ext = ext_map.get(language.lower(), "txt")
        
        reqs = requirements or [f"Implement {topic}", "Include error handling", "Add comments"]
        
        prompt = self.CODE_PROMPT.format(
            topic=topic,
            language=language,
            requirements="\n".join(f"- {r}" for r in reqs),
            context=context or "Use best practices for the language.",
            ext=ext
        )
        
        try:
            result = await self.llm.generate_json(prompt)
            
            # Parse starter code
            starter = None
            if sc := result.get('starter_code'):
                starter = CodeSpec(
                    language=language,
                    filename=sc.get('filename', f'starter.{ext}'),
                    code=sc.get('code', ''),
                    description=sc.get('description', ''),
                    test_cases=[]
                )
            
            # Parse solution code
            solution = None
            if sol := result.get('solution_code'):
                solution = CodeSpec(
                    language=language,
                    filename=sol.get('filename', f'solution.{ext}'),
                    code=sol.get('code', ''),
                    description=sol.get('description', ''),
                    test_cases=[]
                )
            
            # Parse test cases
            tests = []
            for tc in result.get('test_cases', []):
                tests.append(TestCase(
                    input=str(tc.get('input', '')),
                    expected_output=str(tc.get('expected_output', '')),
                    description=tc.get('description'),
                    is_hidden=tc.get('is_hidden', False)
                ))
            
            return LabSpec(
                title=result.get('title', topic),
                description=result.get('description', ''),
                objectives=result.get('objectives', []),
                starter_code=starter,
                solution_code=solution,
                test_cases=tests,
                hints=result.get('hints', []),
                difficulty=result.get('difficulty', difficulty)
            )
            
        except Exception as e:
            logger.error(f"Lab generation failed: {e}")
            raise
    
    async def generate_code_only(
        self,
        prompt: str,
        language: str = "python"
    ) -> str:
        """
        Generate just code from a prompt.
        
        Args:
            prompt: Code generation prompt
            language: Target language
            
        Returns:
            Generated code string
        """
        code_prompt = f'''Generate {language} code for:
{prompt}

Return ONLY the code, no explanations. Include:
- Proper comments
- Type hints (if applicable)
- Error handling
'''
        
        config = GenerationConfig(temperature=0.2)  # Lower for code
        result = await self.llm.generate(code_prompt, config)
        
        # Extract code from markdown blocks if present
        if "```" in result:
            import re
            match = re.search(r'```(?:\w+)?\n(.*?)```', result, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return result.strip()
    
    async def generate_test_cases(
        self,
        code: str,
        language: str = "python",
        num_tests: int = 5
    ) -> List[TestCase]:
        """
        Generate test cases for existing code.
        
        Args:
            code: Code to test
            language: Programming language
            num_tests: Number of tests to generate
            
        Returns:
            List of TestCase objects
        """
        prompt = f'''Analyze this {language} code and generate {num_tests} test cases:

```{language}
{code}
```

Return JSON array:
[
    {{
        "input": "test input",
        "expected_output": "expected output",
        "description": "what this tests"
    }}
]

Include:
- Normal cases
- Edge cases
- Error cases if applicable
'''
        
        try:
            result = await self.llm.generate_json(prompt)
            
            tests = []
            items = result if isinstance(result, list) else result.get('test_cases', [])
            
            for tc in items:
                tests.append(TestCase(
                    input=str(tc.get('input', '')),
                    expected_output=str(tc.get('expected_output', '')),
                    description=tc.get('description')
                ))
            
            return tests
            
        except Exception as e:
            logger.error(f"Test generation failed: {e}")
            return []


# Factory
def get_code_writer() -> CodeWriter:
    """Get code writer instance."""
    return CodeWriter()
