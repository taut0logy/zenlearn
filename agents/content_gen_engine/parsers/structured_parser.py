"""
Structured Content Parser.

Parses LLM-generated XML-tagged content into Python objects.
"""

import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import html
import uuid

from utils.logger import logger


@dataclass
class ParsedImage:
    """Parsed image specification."""
    id: str
    prompt: str
    alt: str
    position: str = "center"
    width: str = "80%"
    style: str = "educational, clean, minimalist"


@dataclass
class ParsedMermaid:
    """Parsed Mermaid diagram."""
    id: str
    diagram_type: str
    code: str
    caption: Optional[str] = None


@dataclass
class ParsedCodeBlock:
    """Parsed code block."""
    language: str
    code: str
    title: Optional[str] = None


@dataclass
class ParsedCallout:
    """Parsed callout box."""
    callout_type: str
    content: str
    title: Optional[str] = None


@dataclass
class ParsedTable:
    """Parsed table."""
    headers: List[str]
    rows: List[List[str]]
    caption: Optional[str] = None


@dataclass
class ParsedContent:
    """All parsed content elements."""
    headings: List[Dict[str, Any]] = field(default_factory=list)
    paragraphs: List[str] = field(default_factory=list)
    images: List[ParsedImage] = field(default_factory=list)
    diagrams: List[ParsedMermaid] = field(default_factory=list)
    code_blocks: List[ParsedCodeBlock] = field(default_factory=list)
    callouts: List[ParsedCallout] = field(default_factory=list)
    lists: List[Dict[str, Any]] = field(default_factory=list)
    tables: List[ParsedTable] = field(default_factory=list)
    citations: List[Dict[str, str]] = field(default_factory=list)
    # Ordered sequence for rendering
    element_order: List[tuple] = field(default_factory=list)


@dataclass
class ParsedPage:
    """Parsed page/slide."""
    number: int
    page_type: str
    title: Optional[str] = None
    subtitle: Optional[str] = None
    content: ParsedContent = field(default_factory=ParsedContent)
    speaker_notes: Optional[str] = None


@dataclass
class ParsedDocument:
    """Complete parsed document."""
    document_type: str
    title: str
    subtitle: Optional[str] = None
    author: Optional[str] = None
    course: Optional[str] = None
    pages: List[ParsedPage] = field(default_factory=list)
    theme: Optional[Dict] = None


class StructuredContentParser:
    """
    Parses LLM-generated structured content into renderable objects.
    
    Handles XML tags: <document>, <page>, <heading>, <paragraph>,
    <img>, <mermaid>, <code>, <callout>, <list>, <table>, <citation>
    """
    
    def __init__(self):
        self.image_counter = 0
        self.diagram_counter = 0
    
    def parse(self, content: str) -> ParsedDocument:
        """
        Parse structured XML content.
        
        Args:
            content: XML-formatted content from LLM
            
        Returns:
            ParsedDocument with all elements extracted
        """
        # Reset counters
        self.image_counter = 0
        self.diagram_counter = 0
        
        # Clean and prepare
        content = self._preprocess(content)
        
        # Parse XML
        try:
            root = ET.fromstring(content)
        except ET.ParseError as e:
            logger.warning(f"XML parse error, attempting fix: {e}")
            content = self._fix_xml(content)
            try:
                root = ET.fromstring(content)
            except ET.ParseError:
                # Fallback: create minimal document
                return self._create_fallback_document(content)
        
        # Extract document metadata
        doc = ParsedDocument(
            document_type=root.get('type', 'markdown'),
            title=root.get('title', 'Untitled')
        )
        
        # Parse pages
        for page_elem in root.findall('.//page'):
            doc.pages.append(self._parse_page(page_elem))
        
        # Extract theme
        theme_elem = root.find('.//theme')
        if theme_elem is not None:
            doc.theme = self._parse_theme(theme_elem)
        
        return doc
    
    def _preprocess(self, content: str) -> str:
        """Preprocess content for XML parsing."""
        content = content.strip()
        
        # Extract document block if wrapped in other content
        if not content.startswith('<document'):
            match = re.search(r'<document.*?</document>', content, re.DOTALL)
            if match:
                content = match.group(0)
            else:
                # Wrap content in document tags
                content = f'<document type="markdown" title="Generated">{content}</document>'
        
        # Escape code blocks
        content = self._escape_code_blocks(content)
        
        # Escape mermaid blocks  
        content = self._escape_mermaid_blocks(content)
        
        return content
    
    def _escape_code_blocks(self, content: str) -> str:
        """Escape special chars in code blocks."""
        pattern = r'(<code[^>]*>)(.*?)(</code>)'
        
        def escape_match(m):
            start, code, end = m.groups()
            escaped = html.escape(code)
            return f"{start}{escaped}{end}"
        
        return re.sub(pattern, escape_match, content, flags=re.DOTALL)
    
    def _escape_mermaid_blocks(self, content: str) -> str:
        """Wrap mermaid in CDATA."""
        pattern = r'(<mermaid[^>]*>)(.*?)(</mermaid>)'
        
        def wrap_cdata(m):
            start, code, end = m.groups()
            if '<![CDATA[' not in code:
                return f"{start}<![CDATA[{code}]]>{end}"
            return m.group(0)
        
        return re.sub(pattern, wrap_cdata, content, flags=re.DOTALL)
    
    def _fix_xml(self, content: str) -> str:
        """Fix common XML issues."""
        # Fix unclosed self-closing tags
        content = re.sub(r'<(img|br|hr)([^/>]*?)(?<!/)>', r'<\1\2/>', content)
        
        # Fix unescaped &
        content = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;)', '&amp;', content)
        
        return content
    
    def _parse_page(self, elem: ET.Element) -> ParsedPage:
        """Parse a single page element."""
        page = ParsedPage(
            number=int(elem.get('number', 1)),
            page_type=elem.get('type', 'content')
        )
        
        # Title and subtitle
        title_elem = elem.find('title')
        if title_elem is not None and title_elem.text:
            page.title = title_elem.text.strip()
        
        subtitle_elem = elem.find('subtitle')
        if subtitle_elem is not None and subtitle_elem.text:
            page.subtitle = subtitle_elem.text.strip()
        
        # Speaker notes
        notes_elem = elem.find('speaker_notes')
        if notes_elem is not None and notes_elem.text:
            page.speaker_notes = notes_elem.text.strip()
        
        # Parse content elements
        page.content = self._parse_content(elem)
        
        return page
    
    def _parse_content(self, parent: ET.Element) -> ParsedContent:
        """Parse all content elements in order."""
        content = ParsedContent()
        
        for child in parent:
            tag = child.tag.lower()
            
            if tag == 'heading':
                heading = {
                    'level': int(child.get('level', 1)),
                    'text': child.text or ''
                }
                content.headings.append(heading)
                content.element_order.append(('heading', len(content.headings) - 1))
            
            elif tag == 'paragraph':
                text = self._get_text(child)
                content.paragraphs.append(text)
                content.element_order.append(('paragraph', len(content.paragraphs) - 1))
            
            elif tag == 'img':
                self.image_counter += 1
                img = ParsedImage(
                    id=f"img_{self.image_counter}",
                    prompt=child.get('prompt', ''),
                    alt=child.get('alt', ''),
                    position=child.get('position', 'center'),
                    width=child.get('width', '80%'),
                    style=child.get('style', 'educational')
                )
                content.images.append(img)
                content.element_order.append(('image', len(content.images) - 1))
            
            elif tag == 'mermaid':
                self.diagram_counter += 1
                code = self._get_text(child).strip()
                # Remove CDATA wrapper
                code = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', code, flags=re.DOTALL)
                
                diagram = ParsedMermaid(
                    id=f"diagram_{self.diagram_counter}",
                    diagram_type=child.get('type', 'flowchart'),
                    code=code,
                    caption=child.get('caption')
                )
                content.diagrams.append(diagram)
                content.element_order.append(('diagram', len(content.diagrams) - 1))
            
            elif tag == 'code':
                code_text = html.unescape(self._get_text(child))
                code_block = ParsedCodeBlock(
                    language=child.get('language', 'python'),
                    code=code_text,
                    title=child.get('title')
                )
                content.code_blocks.append(code_block)
                content.element_order.append(('code', len(content.code_blocks) - 1))
            
            elif tag == 'callout':
                callout = ParsedCallout(
                    callout_type=child.get('type', 'info'),
                    content=self._get_text(child),
                    title=child.get('title')
                )
                content.callouts.append(callout)
                content.element_order.append(('callout', len(content.callouts) - 1))
            
            elif tag == 'list':
                items = [item.text or '' for item in child.findall('item')]
                list_data = {
                    'type': child.get('type', 'bullet'),
                    'items': items
                }
                content.lists.append(list_data)
                content.element_order.append(('list', len(content.lists) - 1))
            
            elif tag == 'table':
                table = self._parse_table(child)
                if table:
                    content.tables.append(table)
                    content.element_order.append(('table', len(content.tables) - 1))
            
            elif tag == 'citation':
                citation = {
                    'source': child.get('source', ''),
                    'page': child.get('page'),
                    'section': child.get('section')
                }
                content.citations.append(citation)
                content.element_order.append(('citation', len(content.citations) - 1))
        
        return content
    
    def _get_text(self, elem: ET.Element) -> str:
        """Get all text content from element."""
        text = elem.text or ''
        
        # Handle CDATA
        if text.startswith('<![CDATA['):
            text = text[9:-3]
        
        for child in elem:
            if child.tail:
                text += child.tail
        
        return text
    
    def _parse_table(self, elem: ET.Element) -> Optional[ParsedTable]:
        """Parse table element."""
        headers = []
        rows = []
        
        headers_elem = elem.find('headers')
        if headers_elem is not None:
            headers = [h.text or '' for h in headers_elem.findall('header')]
        
        for row_elem in elem.findall('row'):
            row = [cell.text or '' for cell in row_elem.findall('cell')]
            rows.append(row)
        
        if headers or rows:
            return ParsedTable(
                headers=headers,
                rows=rows,
                caption=elem.get('caption')
            )
        return None
    
    def _parse_theme(self, elem: ET.Element) -> Dict:
        """Parse theme configuration."""
        theme = {}
        for child in elem:
            if child.text:
                theme[child.tag] = child.text
        return theme
    
    def _create_fallback_document(self, content: str) -> ParsedDocument:
        """Create fallback when XML parsing fails."""
        doc = ParsedDocument(
            document_type='markdown',
            title='Generated Content'
        )
        
        # Create single page with raw content
        page = ParsedPage(number=1, page_type='content')
        page.content.paragraphs.append(content)
        page.content.element_order.append(('paragraph', 0))
        
        doc.pages.append(page)
        return doc


# Factory function
def get_content_parser() -> StructuredContentParser:
    """Get content parser instance."""
    return StructuredContentParser()
