"""
Diagram Generator.

Renders Mermaid diagrams to images using mermaid-cli.
"""

import subprocess
import os
import sys
import tempfile
import shutil
from typing import Optional, Dict, List
from pathlib import Path
from dataclasses import dataclass, field
import json
import re

from content_gen_engine.parsers.structured_parser import ParsedMermaid
from utils.logger import logger


@dataclass
class MermaidConfig:
    """Configuration for Mermaid rendering."""
    theme: str = "default"  # default, forest, dark, neutral
    background_color: str = "white"
    width: int = 1200
    height: int = 800
    output_format: str = "png"  # png, svg
    
    theme_variables: Dict = field(default_factory=lambda: {
        "primaryColor": "#3182ce",
        "primaryTextColor": "#ffffff",
        "primaryBorderColor": "#2c5282",
        "lineColor": "#4a5568",
        "secondaryColor": "#edf2f7",
        "tertiaryColor": "#e2e8f0"
    })


class DiagramGenerator:
    """
    Generates diagrams from Mermaid code.
    
    Uses mermaid-cli (mmdc) for rendering.
    Falls back to returning code if CLI unavailable.
    """
    
    def __init__(
        self,
        config: Optional[MermaidConfig] = None,
        output_dir: str = "./assets/diagrams",
        use_validation: bool = True
    ):
        self.config = config or MermaidConfig()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.use_validation = use_validation
        
        self._mmdc_command = self._find_mmdc_command()
        self._cli_available = self._check_cli()
        
        # Initialize Gemini service for validation (lazy import to avoid circular dependency)
        self._gemini_service = None
    
    def _check_cli(self) -> bool:
        """Check if mermaid-cli is installed."""
        if not self._mmdc_command:
            logger.warning("mermaid-cli not found. Install with: npm install -g @mermaid-js/mermaid-cli")
            return False
        
        try:
            # Test if command works
            result = subprocess.run(
                [self._mmdc_command, '--version'],
                capture_output=True,
                text=True,
                timeout=5,
                shell=sys.platform == 'win32'  # Use shell on Windows
            )
            if result.returncode == 0:
                logger.info(f"Found mermaid-cli: {self._mmdc_command} (version: {result.stdout.strip()})")
                return True
            return False
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.warning(f"mermaid-cli check failed: {e}")
            return False
    
    def _find_mmdc_command(self) -> Optional[str]:
        """Find mmdc command path, handling Windows .cmd files."""
        # Try using shutil.which to locate the command
        if sys.platform == 'win32':
            # On Windows, try mmdc.cmd first, then mmdc
            for cmd in ['mmdc.cmd', 'mmdc']:
                path = shutil.which(cmd)
                if path:
                    return cmd  # Return the command name that works
            return None
        else:
            # On Unix-like systems
            return shutil.which('mmdc')
    
    async def render(self, diagram: ParsedMermaid) -> Optional[str]:
        """
        Render Mermaid diagram to image.
        
        Args:
            diagram: Parsed Mermaid specification
            
        Returns:
            Path to rendered image, or None if failed
        """
        if not self._cli_available:
            logger.warning("Mermaid CLI not available, skipping render")
            return None
        
        # Validate and fix code
        code = self._fix_code(diagram.code, diagram.diagram_type)
        
        # Try rendering with validation and retry
        max_retries = 2
        for attempt in range(max_retries):
            success, result_code, error = await self._try_render(code, diagram.id)
            
            if success:
                return result_code  # This is the output path
            
            # If failed and we have retries left, try to fix with Gemini
            if attempt < max_retries - 1 and self.use_validation:
                logger.warning(f"Render attempt {attempt + 1} failed, trying to fix with Gemini")
                fixed_code = await self._fix_mermaid_with_gemini(code, diagram.diagram_type, error)
                if fixed_code:
                    code = fixed_code
                else:
                    logger.error("Could not fix mermaid code")
                    return None
            else:
                logger.error(f"Mermaid render failed after {max_retries} attempts")
                return None
        
        return None
    
    async def _try_render(self, code: str, diagram_id: str) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Try to render mermaid code.
        
        Returns:
            (success, output_path or None, error or None)
        """
        config_path = self._create_config()
        output_path = self.output_dir / f"{diagram_id}.{self.config.output_format}"
        
        # Write diagram to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False, encoding='utf-8') as f:
            f.write(code)
            input_path = f.name
        
        try:
            cmd = [
                self._mmdc_command,
                '-i', input_path,
                '-o', str(output_path),
                '-c', config_path,
                '-b', self.config.background_color,
                '-w', str(self.config.width),
                '-H', str(self.config.height),
                '-t', self.config.theme
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                shell=sys.platform == 'win32'  # Use shell on Windows for npm commands
            )
            
            if result.returncode == 0:
                logger.info(f"Rendered diagram: {output_path}")
                return True, str(output_path), None
            else:
                error_msg = result.stderr or result.stdout
                logger.warning(f"Mermaid render failed: {error_msg}")
                return False, None, error_msg
            
        except subprocess.TimeoutExpired:
            logger.error("Mermaid render timed out")
            return False, None, "Render timed out"
        finally:
            os.unlink(input_path)
            if os.path.exists(config_path):
                os.unlink(config_path)
    
    async def _fix_mermaid_with_gemini(
        self, 
        mermaid_code: str, 
        diagram_type: str, 
        error: str
    ) -> Optional[str]:
        """
        Use Gemini to fix invalid mermaid code.
        
        Args:
            mermaid_code: The mermaid code that failed
            diagram_type: Type of diagram
            error: Error message from mermaid CLI
            
        Returns:
            Fixed mermaid code or None
        """
        if self._gemini_service is None:
            from services.gemini_service import get_gemini_service
            self._gemini_service = get_gemini_service()
        
        prompt = f"""Fix the following Mermaid diagram code that has errors.

Diagram Type: {diagram_type}
Error: {error}

Current Mermaid Code:
```
{mermaid_code}
```

Please analyze the error and provide ONLY the corrected Mermaid code in valid JSON format:
{{
    "fixed_code": "corrected mermaid code here",
    "changes_made": "brief description of what was fixed"
}}

Important:
- Return ONLY valid JSON
- Ensure the mermaid syntax is correct
- Preserve the diagram's intent
- Fix syntax errors, invalid node IDs, and structure issues"""

        try:
            response = await self._gemini_service.generate_structured(
                prompt=prompt,
                response_schema={
                    "type": "object",
                    "properties": {
                        "fixed_code": {"type": "string"},
                        "changes_made": {"type": "string"}
                    },
                    "required": ["fixed_code", "changes_made"]
                }
            )
            
            if response and "fixed_code" in response:
                logger.info(f"Mermaid fixed by Gemini: {response.get('changes_made', 'N/A')}")
                return response["fixed_code"]
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to fix mermaid with Gemini: {e}")
            return None
    
    async def render_batch(
        self,
        diagrams: List[ParsedMermaid]
    ) -> Dict[str, Optional[str]]:
        """
        Render multiple diagrams.
        
        Returns:
            Dict mapping diagram IDs to file paths
        """
        results = {}
        for diagram in diagrams:
            results[diagram.id] = await self.render(diagram)
        return results
    
    def _fix_code(self, code: str, diagram_type: str) -> str:
        """Fix common Mermaid syntax issues."""
        # Remove CDATA wrapper
        code = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', code, flags=re.DOTALL)
        code = code.strip()
        
        # Type declarations map
        type_declarations = {
            'flowchart': ['flowchart TD', 'flowchart LR', 'flowchart TB', 'flowchart RL', 'graph TD', 'graph LR'],
            'sequence': ['sequenceDiagram'],
            'class': ['classDiagram'],
            'state': ['stateDiagram-v2', 'stateDiagram'],
            'er': ['erDiagram'],
            'gantt': ['gantt'],
            'pie': ['pie']
        }
        
        expected = type_declarations.get(diagram_type, ['flowchart TD'])[0]
        all_possible_declarations = [decl for decls in type_declarations.values() for decl in decls]
        
        # Check if code already has a type declaration
        lines = code.split('\n')
        has_declaration = False
        first_line_is_declaration = False
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if any(line_stripped.startswith(decl) for decl in all_possible_declarations):
                if i == 0:
                    first_line_is_declaration = True
                    has_declaration = True
                    break
                else:
                    # Remove duplicate declarations that aren't on first line
                    lines[i] = ''
        
        # Ensure single type declaration at start
        if not first_line_is_declaration:
            if has_declaration:
                # Clean up the lines (removed duplicates above)
                code = '\n'.join(line for line in lines if line.strip())
            code = f"{expected}\n{code}"
        else:
            code = '\n'.join(lines)
        
        # Remove extra blank lines
        code = re.sub(r'\n{3,}', '\n\n', code)
        
        return code.strip()
    
    def _create_config(self) -> str:
        """Create Mermaid config file."""
        config = {
            "theme": self.config.theme,
            "themeVariables": self.config.theme_variables,
            "flowchart": {"curve": "basis", "padding": 20},
            "sequence": {
                "diagramMarginX": 50,
                "diagramMarginY": 10,
                "actorMargin": 50
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            return f.name
    
    def get_diagram_code(self, diagrams: List[ParsedMermaid]) -> Dict[str, str]:
        """
        Get diagram code without rendering.
        
        Useful when CLI is not available.
        """
        return {d.id: self._fix_code(d.code, d.diagram_type) for d in diagrams}


# Factory
def get_diagram_generator(
    output_dir: str = "./assets/diagrams",
    use_validation: bool = True
) -> DiagramGenerator:
    """Get diagram generator instance."""
    return DiagramGenerator(output_dir=output_dir, use_validation=use_validation)
