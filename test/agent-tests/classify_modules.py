#!/usr/bin/env python3
"""
classify_modules.py — Regenerate module-classification.json from case files.

Run after adding new cases or modules:
    python3 test/agent-tests/classify_modules.py

The script scans the ## Steps section of every case file and marks a module
as 'mutating' if any step contains a genuine state-changing action verb.
All other modules are classified as 'readonly' (parallel-safe).

Classification is intentionally conservative: if a match is ambiguous, the
module is kept as 'mutating' and the human reviewer should check the reason.
"""

import os
import re
import json
from datetime import date

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CASES_DIR = os.path.join(os.path.dirname(__file__), "cases")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "module-classification.json")

# Patterns that indicate a genuine state-changing step.
# Applied only within the ## Steps section of each case file.
# Each pattern is a (regex, example_match) tuple for documentation.
MUTATING_PATTERNS = [
    # Explicit action verbs as the subject of a numbered step
    (re.compile(r"^\d+\.\s+(?:新建|创建|提交|保存|删除|发布|停用|启用|导入|添加|修改|生成版本|编辑)", re.MULTILINE),
     "1. 新建组件 / 2. 编辑优先级"),
    # Click → mutating verb (e.g. "点击删除", "点击提交", "点击发布资源")
    # Note: 发布 must NOT be followed by 日志/记录 (those are view actions)
    (re.compile(r"点击.*?(?:提交|新建|创建|删除|保存|停用|启用|导入|修改|编辑|生成版本|添加)|点击.*?发布(?!日志|记录|时间)"),
     "点击提交按钮 / 点击发布资源"),
    # Verb at start of step without 点击 (e.g. "保存", "删除变量")
    (re.compile(r"^\d+\.\s+(?:保存|删除|新建|添加插件|导入资源)", re.MULTILINE),
     "2. 删除"),
    # Select-then-edit interactions (e.g. "选择文档编辑")
    (re.compile(r"(?:选择|点击).*?编辑"),
     "选择文档编辑"),
]

# Patterns that look like mutations but are NOT (filter values, expected results, etc.)
# These are stripped from the steps text before matching.
FALSE_POSITIVE_PATTERNS = [
    re.compile(r"操作类型.*?(?:创建|编辑|删除)"),    # filter value "操作类型：创建"
    re.compile(r"[：:]\s*(?:创建|编辑|删除)\b"),      # colon-prefixed filter values
    re.compile(r"(?:创建|编辑|删除)成功"),             # success messages
    re.compile(r"已(?:创建|发布|启用|停用)"),          # "已创建" = precondition text
    re.compile(r"发布日志|发布记录"),                  # viewing publish log/record (not publishing)
]

STEPS_SECTION = re.compile(r"## Steps\s*(.*?)(?:## |\Z)", re.DOTALL)


def extract_steps(content: str) -> str:
    m = STEPS_SECTION.search(content)
    return m.group(1) if m else ""


def is_mutating_steps(steps: str) -> bool:
    # Remove false-positive patterns from text before matching
    cleaned = steps
    for fp in FALSE_POSITIVE_PATTERNS:
        cleaned = fp.sub("", cleaned)
    for pattern, _ in MUTATING_PATTERNS:
        if pattern.search(cleaned):
            return True
    return False


def count_cases(cases_dir: str) -> int:
    total = 0
    for root, _, files in os.walk(cases_dir):
        total += sum(1 for f in files if f.endswith(".md"))
    return total


def classify(cases_dir: str) -> dict:
    modules = {}
    for module in sorted(os.listdir(cases_dir)):
        module_path = os.path.join(cases_dir, module)
        if not os.path.isdir(module_path):
            continue
        mutating = False
        for fname in sorted(os.listdir(module_path)):
            if not fname.endswith(".md"):
                continue
            try:
                content = open(os.path.join(module_path, fname), encoding="utf-8").read()
            except Exception:
                continue
            steps = extract_steps(content)
            if is_mutating_steps(steps):
                mutating = True
                break
        modules[module] = "mutating" if mutating else "readonly"
    return modules


def build_output(modules: dict, cases_dir: str) -> dict:
    readonly = [m for m, t in modules.items() if t == "readonly"]
    mutating = [m for m, t in modules.items() if t == "mutating"]
    return {
        "_meta": {
            "description": "Per-module read-only vs mutating classification for parallel batching strategy.",
            "algorithm": (
                "Scan ## Steps sections of all case files for action verbs "
                "(点击.*创建/编辑/删除/保存/提交/发布/停用/启用/导入/添加 or bare numbered steps with those verbs). "
                "False-positive patterns (filter values like 操作类型:创建, success messages, preconditions) "
                "are stripped before matching. Modules with genuine state-changing steps are 'mutating'; "
                "all others are 'readonly'."
            ),
            "regenerate": "python3 test/agent-tests/classify_modules.py",
            "lastUpdated": str(date.today()),
            "caseCount": count_cases(cases_dir),
            "readonlyCount": len(readonly),
            "mutatingCount": len(mutating),
        },
        "modules": {
            module: {"type": mtype, "reason": ""}
            for module, mtype in modules.items()
        },
    }


def main():
    if not os.path.isdir(CASES_DIR):
        print(f"ERROR: Cases directory not found: {CASES_DIR}")
        return 1

    print(f"Scanning cases in: {CASES_DIR}")
    modules = classify(CASES_DIR)

    readonly = [m for m, t in modules.items() if t == "readonly"]
    mutating = [m for m, t in modules.items() if t == "mutating"]

    print(f"\nClassification results ({len(modules)} modules):")
    print(f"  readonly  ({len(readonly)}): {', '.join(readonly)}")
    print(f"  mutating  ({len(mutating)}): {', '.join(mutating)}")

    # Load existing file to preserve human-written reasons
    existing = {}
    if os.path.exists(OUTPUT_FILE):
        try:
            existing = json.load(open(OUTPUT_FILE, encoding="utf-8")).get("modules", {})
        except Exception:
            pass

    output = build_output(modules, CASES_DIR)
    for module, entry in output["modules"].items():
        if module in existing and existing[module].get("reason"):
            # Preserve existing human-written reason; update only if type changed
            old_type = existing[module].get("type", "")
            if old_type != entry["type"]:
                entry["reason"] = f"[AUTO-UPDATED from {old_type}] "
            else:
                entry["reason"] = existing[module]["reason"]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"\nWritten to: {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
