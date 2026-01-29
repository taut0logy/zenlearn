"""
Query Processor - LLM-powered query understanding.

Analyzes user queries to extract intent, entities, and generate
optimized search queries for hybrid retrieval.
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any

from services.gemini_service import GeminiService
from utils.logger import logger


class QueryIntent(str, Enum):
    """Types of queries the system handles."""
    FACTUAL = "factual"           # "What is binary search?"
    CONCEPTUAL = "conceptual"     # "How does binary search work?"
    CODE_FIND = "code_find"       # "Show me binary search code"
    CODE_EXPLAIN = "code_explain" # "Explain this sorting algorithm"
    COMPARE = "compare"           # "Difference between BFS and DFS"
    EXAMPLE = "example"           # "Give me an example of recursion"
    EXERCISE = "exercise"         # "Practice problems for sorting"


@dataclass
class ProcessedQuery:
    """Result of query processing."""
    original: str
    intent: QueryIntent
    entities: List[str] = field(default_factory=list)
    filters: Dict[str, str] = field(default_factory=dict)
    expanded_queries: List[str] = field(default_factory=list)
    hyde_text: Optional[str] = None
    is_code_query: bool = False
    specificity: str = "focused"


class QueryProcessor:
    """
    LLM-powered query understanding for optimal retrieval.
    
    Responsibilities:
    - Classify query intent
    - Extract entities and filters
    - Generate expanded search queries
    - Optional HyDE for conceptual queries
    """
    
    QUERY_ANALYSIS_PROMPT = """Analyze this student query for a course learning platform.

<query>
{query}
</query>

<available_filters>
- course_id: Filter by specific course
- category: "theory" or "lab"
- content_type: "slides", "document", "code"
- week_number: 1-16
- language: Programming language for code
</available_filters>

Return JSON with EXACTLY this structure:
{{
    "intent": "factual|conceptual|code_find|code_explain|compare|example|exercise",
    "entities": ["key concepts or terms from the query"],
    "filters": {{}},
    "search_queries": ["2-3 reformulated queries for search"],
    "is_code_query": true or false,
    "specificity": "broad|focused|specific"
}}"""

    HYDE_PROMPT = """Write a brief, factual answer to this student question as it might appear
in course materials. Write 2-3 sentences, focusing on accuracy.

Question: {query}
Context: This is for a {intent} query about {entities}.

Answer:"""

    def __init__(self, llm_service: Optional[GeminiService] = None):
        self.llm = llm_service or GeminiService()
    
    async def process(self, query: str, context: Optional[Dict] = None) -> ProcessedQuery:
        """
        Process user query for optimal retrieval.
        
        Args:
            query: Raw user query
            context: Optional context (course info, etc.)
            
        Returns:
            ProcessedQuery with intent, entities, expanded queries
        """
        try:
            # Step 1: LLM Analysis
            analysis = await self._analyze_query(query)
            
            # Step 2: Clean filters (LLM often returns invalid ones)
            clean_filters = self._clean_filters(analysis.get('filters', {}))
            
            # Step 3: Build expanded queries
            expanded = self._build_expanded_queries(query, analysis)
            
            # Step 4: Optional HyDE for conceptual queries
            hyde_text = None
            if analysis.get('intent') in ['conceptual', 'code_explain']:
                hyde_text = await self._generate_hyde(query, analysis)
            
            return ProcessedQuery(
                original=query,
                intent=QueryIntent(analysis.get('intent', 'factual')),
                entities=analysis.get('entities', []),
                filters=clean_filters,  # Use cleaned filters
                expanded_queries=expanded,
                hyde_text=hyde_text,
                is_code_query=analysis.get('is_code_query', False),
                specificity=analysis.get('specificity', 'focused')
            )
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            # Fallback to basic processing
            return ProcessedQuery(
                original=query,
                intent=QueryIntent.FACTUAL,
                expanded_queries=[query],
                filters={},  # Empty filters for fallback
            )
    
    async def _analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze query with LLM."""
        prompt = self.QUERY_ANALYSIS_PROMPT.format(query=query)
        
        response = await self.llm.generate_response(prompt)
        
        # Parse JSON from response
        try:
            # Extract JSON from response
            text = response.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse query analysis, using defaults")
            return {
                "intent": "factual",
                "entities": query.split()[:5],
                "search_queries": [query],
                "is_code_query": any(kw in query.lower() for kw in ['code', 'function', 'implement']),
                "filters": {},  # Empty filters for fallback
            }
    
    def _clean_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean and validate filters from LLM response.
        
        Only allows known filter keys with valid values.
        """
        if not filters or not isinstance(filters, dict):
            return {}
        
        # Valid filter keys that match our metadata schema
        valid_keys = {
            'course_id', 'category', 'content_type', 
            'week_number', 'language', 'file_type', 'chunk_type'
        }
        
        cleaned = {}
        for key, value in filters.items():
            # Skip unknown keys
            if key not in valid_keys:
                continue
            # Skip empty or None values
            if value is None or value == "":
                continue
            # Only allow primitive types
            if isinstance(value, (str, int, float, bool)):
                cleaned[key] = value
        
        return cleaned
    
    def _build_expanded_queries(self, query: str, analysis: Dict) -> List[str]:
        """Generate expanded query variants."""
        queries = [query]  # Always include original
        
        # Add LLM-generated variants
        queries.extend(analysis.get('search_queries', []))
        
        # Add entity-based queries
        for entity in analysis.get('entities', []):
            if entity.lower() not in query.lower():
                queries.append(entity)
        
        # For code queries, add programming-specific variants
        if analysis.get('is_code_query'):
            queries.append(f"{query} code")
            queries.append(f"{query} implementation")
            queries.append(f"{query} example")
        
        # Deduplicate while preserving order
        seen = set()
        unique = []
        for q in queries:
            q_lower = q.lower().strip()
            if q_lower and q_lower not in seen:
                seen.add(q_lower)
                unique.append(q)
        
        return unique[:8]  # Limit to 8 variants
    
    async def _generate_hyde(self, query: str, analysis: Dict) -> Optional[str]:
        """
        Generate Hypothetical Document Embedding (HyDE).
        
        Creates a hypothetical "perfect answer" to embed for better retrieval.
        """
        try:
            entities = ", ".join(analysis.get('entities', ['the topic']))
            prompt = self.HYDE_PROMPT.format(
                query=query,
                intent=analysis.get('intent', 'conceptual'),
                entities=entities
            )
            
            response = await self.llm.generate_response(prompt)
            return response.strip()
        except Exception as e:
            logger.warning(f"HyDE generation failed: {e}")
            return None


# Factory and singleton
def get_query_processor(llm_service: Optional[GeminiService] = None) -> QueryProcessor:
    """Create a query processor instance."""
    return QueryProcessor(llm_service)
