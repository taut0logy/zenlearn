"""
Markdown Generator.

Converts parsed content to Markdown format.
"""

from typing import Optional
from pathlib import Path

from content_gen_engine.parsers.structured_parser import (
    ParsedDocument, ParsedPage, ParsedContent,
    ParsedImage, ParsedMermaid, ParsedCodeBlock, ParsedCallout
)
from utils.logger import logger


class MarkdownGenerator:
    """
    Generates Markdown from parsed content.
    
    Features:
    - GitHub Flavored Markdown
    - Mermaid diagrams embedded
    - Image placeholders with prompts
    - Code blocks with syntax highlighting
    """
    
    def __init__(self, output_dir: str = "./output"):
        """Initialize generator."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(
        self,
        document: ParsedDocument,
        include_images: bool = True,
        image_paths: Optional[dict] = None
    ) -> str:
        """
        Generate Markdown from parsed document.
        
        Args:
            document: Parsed document
            include_images: Include image placeholders
            image_paths: Optional dict mapping image IDs to paths
            
        Returns:
            Markdown string
        """
        lines = []
        
        # Title
        lines.append(f"# {document.title}")
        if document.subtitle:
            lines.append(f"*{document.subtitle}*")
        lines.append("")
        
        # Metadata
        if document.author or document.course:
            if document.author:
                lines.append(f"**Author:** {document.author}")
            if document.course:
                lines.append(f"**Course:** {document.course}")
            lines.append("")
        
        # Table of contents
        lines.append("## Table of Contents")
        for page in document.pages:
            if page.title and page.page_type != "title":
                lines.append(f"- [{page.title}](#{self._slugify(page.title)})")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Pages
        for page in document.pages:
            page_md = self._render_page(page, include_images, image_paths)
            lines.append(page_md)
            lines.append("")
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)
    
    def save(
        self,
        document: ParsedDocument,
        filename: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate and save Markdown file.
        
        Returns:
            Path to saved file
        """
        content = self.generate(document, **kwargs)
        
        if not filename:
            filename = self._slugify(document.title) + ".md"
        
        output_path = self.output_dir / filename
        output_path.write_text(content, encoding='utf-8')
        
        logger.info(f"Saved markdown: {output_path}")
        return str(output_path)
    
    def _render_page(
        self,
        page: ParsedPage,
        include_images: bool,
        image_paths: Optional[dict]
    ) -> str:
        """Render a single page to Markdown."""
        lines = []
        
        # Page title
        if page.title:
            if page.page_type == "title":
                lines.append(f"# {page.title}")
                if page.subtitle:
                    lines.append(f"### {page.subtitle}")
            else:
                lines.append(f"## {page.title}")
        
        lines.append("")
        
        # Render content in order
        content = page.content
        for element_type, idx in content.element_order:
            if element_type == 'heading':
                h = content.headings[idx]
                prefix = "#" * (h['level'] + 1)  # +1 because page title is h2
                lines.append(f"{prefix} {h['text']}")
                lines.append("")
            
            elif element_type == 'paragraph':
                lines.append(content.paragraphs[idx])
                lines.append("")
            
            elif element_type == 'image' and include_images:
                img = content.images[idx]
                if image_paths and img.id in image_paths:
                    # Convert absolute path to relative path
                    img_path = self._make_relative_path(image_paths[img.id])
                    lines.append(f"![{img.alt}]({img_path})")
                else:
                    # Placeholder with prompt for later generation
                    lines.append(f"<!-- IMAGE: {img.prompt} -->")
                    lines.append(f"*[Image: {img.alt}]*")
                lines.append("")
            
            elif element_type == 'diagram':
                diagram = content.diagrams[idx]
                # Check if diagram was rendered to image
                if image_paths and diagram.id in image_paths:
                    # Use rendered diagram image
                    diagram_path = self._make_relative_path(image_paths[diagram.id])
                    caption = diagram.caption or "Diagram"
                    lines.append(f"![{caption}]({diagram_path})")
                    if diagram.caption:
                        lines.append(f"*{diagram.caption}*")
                else:
                    # Fallback to mermaid code block
                    lines.append("```mermaid")
                    lines.append(diagram.code)
                    lines.append("```")
                    if diagram.caption:
                        lines.append(f"*{diagram.caption}*")
                lines.append("")
            
            elif element_type == 'code':
                code = content.code_blocks[idx]
                if code.title:
                    lines.append(f"**{code.title}**")
                lines.append(f"```{code.language}")
                lines.append(code.code)
                lines.append("```")
                lines.append("")
            
            elif element_type == 'callout':
                callout = content.callouts[idx]
                icon = self._get_callout_icon(callout.callout_type)
                lines.append(f"> {icon} **{callout.callout_type.upper()}**")
                lines.append(f"> ")
                lines.append(f"> {callout.content}")
                lines.append("")
            
            elif element_type == 'list':
                lst = content.lists[idx]
                # Filter out empty list items
                items = [item.strip() for item in lst['items'] if item and item.strip()]
                if items:  # Only render if there are non-empty items
                    for i, item in enumerate(items):
                        if lst['type'] == 'numbered':
                            lines.append(f"{i+1}. {item}")
                        else:
                            lines.append(f"- {item}")
                    lines.append("")
            
            elif element_type == 'table':
                table = content.tables[idx]
                lines.append(self._render_table(table))
                lines.append("")
            
            elif element_type == 'citation':
                cit = content.citations[idx]
                source = cit['source']
                if cit.get('page'):
                    source += f", p.{cit['page']}"
                lines.append(f"*Source: {source}*")
                lines.append("")
        
        return "\n".join(lines)
    
    def _render_table(self, table) -> str:
        """Render table to Markdown."""
        lines = []
        
        if table.headers:
            lines.append("| " + " | ".join(table.headers) + " |")
            lines.append("| " + " | ".join(["---"] * len(table.headers)) + " |")
        
        for row in table.rows:
            lines.append("| " + " | ".join(row) + " |")
        
        if table.caption:
            lines.append(f"*{table.caption}*")
        
        return "\n".join(lines)
    
    def _get_callout_icon(self, callout_type: str) -> str:
        """Get emoji icon for callout type."""
        icons = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'tip': '💡',
            'example': '📝'
        }
        return icons.get(callout_type, 'ℹ️')
    
    def _make_relative_path(self, absolute_path: str) -> str:
        """Convert path to simple relative path (images/file.png or diagrams/file.png)."""
        abs_path = Path(absolute_path)
        
        # Extract parent folder name and filename
        # This ensures we always get paths like "images/img_1.png" or "diagrams/diagram_1.png"
        parent_name = abs_path.parent.name
        filename = abs_path.name
        
        # Use forward slashes for cross-platform markdown compatibility
        return f"{parent_name}/{filename}"
    
    def _slugify(self, text: str) -> str:
        """Convert text to URL-safe slug."""
        import re
        slug = text.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        return slug.strip('-')


# Factory
def get_markdown_generator(output_dir: str = "./output") -> MarkdownGenerator:
    """Get markdown generator instance."""
    return MarkdownGenerator(output_dir)
