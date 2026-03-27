#!/usr/bin/env python3
"""Convert Excel test cases (.xlsx) to markdown files for /agent-test.

Usage:
    python3 convert_excel.py <excel_file> [--output-dir test/agent-tests/cases] [--sheet 0]

Reads the first sheet (or specified sheet index) of an .xlsx file directly
using zipfile+ElementTree (no third-party dependencies required).

Columns expected: 模块 | 用例名称 | 用例等级 | 前置条件 | 用例步骤 | 预期结果 | 实际结果 | 备注 | 用例版本
"""

import os
import re
import sys
import unicodedata
from xml.etree import ElementTree
from zipfile import ZipFile

# ── Module → Directory mapping ──────────────────────────────────────────────
# Keys must match the Excel module names exactly (including full-width dashes)
MODULE_MAP = {
    "我的网关":                        ("01-my-gateway",             "/"),
    "我的网关-资源管理-资源配置":      ("02-resource-config",        "/gateways/:id/resources"),
    "资源管理-资源版本-版本列表":      ("03-resource-version",       "/gateways/:id/resource-versions"),
    "资源管理-资源版本-SDK列表":       ("04-sdk-list",               "/gateways/:id/resource-versions/sdks"),
    "环境管理-环境概览":               ("05-env-overview",           "/gateways/:id/stages"),
    "环境管理-环境概览-资源信息":      ("06-env-resource-info",      "/gateways/:id/stages/:stage/resources"),
    "环境管理-环境概览-插件管理":      ("07-env-plugin-mgmt",        "/gateways/:id/stages/:stage/plugins"),
    "环境管理-环境概览-变量管理":      ("08-env-variable-mgmt",      "/gateways/:id/stages/:stage/variables"),
    "环境管理-发布记录":               ("09-release-records",        "/gateways/:id/releases"),
    "后端服务":                        ("10-backend-service",        "/gateways/:id/backend-services"),
    "权限管理-权限审批":               ("11-permission-approval",    "/gateways/:id/permissions/approvals"),
    "权限管理－权限审批":              ("11-permission-approval",    "/gateways/:id/permissions/approvals"),
    "权限管理-应用权限":               ("12-app-permissions",        "/gateways/:id/permissions/apps"),
    "运行数据-流水日志":               ("13-access-log",             "/gateways/:id/logs"),
    "运行数据-统计报表":               ("14-statistics",             "/gateways/:id/statistics"),
    "在线调试":                        ("15-online-debug",           "/gateways/:id/online-debug"),
    "在线调试-请求记录":               ("16-debug-request-history",  "/gateways/:id/online-debug/history"),
    "基本信息":                        ("17-basic-info",             "/gateways/:id/basic"),
    "MCP-MCP Server":                  ("18-mcp-server",             "/gateways/:id/mcp"),
    "MCP-MCP 权限审批":                ("19-mcp-permission-approval","/gateways/:id/mcp/approvals"),
    "操作记录":                        ("20-operation-records",      "/gateways/:id/audit"),
    "组件管理-简介":                   ("21-component-intro",        "/components/intro"),
    "组件管理-系统管理":               ("22-system-mgmt",            "/components/systems"),
    "组件管理-组件管理":               ("23-component-mgmt",         "/components/manage"),
    "组件管理－组件管理":              ("23-component-mgmt",         "/components/manage"),
    "文档分类":                        ("24-doc-category",           "/docs/categories"),
    "实时运行数据":                    ("25-realtime-data",          "/gateways/:id/realtime-data"),
    "API文档-网关API文档":             ("26-gateway-api-doc",        "/api-docs/gateways"),
    "API文档-组件API文档":             ("27-component-api-doc",      "/api-docs/components"),
    "平台工具-工具箱":                 ("28-platform-toolbox",       "/tools/toolbox"),
    "平台工具-自动化接入网关":         ("29-auto-gateway-access",    "/tools/auto-access"),
    "平台工具-可编程网关":             ("30-programmable-gateway",   "/tools/programmable"),
    "MCP市场":                         ("31-mcp-market",             "/mcp-market"),
}

# ── Chinese → English slug mapping for common case name patterns ─────────
SLUG_REPLACEMENTS = [
    # Actions
    ("新建", "create"),
    ("取消新建", "cancel-create"),
    ("取消", "cancel"),
    ("删除", "delete"),
    ("编辑", "edit"),
    ("修改", "modify"),
    ("更新", "update"),
    ("查看", "view"),
    ("查询", "query"),
    ("搜索", "search"),
    ("筛选", "filter"),
    ("过滤", "filter"),
    ("排序", "sort"),
    ("导入", "import"),
    ("导出", "export"),
    ("复制", "copy"),
    ("克隆", "clone"),
    ("发布", "publish"),
    ("下架", "unpublish"),
    ("上架", "publish"),
    ("启用", "enable"),
    ("停用", "disable"),
    ("禁用", "disable"),
    ("刷新", "refresh"),
    ("重置", "reset"),
    ("提交", "submit"),
    ("确认", "confirm"),
    ("添加", "add"),
    ("移除", "remove"),
    ("批量", "batch"),
    ("全选", "select-all"),
    ("展开", "expand"),
    ("收起", "collapse"),
    ("切换", "switch"),
    ("跳转", "navigate"),
    ("返回", "back"),
    ("关闭", "close"),
    ("打开", "open"),
    ("下载", "download"),
    ("上传", "upload"),
    ("申请", "apply"),
    ("审批", "approve"),
    ("通过", "pass"),
    ("拒绝", "reject"),
    ("续期", "renew"),
    ("撤销", "revoke"),
    ("绑定", "bind"),
    ("解绑", "unbind"),
    # Nouns
    ("网关", "gateway"),
    ("资源", "resource"),
    ("版本", "version"),
    ("环境", "env"),
    ("插件", "plugin"),
    ("变量", "variable"),
    ("后端服务", "backend-service"),
    ("权限", "permission"),
    ("应用", "app"),
    ("日志", "log"),
    ("统计", "statistics"),
    ("报表", "report"),
    ("调试", "debug"),
    ("请求", "request"),
    ("记录", "record"),
    ("基本信息", "basic-info"),
    ("操作", "operation"),
    ("组件", "component"),
    ("系统", "system"),
    ("文档", "doc"),
    ("分类", "category"),
    ("名称", "name"),
    ("描述", "description"),
    ("标签", "tag"),
    ("配置", "config"),
    ("列表", "list"),
    ("详情", "detail"),
    ("概览", "overview"),
    ("设置", "settings"),
    ("分页", "pagination"),
    ("页码", "page-num"),
    ("普通", "standard"),
    ("可编程", "programmable"),
    ("公开", "public"),
    ("不公开", "private"),
    ("维护人员", "maintainer"),
    ("字符", "char"),
    ("为空", "empty"),
    ("必填", "required"),
    ("选填", "optional"),
    ("状态", "status"),
    ("类型", "type"),
    ("模糊搜索", "fuzzy-search"),
    ("精确搜索", "exact-search"),
    ("前端", "frontend"),
    ("后端", "backend"),
    ("路径", "path"),
    ("方法", "method"),
    ("地址", "address"),
    ("超时时间", "timeout"),
    ("认证", "auth"),
    ("校验", "validate"),
    ("工具", "tool"),
    ("市场", "market"),
    ("服务器", "server"),
    ("弹窗", "dialog"),
    ("按钮", "button"),
    ("下拉框", "dropdown"),
    ("输入框", "input"),
    ("搜索框", "search-box"),
    ("表格", "table"),
    ("表单", "form"),
    ("标题", "title"),
    ("内容", "content"),
    ("链接", "link"),
    ("首字符", "first-char"),
]


# ── Excel reader (no third-party deps) ──────────────────────────────────────

XLSX_NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _col_letter_to_index(col: str) -> int:
    """Convert column letter(s) to 0-based index. A→0, B→1, ..., Z→25, AA→26."""
    result = 0
    for ch in col.upper():
        result = result * 26 + (ord(ch) - ord("A") + 1)
    return result - 1


def read_xlsx(path: str, sheet_index: int = 0) -> list[dict]:
    """Read an .xlsx file and return rows as list of dicts keyed by header names.

    Uses zipfile + ElementTree to parse the XML directly — avoids openpyxl
    compatibility issues with certain .xlsx files (e.g., custom fill styles).
    """
    z = ZipFile(path)

    # 1. Parse shared strings
    shared_strings: list[str] = []
    try:
        ss_tree = ElementTree.parse(z.open("xl/sharedStrings.xml"))
        for si in ss_tree.findall(".//s:si", XLSX_NS):
            text = "".join(t.text or "" for t in si.findall(".//s:t", XLSX_NS))
            shared_strings.append(text)
    except KeyError:
        pass  # No shared strings file

    # 2. Determine which sheet file to read
    #    Typically xl/worksheets/sheet1.xml, sheet2.xml, etc.
    sheet_file = f"xl/worksheets/sheet{sheet_index + 1}.xml"
    if sheet_file not in z.namelist():
        # Fallback: try to find via workbook rels
        available = sorted(n for n in z.namelist() if n.startswith("xl/worksheets/sheet"))
        if sheet_index < len(available):
            sheet_file = available[sheet_index]
        else:
            raise FileNotFoundError(f"Sheet index {sheet_index} not found. Available: {available}")

    # 3. Parse sheet data
    sheet_tree = ElementTree.parse(z.open(sheet_file))
    xml_rows = sheet_tree.findall(".//s:sheetData/s:row", XLSX_NS)

    if not xml_rows:
        return []

    # 4. Extract all rows as lists, preserving column positions
    def _parse_row(xml_row) -> dict[int, str]:
        """Return {col_index: value} for a row."""
        cells = {}
        for cell in xml_row.findall("s:c", XLSX_NS):
            ref = cell.get("r", "")
            col_letters = re.match(r"([A-Z]+)", ref)
            if not col_letters:
                continue
            col_idx = _col_letter_to_index(col_letters.group(1))

            cell_type = cell.get("t", "")
            v_elem = cell.find("s:v", XLSX_NS)
            raw_val = v_elem.text if v_elem is not None else ""

            if cell_type == "s" and raw_val:
                val = shared_strings[int(raw_val)]
            elif cell_type == "inlineStr":
                val = "".join(
                    t.text or "" for t in cell.findall(".//s:t", XLSX_NS)
                )
            else:
                val = raw_val or ""

            cells[col_idx] = val
        return cells

    # Parse header row
    header_cells = _parse_row(xml_rows[0])
    max_col = max(header_cells.keys()) + 1 if header_cells else 0
    headers = [header_cells.get(i, f"col_{i}") for i in range(max_col)]

    # Parse data rows
    rows = []
    for xml_row in xml_rows[1:]:
        cell_dict = _parse_row(xml_row)
        if not cell_dict:
            continue
        row = {}
        for i, header in enumerate(headers):
            row[header] = cell_dict.get(i, "")
        rows.append(row)

    return rows


# ── Slug generation ─────────────────────────────────────────────────────────


def chinese_to_slug(text: str) -> str:
    """Convert Chinese case name to English kebab-case slug."""
    slug = text.strip()

    # Normalize full-width characters to ASCII
    slug = unicodedata.normalize("NFKC", slug)

    # Apply replacements (longest first to avoid partial matches)
    sorted_replacements = sorted(SLUG_REPLACEMENTS, key=lambda x: len(x[0]), reverse=True)
    for cn, en in sorted_replacements:
        slug = slug.replace(cn, f"-{en}-")

    # Replace common separators
    slug = re.sub(r"[（(][^)）]*[)）]", "", slug)  # Remove parenthetical text
    slug = re.sub(r"[，,。.、/\\|·~～！!？?：:；;""''\x22\x27【】{｝《》<>＋+＝=＊*＆&＃#＠@％%\x5b\x5d]", "-", slug)
    slug = re.sub(r"[\u4e00-\u9fff]+", "-", slug)  # Replace remaining Chinese chars
    slug = re.sub(r"[^a-zA-Z0-9-]", "-", slug)     # Replace non-alphanumeric
    slug = re.sub(r"-+", "-", slug)                  # Collapse multiple dashes
    slug = slug.strip("-").lower()

    # Limit length
    if len(slug) > 60:
        slug = slug[:60].rstrip("-")

    return slug or "case"


# ── Markdown formatting ─────────────────────────────────────────────────────


def format_steps(raw_steps: str) -> str:
    """Format steps into numbered markdown list."""
    if not raw_steps:
        return "1. (无步骤描述)\n"

    lines = raw_steps.strip().split("\n")
    result = []
    step_num = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check if line starts with a number prefix like "1." or "1、" or "1："
        m = re.match(r"^(\d+)[.、：:)\]]\s*", line)
        if m:
            step_num = int(m.group(1))
            text = line[m.end():].strip()
            if text:
                result.append(f"{step_num}. {text}")
        else:
            # Continuation of previous step or unnumbered step
            if result:
                result[-1] += f"；{line}"
            else:
                step_num += 1
                result.append(f"{step_num}. {line}")

    if not result:
        return "1. (无步骤描述)\n"

    return "\n".join(result) + "\n"


def format_verify(raw_expected: str) -> str:
    """Format expected results into bullet points."""
    if not raw_expected:
        return "- 操作成功\n- 无报错信息\n"

    lines = raw_expected.strip().split("\n")
    result = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Remove leading numbering
        line = re.sub(r"^(\d+)[.、：:)\]]\s*", "", line)

        if line:
            result.append(f"- {line}")

    if not result:
        return "- 操作成功\n- 无报错信息\n"

    return "\n".join(result) + "\n"


def generate_markdown(row: dict, url_pattern: str) -> str:
    """Generate markdown content for a test case."""
    module = row.get("模块", "")
    case_name = row.get("用例名称", "")
    priority = row.get("用例等级", "P2")
    if priority not in ("P1", "P2", "P3"):
        priority = "P2"
    prerequisites = row.get("前置条件", "") or "已登录"
    steps = format_steps(row.get("用例步骤", ""))
    verify = format_verify(row.get("预期结果", ""))

    md = f"""# Case: {module} - {case_name}

**Page**: {url_pattern}
**Priority**: {priority}
**Prerequisites**: {prerequisites}

## Steps

{steps}
## Verify

{verify}"""
    return md


# ── Main ────────────────────────────────────────────────────────────────────


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 convert_excel.py <excel_file> [--output-dir DIR] [--sheet N]")
        print()
        print("Reads the first sheet of an .xlsx file and generates markdown test case files.")
        print()
        print("Options:")
        print("  --output-dir DIR  Output directory (default: test/agent-tests/cases)")
        print("  --sheet N         Sheet index, 0-based (default: 0)")
        sys.exit(1)

    input_file = sys.argv[1]
    output_dir = "test/agent-tests/cases"
    sheet_index = 0

    for i, arg in enumerate(sys.argv):
        if arg == "--output-dir" and i + 1 < len(sys.argv):
            output_dir = sys.argv[i + 1]
        if arg == "--sheet" and i + 1 < len(sys.argv):
            sheet_index = int(sys.argv[i + 1])

    if not input_file.endswith(".xlsx"):
        print(f"Error: Expected .xlsx file, got: {input_file}")
        sys.exit(1)

    print(f"Reading: {input_file} (sheet {sheet_index})")
    rows = read_xlsx(input_file, sheet_index)
    print(f"Parsed {len(rows)} data rows")

    # Group by module
    modules: dict[str, list[dict]] = {}
    for row in rows:
        mod = row.get("模块", "").strip()
        if not mod:
            continue
        modules.setdefault(mod, []).append(row)

    print(f"Modules found: {len(modules)}")
    for mod, cases in modules.items():
        print(f"  {mod}: {len(cases)} cases")

    # Generate files
    total_files = 0
    skipped_modules = []

    for module_name, cases in modules.items():
        if module_name not in MODULE_MAP:
            skipped_modules.append((module_name, len(cases)))
            continue

        dir_name, url_pattern = MODULE_MAP[module_name]
        dir_path = os.path.join(output_dir, dir_name)
        os.makedirs(dir_path, exist_ok=True)

        # Track slugs for deduplication
        used_slugs: dict[str, int] = {}

        for idx, case in enumerate(cases, 1):
            case_name = case.get("用例名称", "")
            slug = chinese_to_slug(case_name) if case_name else "case"

            # Deduplicate slugs
            if slug in used_slugs:
                used_slugs[slug] += 1
                slug = f"{slug}-{used_slugs[slug]}"
            else:
                used_slugs[slug] = 1

            filename = f"{idx:02d}-{slug}.md"
            filepath = os.path.join(dir_path, filename)

            md = generate_markdown(case, url_pattern)

            with open(filepath, "w") as f:
                f.write(md)

            total_files += 1

    if skipped_modules:
        print(f"\nWARNING: Skipped {len(skipped_modules)} unknown modules:")
        for mod, cnt in skipped_modules:
            print(f"  '{mod}': {cnt} cases")

    print(f"\nGenerated {total_files} markdown files in {output_dir}/")

    # List directories created
    if os.path.exists(output_dir):
        dirs = sorted(os.listdir(output_dir))
        print(f"\nDirectories ({len(dirs)}):")
        for d in dirs:
            full = os.path.join(output_dir, d)
            if os.path.isdir(full):
                count = len([f for f in os.listdir(full) if f.endswith(".md")])
                print(f"  {d}/ ({count} files)")


if __name__ == "__main__":
    main()
