# ✨ Generation & Validation - Grounded Content with Citations

> **Goal**: Generate accurate, well-cited learning materials with minimal hallucination  
> **Key Principle**: Every claim must trace back to source material

---

## 📋 Table of Contents

1. [Generation Philosophy](#generation-philosophy)
2. [Prompt Engineering for Grounded Generation](#prompt-engineering-for-grounded-generation)
3. [Citation System](#citation-system)
4. [Content Generation Pipelines](#content-generation-pipelines)
5. [Validation Framework](#validation-framework)
6. [Code Validation](#code-validation)
7. [Self-Evaluation with Explainability](#self-evaluation-with-explainability)

---

## 🎯 Generation Philosophy

### The Grounding Imperative

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    GROUNDED GENERATION PRINCIPLES                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ❌ HALLUCINATION PATTERN:                                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Query: "Explain quicksort"                                      │   │
│  │  Context: [sorting slides, bubble sort code]                     │   │
│  │  Output: "Quicksort has O(n) average complexity..."  ← WRONG!   │   │
│  │                                                                  │   │
│  │  Problem: LLM used its training data, not the context           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ✅ GROUNDED PATTERN:                                                   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Query: "Explain quicksort"                                      │   │
│  │  Context: [sorting slides mentioning quicksort on slide 15]     │   │
│  │  Output: "According to the lecture slides [slide 15],            │   │
│  │           quicksort uses divide-and-conquer with O(n log n)     │   │
│  │           average complexity..."  ← CORRECT + CITED             │   │
│  │                                                                  │   │
│  │  Key: Explicit instruction to ONLY use provided context         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  VALIDATION LAYER:                                                      │
│  Every generated statement is checked against source material          │
│  Ungrounded claims are flagged or removed                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Generation Goals

| Goal | Strategy | Metric |
|------|----------|--------|
| **Accuracy** | Ground in retrieved context | Faithfulness > 0.95 |
| **Completeness** | Use all relevant sources | Coverage > 0.85 |
| **Citations** | Page/slide-level references | 100% cited claims |
| **Clarity** | Student-appropriate language | Readability score |
| **Structure** | Markdown with clear hierarchy | Format compliance |

---

## 📝 Prompt Engineering for Grounded Generation

### Core Generation Prompt Template

```python
GROUNDED_GENERATION_PROMPT = """
You are an educational assistant helping students learn course material.
Your task is to generate helpful content based EXCLUSIVELY on the provided context.

<critical_rules>
1. ONLY use information from the provided context
2. If the context doesn't contain enough information, say so clearly
3. ALWAYS cite your sources using the provided citation keys
4. Use student-friendly language appropriate for the course level
5. Structure your response with clear headings and organization
6. For code explanations, include the relevant code snippets
</critical_rules>

<query>
{user_query}
</query>

<query_analysis>
Intent: {query_intent}
Key concepts: {entities}
</query_analysis>

<retrieved_context>
{context_string}
</retrieved_context>

<citation_format>
When citing sources, use this format:
- For slides: "According to [Slide X]..." or "...as shown in [Slide X]"
- For documents: "The textbook states [Page Y]..." or "...[Page Y]"
- For code: "In the code example [filename:lines]..."

Every factual claim must have a citation. If you cannot cite a claim, do not make it.
</citation_format>

<output_format>
Provide your response in Markdown format with:
1. A brief introduction addressing the query
2. Main content organized with headers (##, ###)
3. Code blocks with language tags when relevant
4. A "Sources" section at the end listing all citations used

Example structure:
## [Topic]

[Introduction with citation]

### [Subtopic 1]
[Content with citations]

### [Subtopic 2]
[Content with citations]

---
**Sources:**
- [Slide 15]: Lecture 5 - Sorting Algorithms
- [Page 42]: Textbook Chapter 3
</output_format>

Generate your response:
"""
```

### Intent-Specific Prompts

```python
class GenerationPrompts:
    """
    Specialized prompts for different query intents.
    """
    
    CONCEPTUAL_EXPLANATION = """
{base_prompt}

<additional_instructions>
For this conceptual explanation:
1. Start with a high-level overview
2. Break down complex concepts into digestible parts
3. Use analogies if they appear in the source material
4. Include any examples from the context
5. Highlight key takeaways at the end

Focus on helping the student UNDERSTAND, not just memorize.
</additional_instructions>
"""

    CODE_EXPLANATION = """
{base_prompt}

<additional_instructions>
For this code explanation:
1. First show the complete code with proper syntax highlighting
2. Walk through the code section by section
3. Explain the purpose of each significant line/block
4. Highlight the algorithm or pattern being demonstrated
5. Note any edge cases or important considerations
6. Include complexity analysis if mentioned in the context

Format code blocks as:
```{language}
// Code here with inline comments
```
</additional_instructions>
"""

    COMPARISON = """
{base_prompt}

<additional_instructions>
For this comparison:
1. Create a structured comparison (table if appropriate)
2. Identify key dimensions of comparison
3. Present each option's strengths and weaknesses
4. Only compare aspects mentioned in the context
5. Conclude with guidance on when to use each

Use a table format when comparing 2+ items across multiple dimensions.
</additional_instructions>
"""

    EXAMPLE_REQUEST = """
{base_prompt}

<additional_instructions>
For this example request:
1. Provide concrete examples from the context
2. For code examples, show complete working snippets
3. Explain what the example demonstrates
4. If multiple examples exist, order from simple to complex
5. Highlight the key learning point of each example
</additional_instructions>
"""
```

---

## 📚 Citation System

### Citation Tracking Architecture

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class CitationType(str, Enum):
    SLIDE = "slide"
    PAGE = "page"
    CODE = "code"
    SECTION = "section"


@dataclass
class Citation:
    """Represents a single citation to source material."""
    
    # Unique identifier
    citation_id: str
    
    # Source information
    document_id: str
    document_title: str
    source_file: str
    
    # Location
    citation_type: CitationType
    location: str  # "Slide 15", "Page 42", "lines 10-25"
    
    # For display
    display_key: str  # "[Slide 15]", "[Page 42]"
    full_reference: str  # "Lecture 5 - Sorting Algorithms, Slide 15"
    
    # Content excerpt (for validation)
    source_excerpt: str = ""


@dataclass
class CitedContent:
    """Generated content with citation tracking."""
    
    content: str
    citations_used: List[Citation]
    citation_map: Dict[str, Citation]  # display_key -> Citation
    
    # Validation results
    is_validated: bool = False
    validation_score: float = 0.0
    ungrounded_claims: List[str] = field(default_factory=list)


class CitationManager:
    """
    Manages citations throughout the generation pipeline.
    """
    
    def __init__(self):
        self.citations: Dict[str, Citation] = {}
        self.citation_counter = 0
    
    def create_citation(self, chunk_metadata: dict) -> Citation:
        """
        Create a citation from chunk metadata.
        """
        
        self.citation_counter += 1
        citation_id = f"cite_{self.citation_counter}"
        
        # Determine citation type and location
        if slide := chunk_metadata.get('slide_number'):
            citation_type = CitationType.SLIDE
            location = f"Slide {slide}"
            display_key = f"[Slide {slide}]"
        elif page := chunk_metadata.get('page_number'):
            citation_type = CitationType.PAGE
            location = f"Page {page}"
            display_key = f"[Page {page}]"
        elif line_start := chunk_metadata.get('line_start'):
            citation_type = CitationType.CODE
            line_end = chunk_metadata.get('line_end', line_start)
            func = chunk_metadata.get('function_name', '')
            location = f"lines {line_start}-{line_end}"
            display_key = f"[{chunk_metadata.get('source_file', 'code')}:{location}]"
            if func:
                display_key = f"[{func}]"
        else:
            citation_type = CitationType.SECTION
            section = chunk_metadata.get('section', 'Unknown')
            location = section
            display_key = f"[{section}]"
        
        # Build full reference
        doc_title = chunk_metadata.get(
            'document_title',
            chunk_metadata.get('source_file', 'Unknown')
        )
        full_reference = f"{doc_title}, {location}"
        
        citation = Citation(
            citation_id=citation_id,
            document_id=chunk_metadata.get('document_id', ''),
            document_title=doc_title,
            source_file=chunk_metadata.get('source_file', ''),
            citation_type=citation_type,
            location=location,
            display_key=display_key,
            full_reference=full_reference
        )
        
        self.citations[citation_id] = citation
        return citation
    
    def format_sources_section(self, used_citations: List[Citation]) -> str:
        """
        Format the Sources section for the generated output.
        """
        
        if not used_citations:
            return ""
        
        lines = ["", "---", "**Sources:**"]
        
        # Group by document
        by_document: Dict[str, List[Citation]] = {}
        for cite in used_citations:
            doc = cite.document_title
            if doc not in by_document:
                by_document[doc] = []
            by_document[doc].append(cite)
        
        for doc_title, cites in by_document.items():
            locations = sorted(set(c.location for c in cites))
            locations_str = ", ".join(locations)
            lines.append(f"- **{doc_title}**: {locations_str}")
        
        return "\n".join(lines)
```

### Citation Injection in Generation

```python
class CitationAwareGenerator:
    """
    Generates content with proper citation tracking.
    """
    
    def __init__(self, llm_client, citation_manager: CitationManager):
        self.llm = llm_client
        self.citations = citation_manager
    
    async def generate(
        self,
        query: str,
        context: 'RetrievedContext',
        intent: 'QueryIntent'
    ) -> CitedContent:
        """
        Generate cited content from retrieved context.
        """
        
        # Build context string with citation markers
        context_with_citations = self._prepare_context(context)
        
        # Select appropriate prompt
        prompt = self._select_prompt(intent)
        
        # Generate content
        response = await self.llm.generate(
            prompt=prompt.format(
                user_query=query,
                query_intent=intent.value,
                entities=", ".join(context.query_entities),
                context_string=context_with_citations
            ),
            temperature=0.3,  # Lower temperature for accuracy
            max_tokens=2000
        )
        
        # Extract citations used in response
        used_citations = self._extract_used_citations(response)
        
        # Add sources section
        sources_section = self.citations.format_sources_section(used_citations)
        final_content = response + sources_section
        
        return CitedContent(
            content=final_content,
            citations_used=used_citations,
            citation_map={c.display_key: c for c in used_citations}
        )
    
    def _prepare_context(self, context: 'RetrievedContext') -> str:
        """
        Prepare context string with clear citation markers.
        """
        
        parts = []
        
        for chunk in context.chunks:
            citation = self.citations.create_citation(chunk['metadata'])
            
            # Store excerpt for validation
            citation.source_excerpt = chunk['content'][:500]
            
            # Format chunk with citation marker
            chunk_text = f"""
<source citation="{citation.display_key}">
[Source: {citation.full_reference}]

{chunk['content']}
</source>
"""
            parts.append(chunk_text)
        
        return "\n".join(parts)
    
    def _extract_used_citations(self, response: str) -> List[Citation]:
        """
        Extract which citations were actually used in the response.
        """
        
        import re
        
        used = []
        
        # Find all citation patterns like [Slide 15], [Page 42], etc.
        patterns = [
            r'\[Slide \d+\]',
            r'\[Page \d+\]',
            r'\[[\w_]+\.[\w]+:[\w\d\-]+\]',
            r'\[[\w_]+\]'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response)
            for match in matches:
                # Find corresponding citation
                for cite in self.citations.citations.values():
                    if cite.display_key == match:
                        if cite not in used:
                            used.append(cite)
        
        return used
```

---

## 🏭 Content Generation Pipelines

### Theory Content Generator

```python
class TheoryContentGenerator:
    """
    Generates theory learning materials (notes, explanations).
    """
    
    def __init__(self, llm_client, citation_manager):
        self.generator = CitationAwareGenerator(llm_client, citation_manager)
        self.validator = ContentValidator(llm_client)
    
    async def generate_study_notes(
        self,
        topic: str,
        context: 'RetrievedContext',
        format_options: dict = None
    ) -> CitedContent:
        """
        Generate comprehensive study notes for a topic.
        """
        
        prompt = f"""
Generate comprehensive study notes on "{topic}" based on the course materials.

Structure the notes as:
1. Overview (1-2 paragraphs)
2. Key Concepts (bulleted list with explanations)
3. Detailed Explanation (organized by subtopic)
4. Examples (from the source material)
5. Key Takeaways (summary points)

Remember: Only include information from the provided sources. Cite everything.
"""
        
        content = await self.generator.generate(
            query=prompt,
            context=context,
            intent=QueryIntent.CONCEPTUAL
        )
        
        # Validate
        validated = await self.validator.validate(content, context)
        
        return validated
    
    async def generate_concept_explanation(
        self,
        concept: str,
        context: 'RetrievedContext',
        detail_level: str = "intermediate"
    ) -> CitedContent:
        """
        Generate explanation of a specific concept.
        """
        
        detail_instructions = {
            "brief": "Keep the explanation concise, 2-3 paragraphs maximum.",
            "intermediate": "Provide a thorough explanation with examples.",
            "detailed": "Give an in-depth explanation covering all aspects."
        }
        
        prompt = f"""
Explain the concept of "{concept}" for a student.

{detail_instructions.get(detail_level, detail_instructions['intermediate'])}

Include:
- Definition
- Why it matters
- How it works
- Examples from the source material
- Common misconceptions (if mentioned in sources)
"""
        
        return await self.generator.generate(
            query=prompt,
            context=context,
            intent=QueryIntent.CONCEPTUAL
        )


class CodeContentGenerator:
    """
    Generates code-focused learning materials.
    """
    
    def __init__(self, llm_client, citation_manager):
        self.generator = CitationAwareGenerator(llm_client, citation_manager)
        self.code_validator = CodeValidator()
    
    async def generate_code_explanation(
        self,
        code_query: str,
        context: 'RetrievedContext',
        include_walkthrough: bool = True
    ) -> CitedContent:
        """
        Generate explanation of code from course materials.
        """
        
        walkthrough_instruction = """
Include a line-by-line walkthrough of the key parts of the code.
""" if include_walkthrough else ""
        
        prompt = f"""
Explain the following code concept: "{code_query}"

Based on the code examples in the context:
1. Show the relevant code
2. Explain what it does at a high level
3. {walkthrough_instruction}
4. Explain the algorithm/approach used
5. Note the time/space complexity if mentioned
6. Highlight key learning points
"""
        
        content = await self.generator.generate(
            query=prompt,
            context=context,
            intent=QueryIntent.CODE_EXPLAIN
        )
        
        # Validate code blocks
        content = await self._validate_code_blocks(content)
        
        return content
    
    async def _validate_code_blocks(self, content: CitedContent) -> CitedContent:
        """
        Validate any code blocks in the generated content.
        """
        
        import re
        
        # Extract code blocks
        code_pattern = r'```(\w+)\n(.*?)```'
        matches = re.findall(code_pattern, content.content, re.DOTALL)
        
        for language, code in matches:
            validation = await self.code_validator.validate(code, language)
            
            if not validation['valid']:
                # Add warning comment
                warning = f"\n<!-- Warning: Code may have issues: {validation['issues']} -->\n"
                content.content = content.content.replace(
                    f"```{language}\n{code}```",
                    f"```{language}\n{code}```{warning}"
                )
        
        return content
```

---

## ✅ Validation Framework

### Content Validator

```python
class ContentValidator:
    """
    Validates generated content against source material.
    
    Checks:
    1. Faithfulness: Are claims grounded in sources?
    2. Citation accuracy: Are citations correct?
    3. Completeness: Is relevant context used?
    4. Coherence: Is the content well-structured?
    """
    
    VALIDATION_PROMPT = """
You are a validation assistant. Check if the generated content is accurately 
grounded in the source material.

<generated_content>
{generated_content}
</generated_content>

<source_material>
{source_material}
</source_material>

Analyze the content and provide a JSON response:

{{
    "faithfulness_score": 0.0-1.0,
    "faithfulness_issues": [
        "List any claims not supported by sources"
    ],
    
    "citation_accuracy": 0.0-1.0,
    "citation_issues": [
        "List any incorrect or missing citations"
    ],
    
    "completeness_score": 0.0-1.0,
    "missing_information": [
        "Important source information not included"
    ],
    
    "overall_score": 0.0-1.0,
    "overall_assessment": "Brief assessment of content quality",
    
    "suggested_corrections": [
        "Specific corrections to improve accuracy"
    ]
}}

Be strict about faithfulness - if a claim cannot be traced to the sources,
flag it as an issue.
"""
    
    def __init__(self, llm_client):
        self.llm = llm_client
    
    async def validate(
        self,
        content: CitedContent,
        context: 'RetrievedContext'
    ) -> CitedContent:
        """
        Validate generated content against source context.
        """
        
        # Build source material string
        source_material = "\n\n---\n\n".join(
            f"[{c['metadata'].get('citation_key', 'Source')}]\n{c['content']}"
            for c in context.chunks
        )
        
        # Run validation
        prompt = self.VALIDATION_PROMPT.format(
            generated_content=content.content,
            source_material=source_material
        )
        
        response = await self.llm.generate(
            prompt=prompt,
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        validation = json.loads(response)
        
        # Update content with validation results
        content.is_validated = True
        content.validation_score = validation['overall_score']
        content.ungrounded_claims = validation['faithfulness_issues']
        
        # If score is below threshold, attempt correction
        if validation['overall_score'] < 0.8:
            content = await self._apply_corrections(
                content,
                validation['suggested_corrections']
            )
        
        return content
    
    async def _apply_corrections(
        self,
        content: CitedContent,
        corrections: List[str]
    ) -> CitedContent:
        """
        Apply suggested corrections to improve content.
        """
        
        if not corrections:
            return content
        
        correction_prompt = f"""
The following content needs corrections for accuracy:

<content>
{content.content}
</content>

<corrections_needed>
{chr(10).join(f"- {c}" for c in corrections)}
</corrections_needed>

Provide the corrected content. Remove or qualify any ungrounded claims.
Maintain the same structure and citations.
"""
        
        corrected = await self.llm.generate(
            prompt=correction_prompt,
            temperature=0.2
        )
        
        content.content = corrected
        return content


class GroundednessChecker:
    """
    Specialized checker for claim-level groundedness.
    """
    
    CLAIM_EXTRACTION_PROMPT = """
Extract all factual claims from this text. A claim is any statement that 
asserts something as true or factual.

<text>
{text}
</text>

Return JSON:
{{
    "claims": [
        {{
            "claim": "The factual statement",
            "citation_used": "[Citation] or null if none"
        }}
    ]
}}
"""
    
    CLAIM_VERIFICATION_PROMPT = """
Verify if this claim is supported by the source text.

<claim>
{claim}
</claim>

<source>
{source}
</source>

Return JSON:
{{
    "is_supported": true/false,
    "support_type": "direct|inferred|unsupported",
    "explanation": "Brief explanation",
    "relevant_excerpt": "Quote from source that supports/contradicts"
}}
"""
    
    async def check_groundedness(
        self,
        content: str,
        sources: List[dict]
    ) -> dict:
        """
        Check groundedness at the claim level.
        """
        
        # Extract claims
        claims_response = await self.llm.generate(
            prompt=self.CLAIM_EXTRACTION_PROMPT.format(text=content),
            response_format={"type": "json_object"}
        )
        claims = json.loads(claims_response)['claims']
        
        # Build source text
        source_text = "\n\n".join(s['content'] for s in sources)
        
        # Verify each claim
        results = []
        for claim_data in claims:
            verification = await self._verify_claim(
                claim_data['claim'],
                source_text
            )
            results.append({
                **claim_data,
                **verification
            })
        
        # Calculate scores
        supported = sum(1 for r in results if r['is_supported'])
        total = len(results)
        
        return {
            'claims': results,
            'total_claims': total,
            'supported_claims': supported,
            'groundedness_score': supported / total if total > 0 else 1.0,
            'unsupported_claims': [
                r['claim'] for r in results if not r['is_supported']
            ]
        }
```

---

## 💻 Code Validation

### Syntax and Execution Validation

```python
import subprocess
import tempfile
import os
from typing import Optional


class CodeValidator:
    """
    Validates code syntax and optionally executes tests.
    """
    
    SUPPORTED_LANGUAGES = {
        'python': {
            'extension': '.py',
            'syntax_check': ['python', '-m', 'py_compile'],
            'linter': ['flake8', '--max-line-length=120'],
            'executor': ['python']
        },
        'javascript': {
            'extension': '.js',
            'syntax_check': ['node', '--check'],
            'linter': ['eslint'],
            'executor': ['node']
        },
        'java': {
            'extension': '.java',
            'syntax_check': ['javac', '-Xlint:all'],
            'linter': None,
            'executor': ['java']
        },
        'cpp': {
            'extension': '.cpp',
            'syntax_check': ['g++', '-fsyntax-only', '-Wall'],
            'linter': None,
            'executor': None  # Requires compilation
        }
    }
    
    async def validate(
        self,
        code: str,
        language: str,
        run_tests: bool = False,
        test_cases: List[dict] = None
    ) -> dict:
        """
        Validate code syntax and optionally run tests.
        """
        
        result = {
            'valid': True,
            'syntax_valid': True,
            'lint_passed': True,
            'tests_passed': None,
            'issues': [],
            'warnings': []
        }
        
        lang_config = self.SUPPORTED_LANGUAGES.get(language.lower())
        if not lang_config:
            result['warnings'].append(f"Language '{language}' not supported for validation")
            return result
        
        # Create temp file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=lang_config['extension'],
            delete=False
        ) as f:
            f.write(code)
            temp_path = f.name
        
        try:
            # Syntax check
            syntax_result = await self._check_syntax(
                temp_path,
                lang_config['syntax_check']
            )
            result['syntax_valid'] = syntax_result['valid']
            if not syntax_result['valid']:
                result['valid'] = False
                result['issues'].extend(syntax_result['errors'])
            
            # Linting
            if lang_config['linter']:
                lint_result = await self._run_linter(
                    temp_path,
                    lang_config['linter']
                )
                result['lint_passed'] = lint_result['passed']
                result['warnings'].extend(lint_result['warnings'])
            
            # Tests
            if run_tests and test_cases and lang_config['executor']:
                test_result = await self._run_tests(
                    temp_path,
                    lang_config['executor'],
                    test_cases
                )
                result['tests_passed'] = test_result['passed']
                if not test_result['passed']:
                    result['issues'].extend(test_result['failures'])
        
        finally:
            os.unlink(temp_path)
        
        return result
    
    async def _check_syntax(
        self,
        file_path: str,
        check_command: List[str]
    ) -> dict:
        """
        Run syntax check on code file.
        """
        
        try:
            result = subprocess.run(
                check_command + [file_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return {'valid': True, 'errors': []}
            else:
                errors = result.stderr.strip().split('\n')
                return {'valid': False, 'errors': errors}
        
        except subprocess.TimeoutExpired:
            return {'valid': False, 'errors': ['Syntax check timed out']}
        except Exception as e:
            return {'valid': False, 'errors': [str(e)]}
    
    async def _run_linter(
        self,
        file_path: str,
        lint_command: List[str]
    ) -> dict:
        """
        Run linter on code file.
        """
        
        try:
            result = subprocess.run(
                lint_command + [file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            warnings = []
            if result.stdout:
                warnings = result.stdout.strip().split('\n')
            
            return {
                'passed': result.returncode == 0,
                'warnings': warnings
            }
        
        except Exception as e:
            return {'passed': True, 'warnings': [f'Linter error: {e}']}
    
    async def _run_tests(
        self,
        file_path: str,
        executor: List[str],
        test_cases: List[dict]
    ) -> dict:
        """
        Run test cases against code.
        
        Test case format:
        {
            'input': 'input to provide',
            'expected_output': 'expected output',
            'description': 'test description'
        }
        """
        
        failures = []
        passed = 0
        
        for test in test_cases:
            try:
                result = subprocess.run(
                    executor + [file_path],
                    input=test.get('input', ''),
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                actual = result.stdout.strip()
                expected = test['expected_output'].strip()
                
                if actual == expected:
                    passed += 1
                else:
                    failures.append({
                        'test': test.get('description', 'Unnamed test'),
                        'expected': expected,
                        'actual': actual
                    })
            
            except subprocess.TimeoutExpired:
                failures.append({
                    'test': test.get('description', 'Unnamed test'),
                    'error': 'Execution timed out'
                })
            except Exception as e:
                failures.append({
                    'test': test.get('description', 'Unnamed test'),
                    'error': str(e)
                })
        
        return {
            'passed': len(failures) == 0,
            'total': len(test_cases),
            'passed_count': passed,
            'failures': failures
        }
```

---

## 🔍 Self-Evaluation with Explainability

### Evaluation Agent

```python
class SelfEvaluationAgent:
    """
    LLM-based self-evaluation with explainability.
    
    Provides transparent assessment of generated content quality.
    """
    
    EVALUATION_PROMPT = """
Evaluate the quality of this generated educational content.

<query>
{query}
</query>

<generated_content>
{content}
</generated_content>

<source_material>
{sources}
</source_material>

Evaluate on these dimensions and provide scores (0-10) with explanations:

{{
    "accuracy": {{
        "score": 0-10,
        "explanation": "How accurately does the content reflect the sources?",
        "evidence": ["Specific examples of accurate/inaccurate information"]
    }},
    
    "completeness": {{
        "score": 0-10,
        "explanation": "Does it cover all relevant information from sources?",
        "missing": ["Any important information not included"]
    }},
    
    "clarity": {{
        "score": 0-10,
        "explanation": "Is it clear and understandable for students?",
        "suggestions": ["Ways to improve clarity"]
    }},
    
    "citation_quality": {{
        "score": 0-10,
        "explanation": "Are citations appropriate and accurate?",
        "issues": ["Any citation problems"]
    }},
    
    "educational_value": {{
        "score": 0-10,
        "explanation": "How helpful is this for learning?",
        "strengths": ["Educational strengths"],
        "improvements": ["Suggested improvements"]
    }},
    
    "overall": {{
        "score": 0-10,
        "summary": "Overall assessment",
        "confidence": "high|medium|low",
        "recommendation": "accept|revise|regenerate"
    }}
}}
"""
    
    def __init__(self, llm_client):
        self.llm = llm_client
    
    async def evaluate(
        self,
        query: str,
        content: CitedContent,
        context: 'RetrievedContext'
    ) -> dict:
        """
        Perform self-evaluation with explainability.
        """
        
        # Build sources string
        sources = "\n\n---\n\n".join(
            f"[{c['metadata'].get('citation_key', 'Source')}]:\n{c['content']}"
            for c in context.chunks
        )
        
        prompt = self.EVALUATION_PROMPT.format(
            query=query,
            content=content.content,
            sources=sources
        )
        
        response = await self.llm.generate(
            prompt=prompt,
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        evaluation = json.loads(response)
        
        # Calculate aggregate score
        dimension_scores = [
            evaluation['accuracy']['score'],
            evaluation['completeness']['score'],
            evaluation['clarity']['score'],
            evaluation['citation_quality']['score'],
            evaluation['educational_value']['score']
        ]
        evaluation['aggregate_score'] = sum(dimension_scores) / len(dimension_scores)
        
        return evaluation
    
    async def generate_improvement_report(
        self,
        evaluation: dict
    ) -> str:
        """
        Generate a human-readable improvement report.
        """
        
        report_parts = [
            "# Content Evaluation Report",
            "",
            f"**Overall Score:** {evaluation['overall']['score']}/10",
            f"**Recommendation:** {evaluation['overall']['recommendation'].upper()}",
            f"**Confidence:** {evaluation['overall']['confidence']}",
            "",
            "## Dimension Scores",
            ""
        ]
        
        dimensions = ['accuracy', 'completeness', 'clarity', 
                     'citation_quality', 'educational_value']
        
        for dim in dimensions:
            data = evaluation[dim]
            report_parts.append(f"### {dim.replace('_', ' ').title()}")
            report_parts.append(f"**Score:** {data['score']}/10")
            report_parts.append(f"**Assessment:** {data['explanation']}")
            report_parts.append("")
        
        # Improvement suggestions
        report_parts.append("## Suggested Improvements")
        
        if evaluation['clarity'].get('suggestions'):
            report_parts.append("### Clarity")
            for s in evaluation['clarity']['suggestions']:
                report_parts.append(f"- {s}")
        
        if evaluation['educational_value'].get('improvements'):
            report_parts.append("### Educational Value")
            for s in evaluation['educational_value']['improvements']:
                report_parts.append(f"- {s}")
        
        return "\n".join(report_parts)
```

---

## 📊 Generation Pipeline Integration

```python
class GenerationPipeline:
    """
    Complete generation pipeline with validation.
    """
    
    def __init__(
        self,
        llm_client,
        retrieval_pipeline: 'RetrievalPipeline'
    ):
        self.llm = llm_client
        self.retrieval = retrieval_pipeline
        self.citation_manager = CitationManager()
        
        self.theory_generator = TheoryContentGenerator(
            llm_client, self.citation_manager
        )
        self.code_generator = CodeContentGenerator(
            llm_client, self.citation_manager
        )
        self.validator = ContentValidator(llm_client)
        self.evaluator = SelfEvaluationAgent(llm_client)
    
    async def generate(
        self,
        query: str,
        course_id: str,
        validate: bool = True,
        evaluate: bool = True
    ) -> dict:
        """
        Full generation pipeline.
        
        Returns:
        {
            'content': CitedContent,
            'validation': validation results (if enabled),
            'evaluation': evaluation results (if enabled),
            'context': RetrievedContext
        }
        """
        
        # Step 1: Retrieve context
        context = await self.retrieval.retrieve(
            query=query,
            filters={'course_id': course_id}
        )
        
        # Step 2: Determine content type and generate
        query_processor = QueryProcessorAgent(self.llm)
        processed = await query_processor.process(query)
        
        if processed.intent in [QueryIntent.CODE_FIND, QueryIntent.CODE_EXPLAIN]:
            content = await self.code_generator.generate_code_explanation(
                query, context
            )
        else:
            content = await self.theory_generator.generate_concept_explanation(
                query, context
            )
        
        result = {
            'content': content,
            'context': context
        }
        
        # Step 3: Validate
        if validate:
            content = await self.validator.validate(content, context)
            result['validation'] = {
                'score': content.validation_score,
                'is_valid': content.validation_score >= 0.8,
                'issues': content.ungrounded_claims
            }
        
        # Step 4: Evaluate
        if evaluate:
            evaluation = await self.evaluator.evaluate(query, content, context)
            result['evaluation'] = evaluation
        
        return result
```

---

## 📁 Related Files

- **[05-RETRIEVAL-PIPELINE.md](./05-RETRIEVAL-PIPELINE.md)** - How context is retrieved
- **[07-IMPLEMENTATION-TEMPLATES.md](./07-IMPLEMENTATION-TEMPLATES.md)** - Complete code templates
