"""Consumer runtime requirements applied to generated SDKs before packaging."""

from __future__ import annotations

import json
import re
from types import MappingProxyType
from typing import TYPE_CHECKING

from apigateway.biz.sdk.exceptions import SDKGenerateError

if TYPE_CHECKING:
    from pathlib import Path

SDK_RUNTIME_REQUIREMENTS = MappingProxyType({"python": ">=3.10", "javascript": ">=22"})


def _replace_declaration(path: Path, pattern: str, replacement: str) -> None:
    content, count = re.subn(pattern, replacement, path.read_text(), flags=re.MULTILINE)
    if count != 1:
        raise SDKGenerateError("generator_failed", f"unexpected runtime declaration in {path.name}")
    path.write_text(content)


def apply_runtime_requirements(language: str, output_dir: Path) -> None:
    if language not in SDK_RUNTIME_REQUIREMENTS:
        return
    requirement = SDK_RUNTIME_REQUIREMENTS[language]
    try:
        if language == "python":
            _replace_declaration(
                output_dir / "pyproject.toml",
                r'^requires-python = "[^"]+"$',
                f'requires-python = "{requirement}"',
            )
            setup = output_dir / "setup.py"
            _replace_declaration(setup, r'^PYTHON_REQUIRES = "[^"]+"$', f'PYTHON_REQUIRES = "{requirement}"')
            _replace_declaration(setup, r"^setup\($", "setup(\n    python_requires=PYTHON_REQUIRES,")
            _replace_declaration(output_dir / "README.md", r"^Python [^\n]+$", f"Python {requirement}")
        else:
            package_path = output_dir / "package.json"
            package = json.loads(package_path.read_text())
            package.setdefault("engines", {})["node"] = requirement
            package_path.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n")
            readme = output_dir / "README.md"
            readme.write_text(
                readme.read_text()
                + "\n## Runtime requirements\n\n"
                + f"- Node.js {requirement}. npm may only warn about unsupported Node.js versions; "
                "this is the SDK's supported minimum.\n"
                "- Browsers must support ES2015+, Promise, Fetch (including Request, Response and Headers), "
                "URL and URLSearchParams. FormData and Blob are required for form/file operations.\n"
                "- No polyfills are bundled. Environments missing these APIs must provide compatible polyfills.\n"
            )
    except (OSError, ValueError, TypeError) as error:
        raise SDKGenerateError("generator_failed", "cannot apply SDK runtime requirements") from error
