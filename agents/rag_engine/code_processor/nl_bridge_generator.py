"""
Natural Language Bridge Generator.

Generates searchable NL content to bridge the gap between code and student queries.
"""

import json
from typing import Dict, List

from services.gemini_service import gemini_service
from utils.logger import logger
from .code_analyzer_agent import FunctionAnalysis


class NLBridgeGenerator:
    """Generates natural language content for code searchability."""
    
    NL_BRIDGE_PROMPT = """Generate natural language content to help students find this code when searching.

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

Respond with JSON ONLY (no markdown):
{{
    "nl_queries": [
        "15-20 natural language questions/searches students might use",
        "Include formal, casual, problem-based, concept-based phrasings"
    ],
    "keywords": [
        "Individual searchable terms including synonyms"
    ],
    "related_topics": [
        "Broader CS topics this code relates to"
    ]
}}"""

    async def generate_bridge(
        self,
        purpose_summary: str,
        algorithms: List[str],
        concepts: List[str],
        functions_summary: List[str]
    ) -> Dict[str, List[str]]:
        """
        Generate NL bridge content for code searchability.
        
        Returns:
            Dict with nl_queries, keywords, related_topics
        """
        prompt = self.NL_BRIDGE_PROMPT.format(
            purpose_summary=purpose_summary,
            algorithms=json.dumps(algorithms),
            concepts=json.dumps(concepts),
            functions_summary="\n".join(f"- {f}" for f in functions_summary)
        )
        
        try:
            response = await gemini_service.generate_response(prompt)
            data = self._parse_json(response)
            
            return {
                'nl_queries': data.get('nl_queries', []),
                'keywords': data.get('keywords', []),
                'related_topics': data.get('related_topics', [])
            }
        except Exception as e:
            logger.error(f"Error generating NL bridge: {e}")
            return {
                'nl_queries': [],
                'keywords': [],
                'related_topics': []
            }
    
    def merge_all_nl_queries(
        self,
        file_bridge: Dict[str, List[str]],
        function_analyses: Dict[str, FunctionAnalysis]
    ) -> List[str]:
        """
        Combine and deduplicate all NL queries from file and functions.
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
    
    def _parse_json(self, response: str) -> dict:
        """Parse JSON from LLM response."""
        text = response.strip()
        if text.startswith('```'):
            lines = text.split('\n')
            text = '\n'.join(lines[1:-1] if lines[-1] == '```' else lines[1:])
        return json.loads(text)


# Singleton instance
nl_bridge_generator = NLBridgeGenerator()
