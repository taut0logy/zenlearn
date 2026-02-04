"""
Code Validators.

Validates generated code for syntax, execution, and correctness.
"""

import ast
import subprocess
import tempfile
import os
from typing import List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from content_gen_engine.schemas.content_tags import TestCase, CodeSpec
from utils.logger import logger


@dataclass
class ValidationResult:
    """Result of code validation."""

    is_valid: bool
    error_type: Optional[str] = None  # syntax, runtime, test_failure
    error_message: Optional[str] = None
    passed_tests: int = 0
    failed_tests: int = 0
    test_results: List[dict] = None


class SyntaxChecker:
    """
    Checks code syntax without execution.

    Supports:
    - Python (AST parsing)
    - JavaScript (via node --check)
    - Java (via javac)
    """

    def check(self, code: str, language: str) -> ValidationResult:
        """
        Check code syntax.

        Args:
            code: Source code
            language: Programming language

        Returns:
            ValidationResult
        """
        lang = language.lower()

        if lang == "python":
            return self._check_python(code)
        elif lang in ("javascript", "js"):
            return self._check_javascript(code)
        elif lang == "java":
            return self._check_java(code)
        else:
            # Best effort: check if parseable as text
            return ValidationResult(is_valid=True)

    def _check_python(self, code: str) -> ValidationResult:
        """Check Python syntax using AST."""
        try:
            ast.parse(code)
            return ValidationResult(is_valid=True)
        except SyntaxError as e:
            return ValidationResult(
                is_valid=False,
                error_type="syntax",
                error_message=f"Line {e.lineno}: {e.msg}",
            )

    def _check_javascript(self, code: str) -> ValidationResult:
        """Check JavaScript syntax using node."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = subprocess.run(
                ["node", "--check", temp_path],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                return ValidationResult(is_valid=True)
            else:
                return ValidationResult(
                    is_valid=False, error_type="syntax", error_message=result.stderr
                )
        except FileNotFoundError:
            logger.warning("Node.js not found for JavaScript syntax check")
            return ValidationResult(is_valid=True)  # Assume valid if can't check
        except subprocess.TimeoutExpired:
            return ValidationResult(
                is_valid=False,
                error_type="timeout",
                error_message="Syntax check timed out",
            )
        finally:
            os.unlink(temp_path)

    def _check_java(self, code: str) -> ValidationResult:
        """Check Java syntax using javac."""
        # Extract class name
        import re

        match = re.search(r"public\s+class\s+(\w+)", code)
        classname = match.group(1) if match else "Main"

        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, f"{classname}.java")

        with open(temp_path, "w") as f:
            f.write(code)

        try:
            result = subprocess.run(
                ["javac", temp_path], capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                return ValidationResult(is_valid=True)
            else:
                return ValidationResult(
                    is_valid=False, error_type="syntax", error_message=result.stderr
                )
        except FileNotFoundError:
            logger.warning("javac not found for Java syntax check")
            return ValidationResult(is_valid=True)
        finally:
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)


class CodeExecutor:
    """
    Executes code with test cases.

    Runs code in isolated subprocess with timeout.
    """

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def run_tests(
        self, code: str, test_cases: List[TestCase], language: str = "python"
    ) -> ValidationResult:
        """
        Run test cases against code.

        For Python, wraps code and injects test input.
        For other languages, uses appropriate runner.
        """
        lang = language.lower()

        if lang == "python":
            return self._run_python_tests(code, test_cases)
        elif lang in ("javascript", "js"):
            return self._run_js_tests(code, test_cases)
        else:
            logger.warning(f"Test execution not supported for {language}")
            return ValidationResult(is_valid=True, passed_tests=0, failed_tests=0)

    def _run_python_tests(
        self, code: str, test_cases: List[TestCase]
    ) -> ValidationResult:
        """Run Python tests.

        Supports two modes:
        1. Embedded tests: When test inputs are empty, runs code once and compares
           stdout lines against expected outputs (for self-contained code)
        2. Stdin tests: Injects input via stdin for each test case
        """
        # Check if this is embedded test mode (all inputs empty)
        is_embedded_mode = all(not tc.input.strip() for tc in test_cases)

        if is_embedded_mode:
            return self._run_embedded_python_tests(code, test_cases)
        else:
            return self._run_stdin_python_tests(code, test_cases)

    def _run_embedded_python_tests(
        self, code: str, test_cases: List[TestCase]
    ) -> ValidationResult:
        """Run Python code with embedded test cases.

        Executes the code once and compares stdout lines against expected outputs.
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            temp_path = f.name

        results = []
        passed = 0
        failed = 0

        try:
            result = subprocess.run(
                ["python", temp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            # Split stdout by lines
            output_lines = (
                result.stdout.strip().split("\n") if result.stdout.strip() else []
            )

            # Compare each line against expected outputs
            for i, tc in enumerate(test_cases):
                expected = tc.expected_output.strip()
                actual = output_lines[i].strip() if i < len(output_lines) else ""

                test_passed = actual == expected

                results.append(
                    {
                        "input": tc.input or f"(embedded test #{i + 1})",
                        "expected": expected,
                        "actual": actual,
                        "passed": test_passed,
                        "description": tc.description,
                    }
                )

                if test_passed:
                    passed += 1
                else:
                    failed += 1

            # Check for runtime errors
            if result.returncode != 0 and result.stderr:
                # If code crashed, mark remaining tests as failed
                if not results:
                    return ValidationResult(
                        is_valid=False,
                        error_type="runtime",
                        error_message=result.stderr.strip(),
                        passed_tests=0,
                        failed_tests=len(test_cases),
                        test_results=[],
                    )

        except subprocess.TimeoutExpired:
            return ValidationResult(
                is_valid=False,
                error_type="timeout",
                error_message="Code execution timed out",
                passed_tests=0,
                failed_tests=len(test_cases),
                test_results=[],
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_type="runtime",
                error_message=str(e),
                passed_tests=0,
                failed_tests=len(test_cases),
                test_results=[],
            )
        finally:
            os.unlink(temp_path)

        return ValidationResult(
            is_valid=failed == 0,
            error_type="test_failure" if failed > 0 else None,
            passed_tests=passed,
            failed_tests=failed,
            test_results=results,
        )

    def _run_stdin_python_tests(
        self, code: str, test_cases: List[TestCase]
    ) -> ValidationResult:
        """Run Python tests with stdin injection (legacy mode)."""
        results = []
        passed = 0
        failed = 0

        for tc in test_cases:
            # Create test wrapper
            test_code = f'''
import sys
from io import StringIO

# Redirect stdin
sys.stdin = StringIO("""{tc.input}""")

# Capture stdout
old_stdout = sys.stdout
sys.stdout = StringIO()

try:
    # User code
{self._indent_code(code)}
    
    # Get output
    output = sys.stdout.getvalue().strip()
    print(output, file=old_stdout)
except Exception as e:
    print(f"ERROR: {{e}}", file=old_stdout)
'''

            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(test_code)
                temp_path = f.name

            try:
                result = subprocess.run(
                    ["python", temp_path],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )

                output = result.stdout.strip()
                expected = tc.expected_output.strip()

                test_passed = output == expected

                results.append(
                    {
                        "input": tc.input,
                        "expected": expected,
                        "actual": output,
                        "passed": test_passed,
                        "description": tc.description,
                    }
                )

                if test_passed:
                    passed += 1
                else:
                    failed += 1

            except subprocess.TimeoutExpired:
                results.append(
                    {
                        "input": tc.input,
                        "expected": tc.expected_output,
                        "actual": "TIMEOUT",
                        "passed": False,
                        "description": tc.description,
                    }
                )
                failed += 1
            except Exception as e:
                results.append(
                    {
                        "input": tc.input,
                        "expected": tc.expected_output,
                        "actual": f"ERROR: {e}",
                        "passed": False,
                    }
                )
                failed += 1
            finally:
                os.unlink(temp_path)

        return ValidationResult(
            is_valid=failed == 0,
            error_type="test_failure" if failed > 0 else None,
            passed_tests=passed,
            failed_tests=failed,
            test_results=results,
        )

    def _run_js_tests(self, code: str, test_cases: List[TestCase]) -> ValidationResult:
        """Run JavaScript tests."""
        results = []
        passed = 0
        failed = 0

        for tc in test_cases:
            test_code = f"""
const readline = require('readline');
const {{ Readable }} = require('stream');

const input = `{tc.input}`;
const inputStream = Readable.from(input.split('\\n'));

let lines = input.split('\\n');
let lineIndex = 0;
const getLine = () => lines[lineIndex++] || '';

// Mock readline
global.readline = getLine;

{code}
"""

            with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
                f.write(test_code)
                temp_path = f.name

            try:
                result = subprocess.run(
                    ["node", temp_path],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )

                output = result.stdout.strip()
                expected = tc.expected_output.strip()
                test_passed = output == expected

                results.append(
                    {
                        "input": tc.input,
                        "expected": expected,
                        "actual": output,
                        "passed": test_passed,
                    }
                )

                if test_passed:
                    passed += 1
                else:
                    failed += 1

            except Exception as e:
                results.append(
                    {
                        "input": tc.input,
                        "expected": tc.expected_output,
                        "actual": f"ERROR: {e}",
                        "passed": False,
                    }
                )
                failed += 1
            finally:
                os.unlink(temp_path)

        return ValidationResult(
            is_valid=failed == 0,
            passed_tests=passed,
            failed_tests=failed,
            test_results=results,
        )

    def _indent_code(self, code: str, spaces: int = 4) -> str:
        """Indent code block."""
        indent = " " * spaces
        return "\n".join(indent + line for line in code.split("\n"))


class ContentValidator:
    """
    Validates generated content against sources.

    Uses few-shot prompting for grounding checks.
    """

    def __init__(self, llm=None):
        from services.gemini_service import get_gemini_service

        self.llm = llm or get_gemini_service("flash")  # Use flash for speed

    async def check_grounding(
        self, content: str, sources: List[str]
    ) -> Tuple[bool, List[dict]]:
        """
        Check if content is grounded in sources.

        Returns:
            (is_grounded, list of ungrounded claims)
        """
        prompt = f"""You are a fact-checker. Verify if the content below is supported by the sources.

<content>
{content[:3000]}
</content>

<sources>
{chr(10).join(sources[:5])}
</sources>

Return JSON:
{{
    "is_grounded": true/false,
    "ungrounded_claims": [
        {{"claim": "...", "reason": "..."}}
    ],
    "grounding_score": 0-100
}}
"""

        result = await self.llm.generate_json(prompt)

        is_grounded = result.get("is_grounded", True)
        claims = result.get("ungrounded_claims", [])

        return is_grounded, claims

    async def evaluate_quality(
        self, content: str, rubric: Optional[dict] = None
    ) -> dict:
        """
        Evaluate content quality using rubric.

        Returns:
            Quality scores and feedback
        """
        default_rubric = {
            "clarity": "Is the content clear and easy to understand?",
            "accuracy": "Is the information accurate and correct?",
            "completeness": "Does it cover the topic comprehensively?",
            "engagement": "Is it engaging for students?",
        }

        rubric = rubric or default_rubric

        prompt = f"""Evaluate this educational content quality.

<content>
{content[:3000]}
</content>

<rubric>
{chr(10).join(f"- {k}: {v}" for k, v in rubric.items())}
</rubric>

Return JSON:
{{
    "scores": {{
        "clarity": 0-10,
        "accuracy": 0-10,
        "completeness": 0-10,
        "engagement": 0-10
    }},
    "overall_score": 0-10,
    "strengths": ["..."],
    "improvements": ["..."]
}}
"""

        return await self.llm.generate_json(prompt)


# Factories
def get_syntax_checker() -> SyntaxChecker:
    return SyntaxChecker()


def get_code_executor(timeout: int = 10) -> CodeExecutor:
    return CodeExecutor(timeout)


def get_content_validator() -> ContentValidator:
    return ContentValidator()
