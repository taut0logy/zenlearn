"""
Static Code Analyzer using Tree-sitter.

Performs AST-based static analysis to extract structure from source code.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import os

# Try to import tree-sitter-languages, fall back gracefully
try:
    import tree_sitter_languages as tsl
    HAS_TREE_SITTER = True
except ImportError:
    HAS_TREE_SITTER = False


@dataclass
class FunctionInfo:
    """Extracted function/method information."""
    name: str
    qualified_name: str
    signature: str
    code: str
    docstring: Optional[str]
    start_line: int
    end_line: int
    parent_class: Optional[str]
    calls: List[str] = field(default_factory=list)


@dataclass
class ClassInfo:
    """Extracted class information."""
    name: str
    code: str
    start_line: int
    end_line: int
    methods: List[str] = field(default_factory=list)
    docstring: Optional[str] = None


@dataclass 
class StaticAnalysisResult:
    """Results from static code analysis."""
    language: str
    imports: List[str]
    classes: List[ClassInfo]
    functions: List[FunctionInfo]
    global_variables: List[str]


class StaticAnalyzer:
    """AST-based static code analyzer using tree-sitter."""
    
    LANGUAGE_MAP = {
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
    
    # AST node types for different languages
    IMPORT_TYPES = {
        'python': ['import_statement', 'import_from_statement'],
        'javascript': ['import_statement', 'import_declaration'],
        'typescript': ['import_statement', 'import_declaration'],
        'java': ['import_declaration'],
    }
    
    CLASS_TYPES = {
        'python': ['class_definition'],
        'javascript': ['class_declaration'],
        'typescript': ['class_declaration'],
        'java': ['class_declaration'],
    }
    
    FUNCTION_TYPES = {
        'python': ['function_definition'],
        'javascript': ['function_declaration', 'arrow_function', 'method_definition'],
        'typescript': ['function_declaration', 'arrow_function', 'method_definition'],
        'java': ['method_declaration'],
    }
    
    def detect_language(self, filename: str) -> str:
        """Detect language from file extension."""
        ext = os.path.splitext(filename)[1].lower()
        return self.LANGUAGE_MAP.get(ext, 'python')
    
    def analyze(self, code: str, filename: str) -> StaticAnalysisResult:
        """
        Perform static analysis on code.
        
        Args:
            code: Source code content
            filename: Filename for language detection
            
        Returns:
            StaticAnalysisResult with extracted components
        """
        language = self.detect_language(filename)
        
        if not HAS_TREE_SITTER:
            # Fallback: basic regex-based extraction for Python
            return self._fallback_analyze(code, language)
        
        try:
            parser = tsl.get_parser(language)
            tree = parser.parse(code.encode())
            
            imports = self._extract_imports(tree, code, language)
            classes = self._extract_classes(tree, code, language)
            functions = self._extract_functions(tree, code, language)
            globals_vars = self._extract_globals(tree, code, language)
            
            return StaticAnalysisResult(
                language=language,
                imports=imports,
                classes=classes,
                functions=functions,
                global_variables=globals_vars
            )
        except Exception:
            return self._fallback_analyze(code, language)
    
    def _extract_imports(self, tree, source: str, language: str) -> List[str]:
        """Extract import statements."""
        imports = []
        types = self.IMPORT_TYPES.get(language, [])
        
        def walk(node):
            if node.type in types:
                imports.append(source[node.start_byte:node.end_byte])
            for child in node.children:
                walk(child)
        
        walk(tree.root_node)
        return imports
    
    def _extract_classes(self, tree, source: str, language: str) -> List[ClassInfo]:
        """Extract class definitions."""
        classes = []
        types = self.CLASS_TYPES.get(language, [])
        
        def walk(node):
            if node.type in types:
                class_info = self._parse_class(node, source, language)
                if class_info:
                    classes.append(class_info)
            for child in node.children:
                walk(child)
        
        walk(tree.root_node)
        return classes
    
    def _extract_functions(self, tree, source: str, language: str) -> List[FunctionInfo]:
        """Extract function/method definitions."""
        functions = []
        types = self.FUNCTION_TYPES.get(language, [])
        
        def walk(node, parent_class=None):
            if node.type in types:
                func_info = self._parse_function(node, source, language, parent_class)
                if func_info:
                    functions.append(func_info)
            
            # Track class context
            if node.type in self.CLASS_TYPES.get(language, []):
                class_name = self._get_identifier(node, source)
                for child in node.children:
                    walk(child, class_name)
            else:
                for child in node.children:
                    walk(child, parent_class)
        
        walk(tree.root_node)
        return functions
    
    def _extract_globals(self, tree, source: str, language: str) -> List[str]:
        """Extract global variable assignments."""
        globals_vars = []
        
        if language == 'python':
            for child in tree.root_node.children:
                if child.type == 'expression_statement':
                    for sub in child.children:
                        if sub.type == 'assignment':
                            globals_vars.append(source[sub.start_byte:sub.end_byte])
        
        return globals_vars
    
    def _parse_class(self, node, source: str, language: str) -> Optional[ClassInfo]:
        """Parse a class node."""
        name = self._get_identifier(node, source)
        if not name:
            return None
        
        code = source[node.start_byte:node.end_byte]
        docstring = self._extract_docstring(node, source, language)
        
        # Find method names
        methods = []
        for child in node.children:
            if child.type == 'block':
                for block_child in child.children:
                    if block_child.type in self.FUNCTION_TYPES.get(language, []):
                        method_name = self._get_identifier(block_child, source)
                        if method_name:
                            methods.append(method_name)
        
        return ClassInfo(
            name=name,
            code=code,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            methods=methods,
            docstring=docstring
        )
    
    def _parse_function(
        self, 
        node, 
        source: str, 
        language: str,
        parent_class: Optional[str]
    ) -> Optional[FunctionInfo]:
        """Parse a function node."""
        name = self._get_identifier(node, source)
        if not name:
            return None
        
        code = source[node.start_byte:node.end_byte]
        lines = code.split('\n')
        signature = lines[0].strip()
        docstring = self._extract_docstring(node, source, language)
        calls = self._extract_calls(node, source)
        qualified_name = f"{parent_class}.{name}" if parent_class else name
        
        return FunctionInfo(
            name=name,
            qualified_name=qualified_name,
            signature=signature,
            code=code,
            docstring=docstring,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            parent_class=parent_class,
            calls=calls
        )
    
    def _get_identifier(self, node, source: str) -> Optional[str]:
        """Get identifier name from node."""
        for child in node.children:
            if child.type == 'identifier':
                return source[child.start_byte:child.end_byte]
        return None
    
    def _extract_docstring(self, node, source: str, language: str) -> Optional[str]:
        """Extract docstring from function/class."""
        if language != 'python':
            return None
        
        for child in node.children:
            if child.type == 'block':
                for block_child in child.children:
                    if block_child.type == 'expression_statement':
                        for expr in block_child.children:
                            if expr.type == 'string':
                                docstring = source[expr.start_byte:expr.end_byte]
                                return docstring.strip('"""').strip("'''").strip()
        return None
    
    def _extract_calls(self, node, source: str) -> List[str]:
        """Extract function calls from a function body."""
        calls = set()
        
        def walk(n):
            if n.type == 'call':
                for child in n.children:
                    if child.type in ['identifier', 'attribute']:
                        calls.add(source[child.start_byte:child.end_byte])
                        break
            for child in n.children:
                walk(child)
        
        walk(node)
        return list(calls)
    
    def _fallback_analyze(self, code: str, language: str) -> StaticAnalysisResult:
        """Fallback regex-based analysis when tree-sitter unavailable."""
        import re
        
        imports = []
        functions = []
        classes = []
        
        if language == 'python':
            # Extract imports
            for match in re.finditer(r'^(?:from\s+\S+\s+)?import\s+.+$', code, re.MULTILINE):
                imports.append(match.group())
            
            # Extract function definitions
            for match in re.finditer(r'^def\s+(\w+)\s*\([^)]*\):', code, re.MULTILINE):
                functions.append(FunctionInfo(
                    name=match.group(1),
                    qualified_name=match.group(1),
                    signature=match.group(),
                    code=match.group(),
                    docstring=None,
                    start_line=code[:match.start()].count('\n') + 1,
                    end_line=code[:match.start()].count('\n') + 1,
                    parent_class=None
                ))
            
            # Extract class definitions
            for match in re.finditer(r'^class\s+(\w+)', code, re.MULTILINE):
                classes.append(ClassInfo(
                    name=match.group(1),
                    code=match.group(),
                    start_line=code[:match.start()].count('\n') + 1,
                    end_line=code[:match.start()].count('\n') + 1
                ))
        
        return StaticAnalysisResult(
            language=language,
            imports=imports,
            classes=classes,
            functions=functions,
            global_variables=[]
        )


# Singleton instance
static_analyzer = StaticAnalyzer()
