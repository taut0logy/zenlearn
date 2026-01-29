"""
LaTeX generator for converting extracted text to formatted LaTeX.

Enhanced version with support for:
- Colorful boxes (definition, theorem, example, note, warning, proof)
- Code blocks with syntax highlighting hints
- Mermaid.js diagrams
- Tables with booktabs styling
"""

import json
from typing import List, Dict, Any, Optional
from utils.logger import logger


class LatexGenerator:
    """
    Converts extracted text blocks into properly formatted LaTeX.
    
    Generates custom environment markers that map to styled HTML on frontend:
    - \\begin{definitionbox} -> Blue styled box
    - \\begin{theorembox} -> Green styled box  
    - \\begin{examplebox} -> Orange styled box
    - \\begin{notebox} -> Gray styled box
    - \\begin{warningbox} -> Red styled box
    - \\begin{proofbox} -> Purple styled box
    - \\begin{mermaid} -> Mermaid.js diagram
    - \\begin{codebox} -> Syntax highlighted code
    """
    
    DOCUMENT_TEMPLATE = r"""\documentclass[12pt]{{article}}
\usepackage{{amsmath, amssymb, amsthm}}
\usepackage{{mathtools}}
\usepackage{{graphicx}}
\usepackage{{enumitem}}
\usepackage[utf8]{{inputenc}}
\usepackage{{booktabs}}
\usepackage{{tabularx}}
\usepackage[dvipsnames]{{xcolor}}
\usepackage{{tcolorbox}}
\tcbuselibrary{{theorems, skins, breakable}}

% Custom colored boxes
\newtcolorbox{{definitionbox}}[1][]{{
    colback=blue!5!white,
    colframe=blue!75!black,
    fonttitle=\bfseries,
    title=Definition,
    #1
}}

\newtcolorbox{{theorembox}}[1][]{{
    colback=green!5!white,
    colframe=green!50!black,
    fonttitle=\bfseries,
    title=Theorem,
    #1
}}

\newtcolorbox{{examplebox}}[1][]{{
    colback=orange!10!white,
    colframe=orange!75!black,
    fonttitle=\bfseries,
    title=Example,
    #1
}}

\newtcolorbox{{notebox}}[1][]{{
    colback=gray!10!white,
    colframe=gray!50!black,
    fonttitle=\bfseries,
    title=Note,
    #1
}}

\newtcolorbox{{warningbox}}[1][]{{
    colback=red!5!white,
    colframe=red!75!black,
    fonttitle=\bfseries,
    title=Warning,
    #1
}}

\newtcolorbox{{proofbox}}[1][]{{
    colback=purple!5!white,
    colframe=purple!50!black,
    fonttitle=\bfseries,
    title=Proof,
    #1
}}

\title{{{title}}}
\date{{\today}}

\begin{{document}}

\maketitle

{content}

\end{{document}}
"""

    def generate_latex(
        self, 
        title: str, 
        blocks: List[Dict[str, Any]],
        full_text: str = ""
    ) -> str:
        """
        Generate LaTeX document from extracted blocks.
        
        Args:
            title: Document title
            blocks: List of content blocks with type and content
            full_text: Fallback plain text if blocks are empty
            
        Returns:
            Complete LaTeX document as string
        """
        if not blocks and full_text:
            # Fallback: use full text as single paragraph
            content = self._escape_latex(full_text)
        else:
            content_parts = []
            for block in blocks:
                block_type = block.get("type", "paragraph")
                block_content = block.get("content", "")
                metadata = block.get("metadata", {})
                
                formatted = self._format_block(block_type, block_content, metadata)
                if formatted:
                    content_parts.append(formatted)
            
            content = "\n\n".join(content_parts)
        
        # Generate full document
        latex_doc = self.DOCUMENT_TEMPLATE.format(
            title=self._escape_latex(title),
            content=content
        )
        
        logger.info(f"Generated LaTeX document with {len(blocks)} blocks")
        return latex_doc
    
    def generate_latex_fragment(
        self,
        blocks: List[Dict[str, Any]],
        full_text: str = ""
    ) -> str:
        """
        Generate LaTeX fragment (without document wrapper) for inline rendering.
        This is used by the frontend for KaTeX/custom rendering.
        """
        if not blocks and full_text:
            return self._escape_latex(full_text)
        
        content_parts = []
        for block in blocks:
            block_type = block.get("type", "paragraph")
            block_content = block.get("content", "")
            metadata = block.get("metadata", {})
            
            formatted = self._format_block(block_type, block_content, metadata)
            if formatted:
                content_parts.append(formatted)
        
        return "\n\n".join(content_parts)
    
    def _format_block(self, block_type: str, content: str, metadata: Optional[Dict] = None) -> str:
        """Format a single block based on its type."""
        metadata = metadata or {}
        
        # Structure types
        if block_type == "section":
            return f"\\section{{{self._escape_latex(content)}}}"
        
        elif block_type == "subsection":
            return f"\\subsection{{{self._escape_latex(content)}}}"
        
        elif block_type == "heading":  # Legacy support
            return f"\\section{{{self._escape_latex(content)}}}"
        
        elif block_type == "subheading":  # Legacy support
            return f"\\subsection{{{self._escape_latex(content)}}}"
        
        # Math types
        elif block_type == "equation":
            clean_eq = content.strip()
            # If already wrapped, use as-is
            if clean_eq.startswith("$$") or clean_eq.startswith("\\["):
                return clean_eq
            # Remove single $ wrapping if present
            if clean_eq.startswith("$") and clean_eq.endswith("$") and not clean_eq.startswith("$$"):
                clean_eq = clean_eq[1:-1]
            return f"\\[\n{clean_eq}\n\\]"
        
        # List types
        elif block_type in ["list", "itemize"]:
            items = self._parse_list_items(content)
            if items:
                item_str = "\n".join(f"  \\item {self._escape_latex(item)}" for item in items)
                return f"\\begin{{itemize}}\n{item_str}\n\\end{{itemize}}"
            return self._escape_latex(content)
        
        elif block_type in ["numbered_list", "enumerate"]:
            items = self._parse_list_items(content)
            if items:
                item_str = "\n".join(f"  \\item {self._escape_latex(item)}" for item in items)
                return f"\\begin{{enumerate}}\n{item_str}\n\\end{{enumerate}}"
            return self._escape_latex(content)
        
        # Colored box types
        elif block_type == "definition":
            term = metadata.get("term", "")
            title_opt = f"[title=Definition: {self._escape_latex(term)}]" if term else ""
            return f"\\begin{{definitionbox}}{title_opt}\n{self._process_math_content(content)}\n\\end{{definitionbox}}"
        
        elif block_type == "theorem":
            name = metadata.get("name", "")
            title_opt = f"[title=Theorem: {self._escape_latex(name)}]" if name else ""
            return f"\\begin{{theorembox}}{title_opt}\n{self._process_math_content(content)}\n\\end{{theorembox}}"
        
        elif block_type == "example":
            title = metadata.get("title", "")
            title_opt = f"[title=Example: {self._escape_latex(title)}]" if title else ""
            return f"\\begin{{examplebox}}{title_opt}\n{self._process_math_content(content)}\n\\end{{examplebox}}"
        
        elif block_type == "note":
            return f"\\begin{{notebox}}\n{self._process_math_content(content)}\n\\end{{notebox}}"
        
        elif block_type == "warning":
            return f"\\begin{{warningbox}}\n{self._process_math_content(content)}\n\\end{{warningbox}}"
        
        elif block_type == "proof":
            return f"\\begin{{proofbox}}\n{self._process_math_content(content)}\n\\end{{proofbox}}"
        
        # Special content types
        elif block_type == "code":
            language = metadata.get("language", "text")
            # Use codebox custom environment for frontend parsing
            return f"\\begin{{codebox}}[{language}]\n{content}\n\\end{{codebox}}"
        
        elif block_type == "diagram":
            diagram_type = metadata.get("type", "flowchart")
            # Use mermaid environment for frontend parsing
            return f"\\begin{{mermaid}}[{diagram_type}]\n{content}\n\\end{{mermaid}}"
        
        elif block_type == "diagram_description":  # Legacy support
            return f"\\textit{{[Diagram: {self._escape_latex(content)}]}}"
        
        elif block_type == "table":
            return self._format_table(content, metadata)
        
        else:  # paragraph or unknown
            return self._process_math_content(content)
    
    def _format_table(self, content: str, metadata: Optional[Dict] = None) -> str:
        """
        Generate LaTeX table from structured content.
        
        Content can be:
        - JSON string: {"headers": [...], "rows": [[...], ...], "caption": "..."}
        - Plain text (fallback)
        """
        try:
            # Try to parse as JSON
            if content.strip().startswith("{"):
                table_data = json.loads(content)
            elif isinstance(content, dict):
                table_data = content
            else:
                # Plain text fallback
                return self._escape_latex(content)
            
            headers = table_data.get("headers", [])
            rows = table_data.get("rows", [])
            caption = table_data.get("caption", metadata.get("caption", "")) if metadata else table_data.get("caption", "")
            
            if not headers or not rows:
                return self._escape_latex(str(content))
            
            # Generate alignment (center all columns)
            alignment = "c" * len(headers)
            
            latex = "\\begin{table}[htbp]\n\\centering\n"
            latex += f"\\begin{{tabular}}{{{alignment}}}\n"
            latex += "\\toprule\n"
            latex += " & ".join([f"\\textbf{{{self._escape_latex(h)}}}" for h in headers]) + " \\\\\n"
            latex += "\\midrule\n"
            
            for row in rows:
                latex += " & ".join([self._escape_latex(str(cell)) for cell in row]) + " \\\\\n"
            
            latex += "\\bottomrule\n"
            latex += "\\end{tabular}\n"
            
            if caption:
                latex += f"\\caption{{{self._escape_latex(caption)}}}\n"
            
            latex += "\\end{table}"
            return latex
            
        except (json.JSONDecodeError, TypeError):
            return self._escape_latex(str(content))
    
    def _parse_list_items(self, content: str) -> List[str]:
        """Parse list content into individual items."""
        lines = content.strip().split("\n")
        items = []
        for line in lines:
            line = line.strip()
            # Remove common list prefixes
            for prefix in ["- ", "* ", "• ", "· ", "→ ", "> "]:
                if line.startswith(prefix):
                    line = line[len(prefix):]
                    break
            # Remove numbered prefixes like "1. ", "2) "
            if len(line) > 2 and line[0].isdigit():
                for sep in [". ", ") ", ": "]:
                    idx = line.find(sep)
                    if idx > 0 and idx < 4:
                        line = line[idx + len(sep):]
                        break
            if line:
                items.append(line)
        return items
    
    def _process_math_content(self, text: str) -> str:
        """
        Process content that may contain inline math.
        Preserves $ delimiters and escapes non-math content.
        """
        # If content has math delimiters, process carefully
        if "$" in text or "\\(" in text or "\\[" in text:
            return self._escape_latex_preserve_math(text)
        return self._escape_latex(text)
    
    def _escape_latex_preserve_math(self, text: str) -> str:
        """
        Escape LaTeX special chars but preserve math environments.
        This is a simplified approach - splits on $ and escapes alternating sections.
        """
        # Don't escape if it looks like heavy LaTeX
        if "\\begin" in text or "\\section" in text:
            return text
        
        # Split by display math first ($$...$$)
        parts = []
        remaining = text
        
        while "$$" in remaining:
            before, _, after = remaining.partition("$$")
            parts.append(("text", before))
            if "$$" in after:
                math, _, remaining = after.partition("$$")
                parts.append(("display_math", f"$${math}$$"))
            else:
                parts.append(("text", "$$" + after))
                remaining = ""
                break
        parts.append(("text", remaining))
        
        # Process each part
        result = []
        for part_type, content in parts:
            if part_type == "display_math":
                result.append(content)
            else:
                # Handle inline math ($...$)
                processed = self._escape_with_inline_math(content)
                result.append(processed)
        
        return "".join(result)
    
    def _escape_with_inline_math(self, text: str) -> str:
        """Escape text while preserving inline $...$ math."""
        if "$" not in text:
            return self._escape_latex(text)
        
        result = []
        i = 0
        while i < len(text):
            if text[i] == "$":
                # Find closing $
                end = text.find("$", i + 1)
                if end != -1:
                    result.append(text[i:end + 1])  # Keep math as-is
                    i = end + 1
                else:
                    result.append("\\$")
                    i += 1
            else:
                # Find next $ or end
                next_dollar = text.find("$", i)
                if next_dollar == -1:
                    result.append(self._escape_latex(text[i:]))
                    break
                else:
                    result.append(self._escape_latex(text[i:next_dollar]))
                    i = next_dollar
        
        return "".join(result)
    
    def _escape_latex(self, text: str) -> str:
        """Escape special LaTeX characters."""
        # Don't escape if it looks like it's already LaTeX
        if "\\\\" in text or "\\begin" in text or "\\section" in text:
            return text
        
        # Escape special characters
        replacements = [
            ("\\", r"\textbackslash{}"),
            ("&", r"\&"),
            ("%", r"\%"),
            ("$", r"\$"),
            ("#", r"\#"),
            ("_", r"\_"),
            ("{", r"\{"),
            ("}", r"\}"),
            ("~", r"\textasciitilde{}"),
            ("^", r"\textasciicircum{}"),
        ]
        
        result = text
        for old, new in replacements:
            result = result.replace(old, new)
        
        return result


# Singleton instance
_latex_generator = LatexGenerator()


def get_latex_generator() -> LatexGenerator:
    """Get the LaTeX generator instance."""
    return _latex_generator
