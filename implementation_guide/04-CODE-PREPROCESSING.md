# 🤖 Code Preprocessing - LLM-Assisted Code Understanding

> **Goal**: Transform code into searchable, understandable content  
> **Key Innovation**: Bridge the semantic gap between natural language queries and code

---

## 📋 Table of Contents

1. [The Code Search Problem](#the-code-search-problem)
2. [Preprocessing Pipeline Architecture](#preprocessing-pipeline-architecture)
3. [Code Analyzer Agent](#code-analyzer-agent)
4. [Function-Level Analysis](#function-level-analysis)
5. [Natural Language Bridge Generation](#natural-language-bridge-generation)
6. [Implementation Templates](#implementation-templates)

---

## 🎯 The Code Search Problem

### Why Code Search is Hard

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    THE SEMANTIC GAP PROBLEM                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Student Query:                                                         │
│  "How do I find an element in a sorted list efficiently?"               │
│                                                                         │
│  Actual Code:                                                           │
│  ┌─────────────────────────────────────────────────────────┐           │
│  │  def binary_search(arr, target):                         │           │
│  │      left, right = 0, len(arr) - 1                       │           │
│  │      while left <= right:                                │           │
│  │          mid = (left + right) // 2                       │           │
│  │          if arr[mid] == target:                          │           │
│  │              return mid                                  │           │
│  │          elif arr[mid] < target:                         │           │
│  │              left = mid + 1                              │           │
│  │          else:                                           │           │
│  │              right = mid - 1                             │           │
│  │      return -1                                           │           │
│  └─────────────────────────────────────────────────────────┘           │
│                                                                         │
│  ❌ Direct embedding similarity: LOW                                    │
│     - "find element" vs "binary_search" - different vocabulary          │
│     - "sorted list" vs "arr" - abstraction mismatch                     │
│     - "efficiently" vs algorithm implementation - concept gap           │
│                                                                         │
│  ✅ With LLM-Generated Bridge:                                          │
│     - Summary: "Efficiently finds an element in a sorted array"         │
│     - NL Queries: ["find element sorted list", "efficient search", ...] │
│     - Concepts: ["binary search", "divide and conquer", "O(log n)"]     │
│                                                                         │
│  Result: Query and code now share semantic space                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### The Solution: LLM-Assisted Preprocessing

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PREPROCESSING VALUE PROPOSITION                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Raw Code → LLM Analysis → Rich Metadata → Semantic Embedding           │
│                                                                         │
│  What we generate:                                                      │
│  1. Plain English summaries (what the code does)                        │
│  2. Algorithm/pattern identification                                    │
│  3. Natural language query variations (how students might ask)          │
│  4. Concept mapping (CS concepts demonstrated)                          │
│  5. Complexity analysis                                                 │
│  6. Pedagogical context (learning goals, common mistakes)               │
│                                                                         │
│  Trade-off: ~$0.01-0.05 per file at ingestion vs. poor search forever  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Preprocessing Pipeline Architecture

### Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                  CODE PREPROCESSING PIPELINE                              │
└──────────────────────────────────────────────────────────────────────────┘

          ┌──────────────┐
          │  Code File   │
          │  (Any Lang)  │
          └──────┬───────┘
                 │
                 ▼
    ┌────────────────────────┐
    │   STATIC ANALYSIS      │  ◄── Fast, deterministic
    │   ├─ Language detect   │
    │   ├─ AST parsing       │
    │   ├─ Import extraction │
    │   ├─ Function listing  │
    │   └─ Dependency graph  │
    └────────────┬───────────┘
                 │
                 ▼
    ┌────────────────────────┐
    │   CODE ANALYZER AGENT  │  ◄── LLM-powered understanding
    │   (Gemini Flash)       │
    │   ├─ File-level        │
    │   │   analysis         │
    │   └─ Function-level    │
    │       analysis         │
    └────────────┬───────────┘
                 │
                 ▼
    ┌────────────────────────┐
    │   NL BRIDGE GENERATOR  │  ◄── Critical for search
    │   ├─ Query variations  │
    │   ├─ Synonym expansion │
    │   └─ Concept linking   │
    └────────────┬───────────┘
                 │
                 ▼
    ┌────────────────────────┐
    │   METADATA ASSEMBLER   │
    │   ├─ Merge all data    │
    │   ├─ Validate schema   │
    │   └─ Store for chunker │
    └────────────────────────┘
```

### Pipeline Implementation

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import tree_sitter_languages as tsl
import json
from abc import ABC, abstractmethod


@dataclass
class StaticAnalysisResult:
    """Results from AST-based static analysis."""
    language: str
    imports: List[str]
    classes: List[Dict[str, Any]]
    functions: List[Dict[str, Any]]
    global_variables: List[str]
    dependencies: List[str]


@dataclass
class FunctionAnalysis:
    """LLM-generated analysis for a single function."""
    name: str
    summary: str
    what_it_does: str
    how_it_works: str
    when_to_use: str
    example_usage: Optional[str]
    time_complexity: Optional[str]
    space_complexity: Optional[str]
    concepts: List[str]
    nl_queries: List[str]


@dataclass
class CodeAnalysisResult:
    """Complete analysis of a code file."""
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
    
    # Natural language bridge
    nl_queries: List[str]
    keywords: List[str]
    related_topics: List[str]


class CodePreprocessor:
    """
    Main orchestrator for code preprocessing pipeline.
    
    Usage:
        preprocessor = CodePreprocessor(llm_client)
        result = await preprocessor.process(code, filename, course_context)
    """
    
    def __init__(self, llm_client, config: dict = None):
        self.llm = llm_client
        self.config = config or {}
        self.max_functions_to_analyze = config.get("max_functions", 20)
    
    async def process(
        self,
        code: str,
        filename: str,
        course_context: dict
    ) -> CodeAnalysisResult:
        """
        Full preprocessing pipeline for a code file.
        """
        
        # Step 1: Static Analysis (fast, no LLM)
        static = self._static_analysis(code, filename)
        
        # Step 2: File-Level LLM Analysis
        file_analysis = await self._analyze_file(
            code=code,
            static=static,
            course_context=course_context
        )
        
        # Step 3: Function-Level LLM Analysis
        function_analyses = await self._analyze_functions(
            code=code,
            static=static,
            course_context=course_context
        )
        
        # Step 4: Generate NL Bridge
        nl_bridge = await self._generate_nl_bridge(
            code=code,
            file_analysis=file_analysis,
            function_analyses=function_analyses,
            course_context=course_context
        )
        
        # Assemble final result
        return CodeAnalysisResult(
            static=static,
            **file_analysis,
            functions=function_analyses,
            **nl_bridge
        )
    
    def _static_analysis(self, code: str, filename: str) -> StaticAnalysisResult:
        """
        Fast AST-based analysis without LLM.
        """
        # Detect language from extension
        language = self._detect_language(filename)
        
        # Parse with tree-sitter
        parser = tsl.get_parser(language)
        tree = parser.parse(code.encode())
        
        # Extract components
        imports = self._extract_imports(tree, code, language)
        classes = self._extract_classes(tree, code, language)
        functions = self._extract_functions(tree, code, language)
        globals_vars = self._extract_globals(tree, code, language)
        
        # Analyze dependencies
        dependencies = self._analyze_dependencies(imports)
        
        return StaticAnalysisResult(
            language=language,
            imports=imports,
            classes=classes,
            functions=functions,
            global_variables=globals_vars,
            dependencies=dependencies
        )
    
    def _detect_language(self, filename: str) -> str:
        """Detect programming language from filename."""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.rs': 'rust',
            '.go': 'go',
            '.rb': 'ruby',
        }
        ext = '.' + filename.split('.')[-1].lower()
        return extension_map.get(ext, 'python')
```

---

## 🔍 Code Analyzer Agent

### Agent Design

```python
class CodeAnalyzerAgent:
    """
    LLM-powered agent for understanding code semantics.
    
    Design principles:
    1. Structured output via JSON mode
    2. Pedagogical focus (this is for learning)
    3. Search optimization (generate searchable content)
    """
    
    FILE_ANALYSIS_PROMPT = """
You are an expert code analyst helping to make code searchable for students.
Analyze this code file for educational purposes.

<code language="{language}" filename="{filename}">
{code}
</code>

<course_context>
Course: {course_name}
Category: {category}
Week: {week_number}
Topic: {topic}
</course_context>

<static_analysis>
Classes: {classes}
Functions: {functions}
Imports: {imports}
</static_analysis>

Analyze this code and provide a JSON response with EXACTLY this structure:

{{
    "purpose_summary": "2-3 sentences explaining what this code does, written for students who might search for it",
    
    "algorithms_used": [
        "List named algorithms (e.g., 'binary search', 'BFS', 'merge sort')",
        "Be specific and use standard CS terminology"
    ],
    
    "data_structures_used": [
        "List data structures (e.g., 'array', 'hash map', 'binary tree')",
        "Include both built-in and custom structures"
    ],
    
    "design_patterns": [
        "List design patterns if applicable (e.g., 'singleton', 'factory')",
        "Leave empty if none are obvious"
    ],
    
    "concepts_demonstrated": [
        "CS concepts this code teaches (e.g., 'recursion', 'dynamic programming')",
        "Include both fundamental and advanced concepts"
    ],
    
    "learning_goals": [
        "What students should learn from studying this code",
        "What skills they'll develop"
    ],
    
    "common_mistakes": [
        "Mistakes students might make when writing similar code",
        "Bugs they might introduce"
    ],
    
    "complexity": "beginner|intermediate|advanced|expert"
}}

Focus on ACCURACY and SEARCHABILITY. Your analysis will be used to help students find this code.
"""
    
    FUNCTION_ANALYSIS_PROMPT = """
Analyze this function for educational searchability.

<function language="{language}">
{function_code}
</function>

<context>
File: {filename}
Class: {parent_class}
Course: {course_name}
</context>

Provide a JSON response:

{{
    "summary": "One clear sentence describing what this function does",
    
    "what_it_does": "Simple explanation of the function's behavior (2-3 sentences)",
    
    "how_it_works": "Brief explanation of the algorithm/approach used",
    
    "when_to_use": "Scenarios where a student would use this function",
    
    "example_usage": "A single line showing how to call this function",
    
    "time_complexity": "Big-O time complexity (e.g., 'O(n)', 'O(log n)')",
    
    "space_complexity": "Big-O space complexity",
    
    "concepts": [
        "CS concepts demonstrated by this function"
    ],
    
    "nl_queries": [
        "5-8 natural language questions students might ask that this function answers",
        "Vary the phrasing: formal, casual, keyword-based",
        "Examples: 'how to sort a list', 'sorting algorithm python', 'arrange elements in order'"
    ]
}}
"""
    
    async def analyze_file(
        self,
        code: str,
        static: StaticAnalysisResult,
        course_context: dict
    ) -> dict:
        """
        Generate file-level analysis using LLM.
        """
        
        prompt = self.FILE_ANALYSIS_PROMPT.format(
            language=static.language,
            filename=course_context.get('filename', 'unknown'),
            code=code[:8000],  # Truncate if needed
            course_name=course_context.get('course_name', ''),
            category=course_context.get('category', 'lab'),
            week_number=course_context.get('week_number', ''),
            topic=course_context.get('topic', ''),
            classes=json.dumps(static.classes),
            functions=json.dumps([f['name'] for f in static.functions]),
            imports=json.dumps(static.imports),
        )
        
        response = await self.llm.generate(
            prompt=prompt,
            response_format={"type": "json_object"},
            temperature=0.1  # Low temperature for consistency
        )
        
        return json.loads(response)
    
    async def analyze_function(
        self,
        function_code: str,
        function_name: str,
        language: str,
        parent_class: Optional[str],
        course_context: dict
    ) -> FunctionAnalysis:
        """
        Generate function-level analysis.
        """
        
        prompt = self.FUNCTION_ANALYSIS_PROMPT.format(
            language=language,
            function_code=function_code,
            filename=course_context.get('filename', ''),
            parent_class=parent_class or 'None',
            course_name=course_context.get('course_name', ''),
        )
        
        response = await self.llm.generate(
            prompt=prompt,
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        data = json.loads(response)
        
        return FunctionAnalysis(
            name=function_name,
            **data
        )
    
    async def analyze_all_functions(
        self,
        code: str,
        static: StaticAnalysisResult,
        course_context: dict,
        max_functions: int = 20
    ) -> Dict[str, FunctionAnalysis]:
        """
        Analyze all functions in a file (with limit).
        
        Uses batching to reduce API calls.
        """
        
        functions = static.functions[:max_functions]
        
        # For small files, analyze individually
        if len(functions) <= 3:
            results = {}
            for func in functions:
                analysis = await self.analyze_function(
                    function_code=func['code'],
                    function_name=func['name'],
                    language=static.language,
                    parent_class=func.get('parent_class'),
                    course_context=course_context
                )
                results[func['name']] = analysis
            return results
        
        # For larger files, use batch analysis
        return await self._batch_analyze_functions(
            functions=functions,
            language=static.language,
            course_context=course_context
        )
    
    async def _batch_analyze_functions(
        self,
        functions: List[dict],
        language: str,
        course_context: dict
    ) -> Dict[str, FunctionAnalysis]:
        """
        Analyze multiple functions in a single LLM call.
        """
        
        # Build batch prompt
        functions_text = ""
        for i, func in enumerate(functions):
            functions_text += f"""
<function_{i} name="{func['name']}" parent_class="{func.get('parent_class', 'None')}">
{func['code']}
</function_{i}>
"""
        
        prompt = f"""
Analyze these functions from a {language} file for educational searchability.

{functions_text}

<context>
Course: {course_context.get('course_name', '')}
</context>

For EACH function, provide analysis. Return a JSON object where keys are function names:

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
        "nl_queries": ["...", "...", "..."]
    }},
    "function_name_2": {{ ... }}
}}
"""
        
        response = await self.llm.generate(
            prompt=prompt,
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=4000
        )
        
        data = json.loads(response)
        
        # Convert to FunctionAnalysis objects
        results = {}
        for func_name, analysis in data.items():
            results[func_name] = FunctionAnalysis(
                name=func_name,
                **analysis
            )
        
        return results
```

---

## 🔤 Natural Language Bridge Generation

### The Bridge Concept

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    NATURAL LANGUAGE BRIDGE                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  The "bridge" is additional text that:                                  │
│  1. Matches how students naturally phrase questions                     │
│  2. Contains synonyms and related terms                                 │
│  3. Links code to concepts students know                                │
│                                                                         │
│  Example for a binary search function:                                  │
│                                                                         │
│  Bridge Content:                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Natural language queries this code answers:                      │   │
│  │  - "how to search in a sorted array"                              │   │
│  │  - "find element in sorted list python"                           │   │
│  │  - "efficient search algorithm"                                   │   │
│  │  - "binary search implementation"                                 │   │
│  │  - "divide and conquer search"                                    │   │
│  │  - "O(log n) search"                                              │   │
│  │  - "look up value in sorted data"                                 │   │
│  │                                                                   │   │
│  │  Related concepts: binary search, divide and conquer, logarithmic│   │
│  │  time complexity, sorted data structures, search algorithms       │   │
│  │                                                                   │   │
│  │  Keywords: search, find, lookup, binary, sorted, efficient, log, │   │
│  │  array, list, element, target, index                              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  This bridge content is embedded ALONGSIDE the code, dramatically      │
│  improving the chance of matching student queries.                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Bridge Generator Implementation

```python
class NLBridgeGenerator:
    """
    Generates natural language content to bridge code and queries.
    """
    
    NL_BRIDGE_PROMPT = """
You are helping make code findable by students. Given this code analysis,
generate natural language content that will help students find this code
when searching.

<code_summary>
{purpose_summary}
</code_summary>

<algorithms>
{algorithms}
</algorithms>

<concepts>
{concepts}
</concepts>

<functions>
{functions_summary}
</functions>

<course_context>
Course: {course_name}
This is {category} material for week {week}.
</course_context>

Generate content to help students find this code. Return JSON:

{{
    "nl_queries": [
        "Generate 15-20 natural language questions/searches students might use",
        "Include various phrasings:",
        "- Formal: 'How do I implement X?'",
        "- Casual: 'code for X'",
        "- Problem-based: 'my X isn't working'",
        "- Concept-based: 'example of X pattern'",
        "- Task-based: 'sort a list', 'find maximum'",
        "Vary vocabulary and specificity"
    ],
    
    "keywords": [
        "Individual searchable terms",
        "Include: technical terms, casual equivalents, related concepts",
        "Example: ['sort', 'sorting', 'order', 'arrange', 'sequence', ...]"
    ],
    
    "related_topics": [
        "Broader CS topics this code relates to",
        "Topics a student studying this should know",
        "Example: ['algorithms', 'time complexity', 'data structures']"
    ]
}}

Focus on HOW STUDENTS ACTUALLY SEARCH, not formal terminology.
"""

    async def generate_bridge(
        self,
        file_analysis: dict,
        function_analyses: Dict[str, FunctionAnalysis],
        course_context: dict
    ) -> dict:
        """
        Generate the natural language bridge for a code file.
        """
        
        # Summarize functions for prompt
        functions_summary = []
        for name, analysis in function_analyses.items():
            functions_summary.append(
                f"- {name}: {analysis.summary}"
            )
        
        prompt = self.NL_BRIDGE_PROMPT.format(
            purpose_summary=file_analysis.get('purpose_summary', ''),
            algorithms=json.dumps(file_analysis.get('algorithms_used', [])),
            concepts=json.dumps(file_analysis.get('concepts_demonstrated', [])),
            functions_summary="\n".join(functions_summary),
            course_name=course_context.get('course_name', ''),
            category=course_context.get('category', 'lab'),
            week=course_context.get('week_number', '')
        )
        
        response = await self.llm.generate(
            prompt=prompt,
            response_format={"type": "json_object"},
            temperature=0.3  # Slightly higher for creativity
        )
        
        return json.loads(response)
    
    def merge_all_nl_queries(
        self,
        file_bridge: dict,
        function_analyses: Dict[str, FunctionAnalysis]
    ) -> List[str]:
        """
        Combine all NL queries from file and function level.
        Deduplicate and normalize.
        """
        
        all_queries = set()
        
        # File-level queries
        for q in file_bridge.get('nl_queries', []):
            all_queries.add(q.lower().strip())
        
        # Function-level queries
        for analysis in function_analyses.values():
            for q in analysis.nl_queries:
                all_queries.add(q.lower().strip())
        
        return list(all_queries)
```

---

## 📦 Complete Preprocessing Flow

### Putting It All Together

```python
class CodePreprocessingPipeline:
    """
    Complete preprocessing pipeline for code files.
    
    Usage:
        pipeline = CodePreprocessingPipeline(llm_client)
        result = await pipeline.process(code, filename, course_context)
        
        # Result can be passed to chunker
        chunks = code_chunker.chunk(code, result)
    """
    
    def __init__(self, llm_client):
        self.static_analyzer = StaticCodeAnalyzer()
        self.code_agent = CodeAnalyzerAgent(llm_client)
        self.bridge_generator = NLBridgeGenerator(llm_client)
    
    async def process(
        self,
        code: str,
        filename: str,
        course_context: dict
    ) -> CodeAnalysisResult:
        """
        Full preprocessing pipeline.
        
        Steps:
        1. Static analysis (AST parsing)
        2. File-level LLM analysis
        3. Function-level LLM analysis
        4. NL bridge generation
        5. Assemble final metadata
        """
        
        # ═══════════════════════════════════════════════════════════
        # STEP 1: Static Analysis
        # ═══════════════════════════════════════════════════════════
        print(f"[1/4] Static analysis: {filename}")
        
        static = self.static_analyzer.analyze(code, filename)
        
        # ═══════════════════════════════════════════════════════════
        # STEP 2: File-Level Analysis
        # ═══════════════════════════════════════════════════════════
        print(f"[2/4] File-level LLM analysis")
        
        file_analysis = await self.code_agent.analyze_file(
            code=code,
            static=static,
            course_context=course_context
        )
        
        # ═══════════════════════════════════════════════════════════
        # STEP 3: Function-Level Analysis
        # ═══════════════════════════════════════════════════════════
        print(f"[3/4] Function-level LLM analysis ({len(static.functions)} functions)")
        
        function_analyses = await self.code_agent.analyze_all_functions(
            code=code,
            static=static,
            course_context=course_context
        )
        
        # ═══════════════════════════════════════════════════════════
        # STEP 4: NL Bridge Generation
        # ═══════════════════════════════════════════════════════════
        print(f"[4/4] Generating NL bridge")
        
        nl_bridge = await self.bridge_generator.generate_bridge(
            file_analysis=file_analysis,
            function_analyses=function_analyses,
            course_context=course_context
        )
        
        # Merge all NL queries
        all_nl_queries = self.bridge_generator.merge_all_nl_queries(
            file_bridge=nl_bridge,
            function_analyses=function_analyses
        )
        
        # ═══════════════════════════════════════════════════════════
        # ASSEMBLE RESULT
        # ═══════════════════════════════════════════════════════════
        
        return CodeAnalysisResult(
            static=static,
            purpose_summary=file_analysis['purpose_summary'],
            algorithms_used=file_analysis['algorithms_used'],
            data_structures_used=file_analysis['data_structures_used'],
            design_patterns=file_analysis['design_patterns'],
            concepts_demonstrated=file_analysis['concepts_demonstrated'],
            learning_goals=file_analysis['learning_goals'],
            common_mistakes=file_analysis['common_mistakes'],
            complexity=file_analysis['complexity'],
            functions=function_analyses,
            nl_queries=all_nl_queries,
            keywords=nl_bridge['keywords'],
            related_topics=nl_bridge['related_topics']
        )
    
    def to_embedding_text(self, result: CodeAnalysisResult) -> str:
        """
        Convert analysis result to text optimized for embedding.
        
        This text will be embedded alongside the code chunks.
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
```

---

## 🎯 Example Output

### Input Code

```python
# sorting_demo.py
def quicksort(arr):
    """
    Sort array using quicksort algorithm.
    """
    if len(arr) <= 1:
        return arr
    
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    return quicksort(left) + middle + quicksort(right)
```

### Output Analysis

```json
{
  "purpose_summary": "Demonstrates the quicksort algorithm, a divide-and-conquer sorting technique that recursively partitions an array around a pivot element to achieve efficient O(n log n) average-case sorting.",
  
  "algorithms_used": ["quicksort", "divide and conquer"],
  
  "data_structures_used": ["array", "list"],
  
  "design_patterns": [],
  
  "concepts_demonstrated": [
    "recursion",
    "divide and conquer",
    "partitioning",
    "list comprehension",
    "pivot selection"
  ],
  
  "learning_goals": [
    "Understand how quicksort divides problems into subproblems",
    "Learn recursive algorithm design",
    "Understand average vs worst-case complexity"
  ],
  
  "common_mistakes": [
    "Choosing first/last element as pivot (leads to O(n²) on sorted input)",
    "Not handling empty arrays",
    "Incorrect partition logic"
  ],
  
  "complexity": "intermediate",
  
  "functions": {
    "quicksort": {
      "summary": "Sorts a list using the quicksort divide-and-conquer algorithm",
      "what_it_does": "Takes an unsorted list and returns a new sorted list by recursively partitioning around pivot elements",
      "how_it_works": "Selects middle element as pivot, partitions into smaller/equal/larger sublists, recursively sorts, and concatenates",
      "when_to_use": "When you need efficient general-purpose sorting with good average performance",
      "example_usage": "sorted_list = quicksort([3, 1, 4, 1, 5, 9, 2, 6])",
      "time_complexity": "O(n log n) average, O(n²) worst",
      "space_complexity": "O(n) due to list creation",
      "concepts": ["recursion", "partitioning", "divide and conquer"],
      "nl_queries": [
        "how to sort a list in python",
        "quicksort implementation",
        "fast sorting algorithm",
        "divide and conquer sorting",
        "sort array recursively",
        "efficient sort python"
      ]
    }
  },
  
  "nl_queries": [
    "how to sort a list",
    "sorting algorithm python",
    "quicksort code",
    "fast way to sort array",
    "divide and conquer sort",
    "recursive sorting",
    "sort numbers efficiently",
    "implement quicksort",
    "partition and sort",
    "sort list in place python",
    "comparison sort example",
    "nlogn sorting algorithm",
    "sort with pivot",
    "list sorting function"
  ],
  
  "keywords": [
    "sort", "sorting", "quicksort", "quick sort", "array", "list",
    "recursive", "recursion", "divide", "conquer", "partition",
    "pivot", "efficient", "fast", "algorithm", "order", "arrange"
  ],
  
  "related_topics": [
    "sorting algorithms",
    "recursion",
    "divide and conquer",
    "time complexity",
    "algorithm analysis"
  ]
}
```

---

## 💰 Cost Estimation

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PREPROCESSING COST ANALYSIS                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Assumptions:                                                           │
│  - Average file: 200 lines of code                                      │
│  - Average 5 functions per file                                         │
│  - Using Gemini Flash ($0.075/1M input, $0.30/1M output)               │
│                                                                         │
│  Per File Costs:                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Analysis Type        │ Input Tokens │ Output Tokens │ Cost       │   │
│  ├─────────────────────────────────────────────────────────────────┤   │
│  │ File-level analysis  │ ~2,000       │ ~500          │ $0.0003    │   │
│  │ Function analysis x5 │ ~3,000       │ ~1,500        │ $0.0007    │   │
│  │ NL bridge generation │ ~1,000       │ ~800          │ $0.0003    │   │
│  ├─────────────────────────────────────────────────────────────────┤   │
│  │ TOTAL PER FILE       │ ~6,000       │ ~2,800        │ ~$0.0013   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  Course Estimate (10 materials, 3 code files avg):                      │
│  - 30 code files × $0.0013 = ~$0.04 per course                         │
│                                                                         │
│  ROI: $0.04 one-time cost vs. dramatically improved code search        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Related Files

- **[03-CHUNKING-STRATEGIES.md](./03-CHUNKING-STRATEGIES.md)** - How preprocessed metadata is used
- **[05-RETRIEVAL-PIPELINE.md](./05-RETRIEVAL-PIPELINE.md)** - Searching with enriched code
- **[07-IMPLEMENTATION-TEMPLATES.md](./07-IMPLEMENTATION-TEMPLATES.md)** - Full code templates
