"""
Validated Code Generation Tool.
"""

from typing import Optional, List
from langchain_core.tools import tool
from langchain_core.callbacks.manager import adispatch_custom_event

from services.gemini_service import get_gemini_service
from content_gen_engine.validators.code_validator import (
    get_syntax_checker,
    get_code_executor,
)
from content_gen_engine.schemas.content_tags import TestCase
from utils.logger import logger


CODE_WITH_TESTS_PROMPT = '''Generate Python code for the following topic, with embedded test cases.

<topic>
{topic}
</topic>

<context>
{context}
</context>

REQUIREMENTS:
1. Write a complete, working implementation with proper type hints and error handling
2. Add embedded test cases that call the function and print results to stdout
3. Each print() statement should output one test result on its own line

EXAMPLE FORMAT:
```python
def example_function(x: int) -> int:
    """Function description."""
    # Implementation
    return x * 2

# Test Cases - print results to stdout
print(example_function(5))   # Should print: 10
print(example_function(0))   # Should print: 0
print(example_function(-3))  # Should print: -6
```

Return JSON with this exact structure:
{{
    "code": "complete Python code with function AND embedded test print statements",
    "test_cases": [
        {{
            "expected_output": "exact value that first print will output",
            "description": "what this test verifies"
        }},
        {{
            "expected_output": "exact value that second print will output", 
            "description": "what this test verifies"
        }},
        {{
            "expected_output": "exact value that third print will output",
            "description": "what this test verifies"
        }}
    ]
}}

CRITICAL:
- The code must be RUNNABLE - when executed, it should print test outputs
- Each expected_output must EXACTLY match what gets printed (no extra text)
- Include 3 test cases: normal case, edge case, and error/boundary case
- For functions that raise exceptions, wrap the test call in try/except and print the error type
'''


@tool
async def generate_validated_code(
    topic: str,
    context: Optional[str] = None,
) -> str:
    """
    Generate Python code with automated validation (syntax check + test execution).

    Use this tool whenever the user asks to write, generate, or provide Python code,
    especially if they ask for "validated" or "tested" code.

    Args:
        topic: Description of the code to generate (e.g. "binary search function", "calculate fibonacci")
        context: Optional background context or specific requirements.

    Returns:
        Formatted markdown string containing the code and validation report.
    """
    try:
        logger.info(f"[ValidatedCodeGen] Generating code for: {topic}")

        # 1. Notify start
        await adispatch_custom_event(
            "progress_update", {"message": "Generating Python code with test cases..."}
        )

        # 2. Generate Code with Embedded Tests
        llm = get_gemini_service("pro")
        prompt = CODE_WITH_TESTS_PROMPT.format(
            topic=topic, context=context or "Use best practices and handle edge cases."
        )

        result = await llm.generate_json(prompt)

        code = result.get("code", "")
        if not code:
            return "Error: Failed to generate code. Please try again."

        # Extract code from markdown blocks if present
        if "```" in code:
            import re

            match = re.search(r"```(?:python)?\n(.*?)```", code, re.DOTALL)
            if match:
                code = match.group(1).strip()

        # Parse test cases
        test_cases: List[TestCase] = []
        for tc in result.get("test_cases", []):
            test_cases.append(
                TestCase(
                    input="",  # Empty input - tests are embedded in code
                    expected_output=str(tc.get("expected_output", "")),
                    description=tc.get("description", ""),
                )
            )

        # 3. Validate Syntax
        await adispatch_custom_event(
            "progress_update", {"message": "Validating syntax..."}
        )
        syntax_checker = get_syntax_checker()
        syntax_result = syntax_checker.check(code, "python")

        if not syntax_result.is_valid:
            return (
                f"### Generated Code\n\n```python\n{code}\n```\n\n"
                f"### ❌ Validation Failed\n"
                f"**Syntax Error**: {syntax_result.error_message}"
            )

        # 4. Run Tests
        await adispatch_custom_event(
            "progress_update", {"message": "Running test cases..."}
        )

        executor = get_code_executor()
        test_result = executor.run_tests(code, test_cases, language="python")

        # 5. Format Output
        status_icon = "✅" if test_result.is_valid else "⚠️"

        report = (
            f"### Generated Code\n\n```python\n{code}\n```\n\n"
            f"### {status_icon} Validation Report\n\n"
            f"- **Syntax**: ✅ Valid\n"
            f"- **Test Execution**: {test_result.passed_tests}/{len(test_cases)} Passed\n\n"
        )

        if test_result.failed_tests > 0:
            report += "**Failed Tests:**\n"
            for tr in test_result.test_results:
                if not tr["passed"]:
                    report += (
                        f"- {tr.get('description', 'Test')}\n"
                        f"  - Expected: `{tr['expected']}`\n"
                        f"  - Actual: `{tr['actual']}`\n"
                    )
        elif len(test_cases) > 0:
            report += "**Verified Cases:**\n"
            for tr in test_result.test_results:
                desc = tr.get("description", "Test")
                report += f"- ✓ {desc}: `{tr['actual']}`\n"
        else:
            report += "*No test cases could be generated.*"

        await adispatch_custom_event(
            "progress_update", {"message": "Validation complete!"}
        )

        return report

    except Exception as e:
        logger.error(f"[ValidatedCodeGen] Error: {e}")
        return f"Error generating validated code: {str(e)}"
