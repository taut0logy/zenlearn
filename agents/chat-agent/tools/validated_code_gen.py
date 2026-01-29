"""
Validated Code Generation Tool.
"""

from typing import Optional
from langchain_core.tools import tool
from langchain_core.callbacks.manager import adispatch_custom_event

from content_gen_engine.agents.code_writer import get_code_writer
from content_gen_engine.validators.code_validator import (
    get_syntax_checker,
    get_code_executor,
)
from utils.logger import logger


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
            "progress_update", {"message": "Generating Python code..."}
        )

        # 2. Generate Code
        writer = get_code_writer()
        prompt = f"{topic}\nContext: {context}" if context else topic
        code = await writer.generate_code_only(prompt, language="python")

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

        # 4. Generate & Run Tests
        await adispatch_custom_event(
            "progress_update", {"message": "Generating and running test cases..."}
        )

        # Generate tests
        test_cases = await writer.generate_test_cases(
            code, language="python", num_tests=3
        )

        # Run tests
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
                        f"- Input: `{tr['input']}`\n"
                        f"  - Expected: `{tr['expected']}`\n"
                        f"  - Actual: `{tr['actual']}`\n"
                    )
        elif len(test_cases) > 0:
            report += "**Verified Cases:**\n"
            for tr in test_result.test_results:
                report += f"- `{tr['input']}` → `{tr['actual']}`\n"
        else:
            report += "*No test cases could be generated.*"

        await adispatch_custom_event(
            "progress_update", {"message": "Validation complete!"}
        )

        return report

    except Exception as e:
        logger.error(f"[ValidatedCodeGen] Error: {e}")
        return f"Error generating validated code: {str(e)}"
