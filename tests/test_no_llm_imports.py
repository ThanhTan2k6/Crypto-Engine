"""
Invariant Test: Ensure src/engine/ contains ZERO LLM library imports.
Anti-Hallucination Architectural Boundary Enforcement.
"""

from pathlib import Path
import pytest

BANNED_IMPORTS = [
    "langchain",
    "langgraph",
    "google.genai",
    "openai",
    "instructor",
    "anthropic",
]

ENGINE_DIR = Path("src/engine")


def test_zero_llm_imports_in_quant_engine():
    assert ENGINE_DIR.exists(), "src/engine must exist"
    py_files = list(ENGINE_DIR.glob("**/*.py"))
    assert len(py_files) > 0, "No python files found in src/engine"

    violations = []
    for py_file in py_files:
        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()
            for banned in BANNED_IMPORTS:
                if banned in content:
                    violations.append(f"Banned import '{banned}' detected in {py_file}")

    assert len(violations) == 0, f"Architectural Violation: LLM imports found in quant engine:\n" + "\n".join(violations)
