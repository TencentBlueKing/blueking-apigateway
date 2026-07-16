#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 一致性检查工具
检查 API 代码实现、YAML 网关资源定义、API 文档三者是否一致。

用法:
    python check_api_consistency.py [--scope SCOPE] [--api OPERATION_ID] [--fix] [--json] [--project-dir DIR]
"""

import argparse
import ast
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("错误: 需要 PyYAML。请运行: pip install pyyaml")
    sys.exit(1)

# ── 颜色输出 ──────────────────────────────────────────────────────────
# 非 TTY 环境（如重定向到文件）时禁用颜色，避免乱码
_USE_COLOR = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

RED = "\033[91m" if _USE_COLOR else ""
YELLOW = "\033[93m" if _USE_COLOR else ""
GREEN = "\033[92m" if _USE_COLOR else ""
CYAN = "\033[96m" if _USE_COLOR else ""
DIM = "\033[2m" if _USE_COLOR else ""
RESET = "\033[0m" if _USE_COLOR else ""
BOLD = "\033[1m" if _USE_COLOR else ""


def c(text: str, color: str) -> str:
    if not color:
        return text
    return f"{color}{text}{RESET}"


# ── Django URL 解析器（基于 AST） ────────────────────────────────────


def normalize_path(path_str: str) -> str:
    """将 Django URL 参数格式 <type:name> 转换为 YAML 格式 {name}"""
    result = re.sub(r"<(?:\w+:)?(\w+)>", r"{\1}", path_str)
    # 确保以 / 结尾
    if result and not result.endswith("/"):
        result += "/"
    return result


def parse_django_urls(filepath: Path, prefix: str = "") -> list[dict]:
    """
    使用 Python AST 模块解析 Django urls.py，提取所有完整的路由定义。
    正确处理嵌套的 include() 和 path() 调用，包括 urlpatterns += [...] 形式。
    返回: [{"full_path": "/api/v2/open/gateways/", "view_class": "GatewayListApi", "name": "...", "line": N}, ...]
    """
    content = filepath.read_text(encoding="utf-8")
    tree = ast.parse(content, filename=str(filepath))
    routes: list[dict] = []

    def _get_str_value(node: ast.AST) -> str | None:
        """从 AST 节点获取字符串常量值"""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

    def _get_view_class(node: ast.AST) -> str | None:
        """从 views.XxxApi.as_view() 调用中提取 View 类名"""
        if isinstance(node, ast.Call):
            func = node.func
            # views.XxxApi.as_view() 形式
            if isinstance(func, ast.Attribute) and func.attr == "as_view":
                if isinstance(func.value, ast.Attribute):
                    return func.value.attr
        return None

    def _get_name_kwarg(call_node: ast.Call) -> str | None:
        """从 path() 调用中提取 name= 关键字参数"""
        for kw in call_node.keywords:
            if kw.arg == "name":
                return _get_str_value(kw.value)
        return None

    def _get_func_name(node: ast.AST) -> str | None:
        """获取函数调用的名称"""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return None

    def _process_path_call(call_node: ast.Call, current_prefix: str):
        """处理单个 path() 调用"""
        if not call_node.args:
            return
        url_pattern = _get_str_value(call_node.args[0])
        if url_pattern is None:
            return

        full_prefix = current_prefix + url_pattern

        if len(call_node.args) >= 2:
            second_arg = call_node.args[1]

            if isinstance(second_arg, ast.Call):
                func_name = _get_func_name(second_arg.func)

                if func_name == "include" and second_arg.args:
                    # path("prefix/", include([...])) — 递归处理
                    inner = second_arg.args[0]
                    if isinstance(inner, ast.List):
                        _process_list(inner, full_prefix)
                else:
                    # path("prefix/", views.XxxApi.as_view(), name="...") — 叶子路由
                    view_class = _get_view_class(second_arg)
                    name = _get_name_kwarg(call_node)
                    if view_class:
                        routes.append(
                            {
                                "full_path": full_prefix,
                                "view_class": view_class,
                                "name": name or "",
                                "line": call_node.lineno,
                                "filepath": str(filepath),
                            }
                        )

    def _process_list(list_node: ast.List, current_prefix: str):
        """处理 urlpatterns 列表中的所有 path() 调用"""
        for elt in list_node.elts:
            if isinstance(elt, ast.Call) and _get_func_name(elt.func) == "path":
                _process_path_call(elt, current_prefix)

    # 遍历 AST 找到 urlpatterns = [...] 和 urlpatterns += [...]
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "urlpatterns":
                    if isinstance(node.value, ast.List):
                        _process_list(node.value, prefix)
        elif isinstance(node, ast.AugAssign):
            if isinstance(node.target, ast.Name) and node.target.id == "urlpatterns":
                if isinstance(node.value, ast.List):
                    _process_list(node.value, prefix)
        # 处理条件块中的 urlpatterns += [...]（如 if not settings.XXX:）
        elif isinstance(node, ast.If):
            for sub_node in ast.walk(node):
                if isinstance(sub_node, ast.AugAssign):
                    if isinstance(sub_node.target, ast.Name) and sub_node.target.id == "urlpatterns":
                        if isinstance(sub_node.value, ast.List):
                            _process_list(sub_node.value, prefix)

    return routes


# ── View 方法解析 ────────────────────────────────────────────────────


def parse_view_methods(filepath: Path) -> dict[str, list[str]]:
    """从 views.py 提取每个 View 类支持的 HTTP 方法"""
    content = filepath.read_text(encoding="utf-8")
    result = {}
    current_class = None
    methods: list[str] = []

    for line in content.splitlines():
        class_match = re.match(r"^class\s+(\w+)", line)
        if class_match:
            if current_class and methods:
                result[current_class] = methods
            current_class = class_match.group(1)
            methods = []
            continue
        method_match = re.match(
            r"^\s+def\s+(get|post|put|delete|patch|list|create|retrieve|update|destroy|partial_update)\b", line
        )
        if method_match and current_class:
            m = method_match.group(1).upper()
            # DRF 的 list/create/retrieve/update/destroy/partial_update 映射到 HTTP 方法
            drf_map = {
                "LIST": "GET",
                "CREATE": "POST",
                "RETRIEVE": "GET",
                "UPDATE": "PUT",
                "DESTROY": "DELETE",
                "PARTIAL_UPDATE": "PATCH",
            }
            methods.append(drf_map.get(m, m))

    if current_class and methods:
        result[current_class] = list(set(methods))

    return result


# ── View → Serializer 映射解析 ────────────────────────────────────


def parse_view_serializers(filepath: Path) -> dict[str, dict[str, str]]:
    """
    从 views.py 提取 View 类使用的 Serializer 信息。
    返回: {ClassName: {"serializer_class": "SLZName", "input_slz": "InputSLZName"}}
    """
    content = filepath.read_text(encoding="utf-8")
    result = {}
    current_class = None
    current_info: dict[str, str] = {}
    current_method = None

    for line in content.splitlines():
        class_match = re.match(r"^class\s+(\w+)", line)
        if class_match:
            if current_class:
                result[current_class] = current_info
            current_class = class_match.group(1)
            current_info = {}
            current_method = None
            continue

        # serializer_class = serializers.XxxSLZ 或 serializer_class = XxxSLZ
        slz_match = re.match(r"^\s+serializer_class\s*=\s*(?:serializers\.)?(\w+)", line)
        if slz_match and current_class:
            current_info["serializer_class"] = slz_match.group(1)

        # 方法开头
        method_match = re.match(
            r"^\s+def\s+(get|post|put|delete|patch|list|create|retrieve|update|destroy|partial_update)\b", line
        )
        if method_match:
            current_method = method_match.group(1)

        # 方法体内的 slz = XxxInputSLZ(data=request.xxx) 或 serializers.XxxInputSLZ(data=request.xxx)
        if current_method and current_class:
            # 匹配 slz = serializers.XxxInputSLZ(data=...)
            input_match = re.search(r"(?:serializers\.)?(\w+(?:Input|Query)\w*SLZ)\s*\(data=", line)
            if input_match:
                current_info["input_slz"] = input_match.group(1)

    if current_class:
        result[current_class] = current_info

    return result


# ── Serializer 字段解析 ────────────────────────────────────────────


def parse_serializer_fields(filepath: Path) -> dict[str, list[dict]]:
    """
    从 serializers.py 解析所有 Serializer 类的字段定义。
    支持基类继承：子类会继承基类中定义的字段。
    返回: {ClassName: [{"name": "field_name", "type": "CharField", "required": True/False}, ...]}
    """
    content = filepath.read_text(encoding="utf-8")
    result: dict[str, list[dict]] = {}
    # 追踪类继承关系：ClassName → [BaseClass1, BaseClass2, ...]
    class_bases: dict[str, list[str]] = {}
    current_class = None
    current_fields: list[dict] = []

    # 也追踪 Meta.fields 以处理 ModelSerializer
    in_meta = False
    meta_fields: list[str] = []
    in_meta_fields = False  # 正在读取多行 fields = [...]
    meta_fields_buffer = ""

    for line in content.splitlines():
        # 类定义：提取类名和基类
        class_match = re.match(r"^class\s+(\w+)\s*\(([^)]*)\)", line)
        if class_match:
            # 保存上一个类：将 Meta.fields 中未显式声明的字段也加入
            if current_class:
                explicit_names = {f["name"] for f in current_fields}
                for mf in meta_fields:
                    if mf not in explicit_names:
                        current_fields.append(
                            {"name": mf, "type": "ModelField", "required": False, "output_only": False}
                        )
                if current_fields:
                    result[current_class] = current_fields
            current_class = class_match.group(1)
            # 提取基类列表
            bases_str = class_match.group(2)
            bases = [b.strip().split(".")[-1] for b in bases_str.split(",") if b.strip()]
            class_bases[current_class] = bases
            current_fields = []
            in_meta = False
            meta_fields = []
            in_meta_fields = False
            meta_fields_buffer = ""
            continue

        if not current_class:
            continue

        # Meta class
        if re.match(r"^\s+class\s+Meta\s*:", line):
            in_meta = True
            continue
        if in_meta:
            # 处理多行 fields = [...] 定义
            if in_meta_fields:
                meta_fields_buffer += line
                if "]" in line or ")" in line:
                    meta_fields = re.findall(r'["\'](\w+)["\']', meta_fields_buffer)
                    in_meta_fields = False
            elif re.search(r"fields\s*=\s*[\[\(]", line):
                meta_fields_buffer = line
                if "]" in line.split("=", 1)[-1] or ")" in line.split("=", 1)[-1]:
                    # 单行完整定义
                    meta_fields = re.findall(r'["\'](\w+)["\']', meta_fields_buffer)
                else:
                    # 多行定义，继续读取
                    in_meta_fields = True
            # 缩进回退则退出 Meta
            if line.strip() and not line.startswith(" " * 8) and not line.startswith("\t\t"):
                in_meta = False

        # 字段定义: name = serializers.CharField(...)
        field_match = re.match(r"^\s{4}(\w+)\s*=\s*(?:serializers\.)?(\w+(?:Field|Serializer|SLZ)?)\s*\(", line)
        if field_match and current_class:
            fname = field_match.group(1)
            ftype = field_match.group(2)

            # 跳过隐式/输出字段
            # - HiddenField: 隐式注入的参数（如 CurrentGatewayDefault），用户无需传入
            # - SerializerMethodField: 仅输出字段
            implicit_types = {"HiddenField"}
            if ftype in implicit_types:
                continue

            output_only_types = {"SerializerMethodField"}
            if ftype in output_only_types:
                current_fields.append({"name": fname, "type": ftype, "required": False, "output_only": True})
                continue

            # 判断 required
            required = True  # Django REST framework 默认 required=True
            if "required=False" in line:
                required = False
            if "read_only=True" in line:
                # read_only 字段是输出字段
                current_fields.append({"name": fname, "type": ftype, "required": False, "output_only": True})
                continue

            current_fields.append({"name": fname, "type": ftype, "required": required, "output_only": False})

    if current_class:
        explicit_names = {f["name"] for f in current_fields}
        for mf in meta_fields:
            if mf not in explicit_names:
                current_fields.append({"name": mf, "type": "ModelField", "required": False, "output_only": False})
        if current_fields:
            result[current_class] = current_fields

    # 继承合并：将基类字段合并到子类中（仅限同文件内的基类）
    for cls_name, bases in class_bases.items():
        if cls_name not in result:
            continue
        child_field_names = {f["name"] for f in result[cls_name]}
        for base_name in bases:
            if base_name in result:
                for field in result[base_name]:
                    if field["name"] not in child_field_names:
                        result[cls_name].append(field)
                        child_field_names.add(field["name"])

    return result


# ── DRF 字段类型 → OpenAPI 类型映射 ─────────────────────────────────

DRF_TO_OPENAPI_TYPE = {
    "CharField": "string",
    "RegexField": "string",
    "SlugField": "string",
    "URLField": "string",
    "EmailField": "string",
    "FileField": "string",
    "IntegerField": "integer",
    "FloatField": "number",
    "DecimalField": "number",
    "BooleanField": "boolean",
    "NullBooleanField": "boolean",
    "ListField": "array",
    "ListSerializer": "array",
    "DictField": "object",
    "JSONField": "object",
    "ChoiceField": "string",
    "MultipleChoiceField": "array",
    "SerializerMethodField": "string",
}


# ── 检查器 ────────────────────────────────────────────────────────────


class APIConsistencyChecker:
    SCOPE_MAP = {
        "v2_open": {"url_prefix": "/api/v2/open/", "code_dir": "open"},
        "v2_inner": {"url_prefix": "/api/v2/inner/", "code_dir": "inner"},
        "v2_sync": {"url_prefix": "/api/v2/sync/", "code_dir": "sync"},
    }

    # 默认值（可被 config.yaml 覆盖）
    SKIP_BACKENDS = {"core-api", "mcp-proxy"}
    KNOWN_SPECIAL_CASES = {
        "v2_open_get_gateway_public_key",
        "v2_open_get_gateway_public_key_new",
        "v2_open_oauth_protected_resource",
    }
    PAGINATION_PARAMS = {"limit", "offset", "page", "page_size"}

    def __init__(self, project_dir: str, json_output: bool = False):
        self.project_dir = Path(project_dir).resolve()
        self.base = self.project_dir / "src" / "dashboard" / "apigateway" / "apigateway"
        self.resources_yaml = self.base / "data" / "apigw-definitions" / "bk-apigateway-resources.yaml"
        self.definition_yaml = self.base / "data" / "apigw-definitions" / "bk-apigateway-definition.yaml"
        self.docs_dir = self.base / "data" / "apidocs" / "zh"
        self.apis_dir = self.base / "apis" / "v2"
        self.json_output = json_output

        # 从 config.yaml 加载配置（覆盖类级别的默认值）
        self._load_config()

        # YAML 中的 API: operationId → info
        self.yaml_apis: dict[str, dict] = {}
        # YAML path → operationId 的映射（用于从路径反查）
        self.yaml_path_method_to_opid: dict[str, str] = {}
        # 代码中的路由: 按 normalized_path 索引
        self.code_routes: dict[str, dict] = {}
        # 文档: operationId → info
        self.docs: dict[str, dict] = {}
        # View 方法映射: class_name → [methods]
        self.view_methods: dict[str, list[str]] = {}
        # View → Serializer 映射: class_name → {"serializer_class": ..., "input_slz": ...}
        self.view_serializer_map: dict[str, dict[str, str]] = {}
        # Serializer 字段: SLZ_class_name → [{"name", "type", "required", "output_only"}, ...]
        self.serializer_fields: dict[str, list[dict]] = {}

        self.skipped: list[dict] = []
        self.errors: list[dict] = []
        self.warnings: list[dict] = []

    def _load_config(self):
        """从 config.yaml 加载配置，覆盖类级别的默认值"""
        config_path = Path(__file__).resolve().parent / "config.yaml"
        if not config_path.exists():
            return
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
            if "skip_backends" in cfg:
                self.SKIP_BACKENDS = set(cfg["skip_backends"])
            if "known_special_cases" in cfg:
                self.KNOWN_SPECIAL_CASES = set(cfg["known_special_cases"])
            if "pagination_params" in cfg:
                self.PAGINATION_PARAMS = set(cfg["pagination_params"])
        except Exception:
            pass  # 配置文件解析失败时使用默认值

    def _log(self, level: str, check: str, op_id: str, msg: str, suggestion: str = ""):
        entry = {"check": check, "operation_id": op_id, "message": msg, "suggestion": suggestion}
        if level == "error":
            self.errors.append(entry)
        else:
            self.warnings.append(entry)

    # ── 收集 YAML ─────────────────────────────────────────────────────

    def collect_yaml(self, scope: str | None = None, target_api: str | None = None):
        if not self.resources_yaml.exists():
            print(c(f"错误: 未找到 {self.resources_yaml}", RED))
            return

        with open(self.resources_yaml, "r", encoding="utf-8") as f:
            raw_content = f.read()

        # $ref 检测：当前不支持 $ref 引用，如果发现则警告
        if "$ref" in raw_content:
            ref_count = raw_content.count("$ref")
            print(c(f"⚠️  YAML 中发现 {ref_count} 处 $ref 引用，当前工具不会解析 $ref，可能导致部分定义丢失", YELLOW))

        data = yaml.safe_load(raw_content)

        for path_str, methods in data.get("paths", {}).items():
            for method, detail in methods.items():
                if method in ("parameters", "summary", "description"):
                    continue
                op_id = detail.get("operationId", "")
                if not op_id:
                    continue
                # --api 过滤
                if target_api and op_id != target_api:
                    continue
                # 跳过 v1 API（已废弃，不再检查）
                if path_str.startswith("/api/v1/"):
                    continue
                # scope 过滤
                if scope and scope != "all":
                    if (
                        scope == "v2_open"
                        and not path_str.startswith("/api/v2/open/")
                        or scope == "v2_inner"
                        and not path_str.startswith("/api/v2/inner/")
                        or scope == "v2_sync"
                        and not path_str.startswith("/api/v2/sync/")
                    ):
                        continue

                x_res = detail.get("x-bk-apigateway-resource", {})
                backend = x_res.get("backend", {})

                # 标准化 YAML 路径（移除尾部 / 差异）
                norm_path = path_str.rstrip("/") + "/"

                self.yaml_apis[op_id] = {
                    "path": path_str,
                    "norm_path": norm_path,
                    "method": method.upper(),
                    "tags": list(set(detail.get("tags", []))),
                    "description": detail.get("description", ""),
                    "parameters": detail.get("parameters", []),
                    "request_body": detail.get("requestBody", {}),
                    "responses": detail.get("responses", {}),
                    "backend_path": backend.get("path", ""),
                    "backend_method": backend.get("method", "").upper(),
                    "backend_name": backend.get("name", "default"),
                    "is_public": x_res.get("isPublic", False),
                    "auth_config": x_res.get("authConfig", {}),
                }

                # 构建路径+方法 → operationId 的映射
                key = f"{method.upper()}:{norm_path}"
                self.yaml_path_method_to_opid[key] = op_id

    # ── 收集代码 ──────────────────────────────────────────────────────

    def collect_code(self, scope: str | None = None):
        # ── 扫描 v2 API 代码 ────────────────────────────────────────────
        if not self.apis_dir.exists():
            return

        dirs_to_scan = []
        if scope in (None, "all"):
            dirs_to_scan = ["open", "inner", "sync"]
        elif scope in self.SCOPE_MAP:
            dirs_to_scan = [self.SCOPE_MAP[scope]["code_dir"]]

        for sub in dirs_to_scan:
            urls_file = self.apis_dir / sub / "urls.py"
            scope_prefix = f"/api/v2/{sub}/"

            if urls_file.exists():
                routes = parse_django_urls(urls_file, prefix=scope_prefix)
                for route in routes:
                    norm = normalize_path(route["full_path"]).rstrip("/") + "/"
                    route["norm_path"] = norm
                    route["scope_dir"] = sub
                    self.code_routes[norm] = route

            # 收集 View 方法信息 和 View→Serializer 映射
            # 使用 "子目录:类名" 作为 key，避免不同子模块同名类互相覆盖
            for vf in self.apis_dir.glob(f"{sub}/views*.py"):
                methods_map = parse_view_methods(vf)
                for cls_name, methods in methods_map.items():
                    self.view_methods[f"{sub}:{cls_name}"] = methods
                slz_map = parse_view_serializers(vf)
                for cls_name, info in slz_map.items():
                    self.view_serializer_map[f"{sub}:{cls_name}"] = info

            # 收集 Serializer 字段定义
            for sf in self.apis_dir.glob(f"{sub}/serializers*.py"):
                fields_map = parse_serializer_fields(sf)
                for cls_name, fields in fields_map.items():
                    self.serializer_fields[f"{sub}:{cls_name}"] = fields

    # ── 收集文档 ──────────────────────────────────────────────────────

    def collect_docs(self, scope: str | None = None):
        if not self.docs_dir.exists():
            return
        for md_file in sorted(self.docs_dir.glob("*.md")):
            op_id = md_file.stem
            if scope and scope != "all":
                if not op_id.startswith(scope):
                    continue
            content = md_file.read_text(encoding="utf-8")
            params_info = self._extract_doc_params_detailed(content)
            self.docs[op_id] = {
                "filepath": str(md_file.relative_to(self.project_dir)),
                "title": self._md_title(content),
                "params": params_info["all_params"],
                "path_params": params_info["path_params"],
                "query_params": params_info["query_params"],
                "body_params": params_info["body_params"],
            }

    @staticmethod
    def _md_title(content: str) -> str:
        m = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        return m.group(1).strip() if m else ""

    @staticmethod
    def _extract_doc_params(content: str) -> list[str]:
        """从文档的参数表格中提取参数名（兼容旧接口）"""
        params = []
        for line in content.splitlines():
            m = re.match(r"^\|\s*`?(\w+)`?\s*\|", line)
            if m and m.group(1) not in ("参数名称", "参数名", "Field", "字段", "Name", "Parameter"):
                params.append(m.group(1))
        return params

    @staticmethod
    def _extract_doc_params_detailed(content: str) -> dict[str, list[str]]:
        """
        从文档中提取分类的参数名。
        支持检测 '#### 路径参数', '#### query 参数', '#### 请求参数' 等区域。
        """
        all_params: list[str] = []
        path_params: list[str] = []
        query_params: list[str] = []
        body_params: list[str] = []

        current_section = "unknown"
        header_patterns = {
            "path": re.compile(r"^#{1,5}\s*(路径参数|Path\s*Parameters?)", re.IGNORECASE),
            "query": re.compile(r"^#{1,5}\s*(query\s*参数|查询参数|Query\s*Parameters?|输入参数)", re.IGNORECASE),
            "body": re.compile(r"^#{1,5}\s*(请求参数|Body|Request\s*Body|请求体)", re.IGNORECASE),
        }
        # 响应相关的标题，遇到后停止提取输入参数
        response_pattern = re.compile(r"^#{1,5}\s*(响应|Response|返回|输出)", re.IGNORECASE)
        table_header_words = {"参数名称", "参数名", "Field", "字段", "Name", "Parameter"}

        in_table = False
        for line in content.splitlines():
            # 检查是否进入了新的参数段
            for section_name, pattern in header_patterns.items():
                if pattern.match(line.strip()):
                    current_section = section_name
                    in_table = False
                    break

            # 遇到响应段，停止提取
            if response_pattern.match(line.strip()):
                current_section = "response"
                in_table = False
                continue

            if current_section == "response":
                continue

            # 检测表格行
            m = re.match(r"^\|\s*`?(\w+)`?\s*\|", line)
            if m:
                name = m.group(1)
                if name in table_header_words:
                    in_table = True
                    continue
                if in_table:
                    all_params.append(name)
                    if current_section == "path":
                        path_params.append(name)
                    elif current_section == "query":
                        query_params.append(name)
                    elif current_section == "body":
                        body_params.append(name)
                    else:
                        # 未归类的参数，放到 body_params（大部分是请求参数）
                        body_params.append(name)
            # 非表格行，重置表格状态
            elif line.strip() and not line.strip().startswith("|"):
                in_table = False

        return {
            "all_params": all_params,
            "path_params": path_params,
            "query_params": query_params,
            "body_params": body_params,
        }

    # ── 路径匹配 ──────────────────────────────────────────────────────

    def _match_yaml_to_code(self) -> dict[str, str | None]:
        """
        尝试将每个 YAML API (operationId) 匹配到代码路由。
        返回 {operationId: code_norm_path | None}
        """
        matches = {}
        for op_id, yapi in self.yaml_apis.items():
            yaml_norm = yapi["norm_path"]
            # 将 YAML 路径中的参数名转为 正则
            # e.g., /api/v2/open/gateways/{gateway_name}/ → /api/v2/open/gateways/\{[^}]+\}/
            pattern = re.sub(r"\{[^}]+\}", r"{[^}]+}", re.escape(yaml_norm))
            pattern = pattern.replace(r"\{", "{").replace(r"\}", "}")

            best_match = None
            for code_path in self.code_routes:
                # 直接精确匹配
                if self._paths_equivalent(yaml_norm, code_path):
                    best_match = code_path
                    break

            matches[op_id] = best_match
        return matches

    @staticmethod
    def _paths_equivalent(yaml_path: str, code_path: str) -> bool:
        """比较两个路径是否等价（忽略参数名差异）"""
        y_parts = [p for p in yaml_path.strip("/").split("/")]
        c_parts = [p for p in code_path.strip("/").split("/")]

        if len(y_parts) != len(c_parts):
            return False

        for yp, cp in zip(y_parts, c_parts):
            y_is_param = yp.startswith("{") and yp.endswith("}")
            c_is_param = cp.startswith("{") and cp.endswith("}")

            if y_is_param and c_is_param:
                continue  # 都是参数，认为等价
            if y_is_param != c_is_param:
                return False  # 一个是参数一个不是
            if yp != cp:
                return False
        return True

    @staticmethod
    def _get_yaml_param_names(yapi: dict) -> dict[str, list[str]]:
        """
        从 YAML API 信息中提取分类的参数名。
        返回: {"path": [...], "query": [...], "body": [...]}
        """
        path_params = []
        query_params = []
        body_params = []

        # parameters (path + query)
        for p in yapi.get("parameters", []):
            name = p.get("name", "")
            location = p.get("in", "")
            if location == "path":
                path_params.append(name)
            elif location == "query":
                query_params.append(name)

        # requestBody properties
        rb = yapi.get("request_body", {})
        if rb:
            content = rb.get("content", {})
            for content_type, detail in content.items():
                schema = detail.get("schema", {})
                props = schema.get("properties", {})
                for prop_name in props:
                    body_params.append(prop_name)

        return {"path": path_params, "query": query_params, "body": body_params}

    # ── 执行检查 ──────────────────────────────────────────────────────

    def run_checks(self):
        # 建立 YAML → 代码路由 的匹配
        yaml_to_code = self._match_yaml_to_code()
        matched_code_paths = set(v for v in yaml_to_code.values() if v)

        for op_id, yapi in self.yaml_apis.items():
            if op_id in self.KNOWN_SPECIAL_CASES:
                self.skipped.append({"operation_id": op_id, "reason": "已知特殊 case"})
                continue

            backend_name = yapi.get("backend_name", "default")
            tags = set(yapi.get("tags", []))
            is_public = yapi.get("is_public", False)
            is_skip_backend = backend_name in self.SKIP_BACKENDS
            has_doc = op_id in self.docs

            code_path = yaml_to_code.get(op_id)
            has_code = code_path is not None

            # CHECK-1: 存在性 — YAML 有定义但代码无对应
            if not has_code and not is_skip_backend:
                self._log(
                    "error",
                    "CHECK-1",
                    op_id,
                    f"YAML 有定义但代码无对应路由: {yapi['path']}",
                    "添加路由或从 resources.yaml 移除该资源",
                )

            # CHECK-1: 存在性 — 缺文档
            if not has_doc and ".well-known" not in yapi.get("path", ""):
                self._log(
                    "warning",
                    "CHECK-1",
                    op_id,
                    f"YAML 有定义但无文档: {yapi['path']}",
                    f"创建 {self.docs_dir.name}/{op_id}.md",
                )

            # CHECK-2: 路径一致性（backend_path vs 实际路径）
            if has_code and not is_skip_backend:
                backend_path = yapi.get("backend_path", "")
                code_route = self.code_routes[code_path]
                if backend_path:
                    # backend.path 通常有 /backend/ 前缀，去掉后应与代码路由一致
                    bp_clean = re.sub(r"^/backend/", "/", backend_path)
                    bp_norm = normalize_path(bp_clean).rstrip("/") + "/"
                    code_norm = normalize_path(code_route["full_path"]).rstrip("/") + "/"
                    if not self._paths_equivalent(bp_norm, code_norm):
                        self._log(
                            "warning",
                            "CHECK-2",
                            op_id,
                            f"backend.path '{backend_path}' (去掉 /backend/ 后) 与代码路由 '{code_route['full_path']}' 不一致",
                            "确认 backend 转发路径是否正确",
                        )

            # CHECK-3: HTTP 方法一致性
            if has_code and not is_skip_backend:
                code_route = self.code_routes[code_path]
                view_class = code_route.get("view_class", "")
                scope_dir = code_route.get("scope_dir", "")
                scoped_view = f"{scope_dir}:{view_class}" if scope_dir else view_class
                code_methods = self.view_methods.get(scoped_view, [])
                yaml_method = yapi.get("method", "")

                if code_methods and yaml_method and yaml_method not in code_methods:
                    self._log(
                        "error",
                        "CHECK-3",
                        op_id,
                        f"YAML method={yaml_method} 但 View {view_class} 仅支持 {code_methods}",
                        "检查 View 类是否实现了该方法",
                    )

                backend_method = yapi.get("backend_method", "")
                if backend_method and yaml_method and backend_method != yaml_method:
                    self._log(
                        "warning",
                        "CHECK-3",
                        op_id,
                        f"backend.method={backend_method} 与前端 method={yaml_method} 不一致",
                        "通常应一致，确认是否有意转换",
                    )

            # CHECK-6: 鉴权配置
            if "inner" in tags and is_public:
                self._log("error", "CHECK-6", op_id, "inner API 不应为 isPublic: true", "将 isPublic 设为 false")

            # ── CHECK-4: YAML 参数 ↔ 文档参数 ────────────────────────────
            if has_doc:
                yaml_params = self._get_yaml_param_names(yapi)
                doc_info = self.docs[op_id]
                doc_all = set(doc_info.get("params", []))
                doc_path_params = set(doc_info.get("path_params", []))

                # 4a-path: 路径参数一致性检查（YAML path params vs 文档路径参数）
                yaml_path_set = set(yaml_params["path"])
                missing_path_in_doc = yaml_path_set - doc_path_params
                extra_path_in_doc = doc_path_params - yaml_path_set
                if missing_path_in_doc:
                    self._log(
                        "warning",
                        "CHECK-4",
                        op_id,
                        f"YAML 定义了路径参数但文档「路径参数」中缺少: {sorted(missing_path_in_doc)}",
                        f"在 {op_id}.md 的「路径参数」表格中补充",
                    )
                if extra_path_in_doc:
                    self._log(
                        "warning",
                        "CHECK-4",
                        op_id,
                        f"文档「路径参数」中有但 YAML 未定义: {sorted(extra_path_in_doc)}",
                        "确认是否需要在 resources.yaml 补充路径参数定义，或从文档中移除",
                    )

                # 4a: YAML 有但文档缺少的参数（query + body）
                yaml_all = set(yaml_params["query"]) | set(yaml_params["body"])
                missing_in_doc = yaml_all - doc_all
                if missing_in_doc:
                    self._log(
                        "warning",
                        "CHECK-4",
                        op_id,
                        f"YAML 定义了参数但文档中缺少: {sorted(missing_in_doc)}",
                        f"在 {op_id}.md 补充缺失的参数说明",
                    )

                # 4b: 文档有但 YAML 没有的参数（排除路径参数）
                yaml_path_params = set(yaml_params["path"])
                extra_in_doc = doc_all - yaml_all - yaml_path_params
                if extra_in_doc:
                    self._log(
                        "warning",
                        "CHECK-4",
                        op_id,
                        f"文档描述了参数但 YAML 中未定义: {sorted(extra_in_doc)}",
                        "确认是否需要在 resources.yaml 补充参数定义，或从文档中移除多余参数",
                    )

            # ── CHECK-5: YAML/文档参数 ↔ Serializer 字段 ─────────────────
            if has_code and not is_skip_backend:
                code_route = self.code_routes[code_path]
                view_class = code_route.get("view_class", "")
                scope_dir = code_route.get("scope_dir", "")
                scoped_view = f"{scope_dir}:{view_class}" if scope_dir else view_class
                slz_info = self.view_serializer_map.get(scoped_view, {})

                # 确定输入 Serializer
                # 优先使用显式的 input_slz；fallback 到 serializer_class 时，
                # 如果名称含 "Output" 则说明是输出序列化器，不应作为输入参数来检查
                input_slz_name = slz_info.get("input_slz", "")
                if not input_slz_name:
                    fallback = slz_info.get("serializer_class", "")
                    if fallback and "Output" not in fallback:
                        input_slz_name = fallback
                # 查找 serializer_fields 时也用 scope_dir 前缀
                scoped_slz = f"{scope_dir}:{input_slz_name}" if scope_dir and input_slz_name else input_slz_name
                if input_slz_name and scoped_slz in self.serializer_fields:
                    slz_fields = self.serializer_fields[scoped_slz]
                    # 只看输入字段（排除 output_only）
                    slz_input_names = set(f["name"] for f in slz_fields if not f.get("output_only", False))

                    yaml_params = self._get_yaml_param_names(yapi)
                    yaml_non_path = set(yaml_params["query"]) | set(yaml_params["body"])

                    # 分页参数由 DRF 分页器自动处理（如 paginate_queryset / get_paginated_response），
                    # 不需要在 Serializer 中声明，比较时应排除
                    pagination_params = self.PAGINATION_PARAMS

                    # 5a: Serializer 有但 YAML 没有的字段
                    missing_in_yaml = slz_input_names - yaml_non_path - pagination_params
                    if missing_in_yaml:
                        self._log(
                            "warning",
                            "CHECK-5",
                            op_id,
                            f"Serializer '{input_slz_name}' 定义了字段但 YAML 中缺少: {sorted(missing_in_yaml)}",
                            "在 resources.yaml 的 parameters/requestBody 中补充这些字段",
                        )

                    # 5b: YAML 有但 Serializer 没有的字段
                    extra_in_yaml = yaml_non_path - slz_input_names - pagination_params
                    if extra_in_yaml:
                        self._log(
                            "warning",
                            "CHECK-5",
                            op_id,
                            f"YAML 定义了参数但 Serializer '{input_slz_name}' 中没有: {sorted(extra_in_yaml)}",
                            "确认 YAML 参数是否过时，或 Serializer 是否缺少字段定义",
                        )

        # 反向检查：代码中有但 YAML 没有
        for code_path, code_route in self.code_routes.items():
            if code_path not in matched_code_paths:
                self._log(
                    "warning",
                    "CHECK-1-REV",
                    code_route.get("view_class", "unknown"),
                    f"代码有路由但 YAML 无匹配定义: {code_route['full_path']}",
                    "在 bk-apigateway-resources.yaml 补充资源定义，或确认路径是否变更",
                )

        # 反向检查：文档存在但 YAML 没有
        # 使用完整的 operationId 集合（包含 v1 等被 scope 过滤掉的 API），避免误报
        all_op_ids = self._collect_all_operation_ids()
        for op_id, doc in self.docs.items():
            if op_id not in self.yaml_apis and op_id not in all_op_ids:
                self._log(
                    "warning",
                    "CHECK-1-REV",
                    op_id,
                    f"文档存在但 YAML 无定义: {doc['filepath']}",
                    "确认是否为废弃文档，或补充资源定义",
                )

    def _collect_all_operation_ids(self) -> set[str]:
        """从完整的 resources YAML 中收集所有 operationId（不受 scope 过滤）"""
        if not self.resources_yaml.exists():
            return set()
        with open(self.resources_yaml, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        all_ids = set()
        for path_str, methods in data.get("paths", {}).items():
            for method, detail in methods.items():
                if method in ("parameters", "summary", "description"):
                    continue
                op_id = detail.get("operationId", "")
                if op_id:
                    all_ids.add(op_id)
        return all_ids

    def check_definition(self):
        """检查 definition.yaml 的 grant_permissions 和 mcp_servers"""
        if not self.definition_yaml.exists():
            return
        raw = self.definition_yaml.read_text(encoding="utf-8")
        # 替换 Jinja2 / Django 模板变量 {{ ... }} 为占位字符串
        raw = re.sub(r'"(\{\{.*?\}\})"', '"__TEMPLATE_VAR__"', raw)
        raw = re.sub(r"\{\{.*?\}\}", "__TEMPLATE_VAR__", raw)
        definition = yaml.safe_load(raw)

        # 使用完整的 operationId 集合（不受 scope 过滤），避免跨 scope 引用导致误报
        all_op_ids = self._collect_all_operation_ids()

        # CHECK-7: grant_permissions
        for item in definition.get("grant_permissions", []):
            for res_name in item.get("resource_names", []):
                if res_name not in all_op_ids:
                    self._log(
                        "error",
                        "CHECK-7",
                        res_name,
                        f"grant_permissions 授权了不存在的资源: {res_name}",
                        "移除授权或添加资源定义",
                    )

        # CHECK-8: mcp_servers
        for stage in definition.get("stages", []):
            mcp_servers = stage.get("mcp_servers", [])
            if isinstance(mcp_servers, dict):
                mcp_servers = [{"name": k, **v} for k, v in mcp_servers.items()]
            for srv_conf in mcp_servers:
                srv_name = srv_conf.get("name", "unknown")
                res_names = srv_conf.get("resource_names", [])
                tool_names = srv_conf.get("tool_names", [])
                for rn in res_names:
                    if rn not in all_op_ids:
                        self._log(
                            "error",
                            "CHECK-8",
                            rn,
                            f"mcp_servers '{srv_name}' 引用不存在的资源: {rn}",
                            "补充资源定义或修正 mcp_servers 配置",
                        )
                if len(res_names) != len(tool_names):
                    self._log(
                        "warning",
                        "CHECK-8",
                        srv_name,
                        f"resource_names({len(res_names)}) 与 tool_names({len(tool_names)}) 数量不匹配",
                        "检查配置是否一一对应",
                    )

    # ── JSON 输出 ─────────────────────────────────────────────────────

    def to_json(self) -> dict:
        total = len(self.yaml_apis)
        issue_ids = set(e["operation_id"] for e in self.errors) | set(w["operation_id"] for w in self.warnings)
        skip_ids = {s["operation_id"] for s in self.skipped}
        passed = [oid for oid in self.yaml_apis if oid not in issue_ids and oid not in skip_ids]
        return {
            "summary": {
                "total_yaml_apis": total,
                "total_code_routes": len(self.code_routes),
                "total_docs": len(self.docs),
                "passed": len(passed),
                "errors": len(self.errors),
                "warnings": len(self.warnings),
                "skipped": len(self.skipped),
            },
            "errors": self.errors,
            "warnings": self.warnings,
            "skipped": self.skipped,
            "passed": sorted(passed),
        }

    # ── 彩色报告 ──────────────────────────────────────────────────────

    def print_report(self):
        if self.json_output:
            print(json.dumps(self.to_json(), ensure_ascii=False, indent=2))
            return

        total = len(self.yaml_apis)
        issue_ids = set(e["operation_id"] for e in self.errors) | set(w["operation_id"] for w in self.warnings)
        skip_ids = {s["operation_id"] for s in self.skipped}
        passed = [oid for oid in self.yaml_apis if oid not in issue_ids and oid not in skip_ids]

        print(c("=" * 60, CYAN))
        print(c("🔍 API 一致性检查报告", BOLD + CYAN))
        print(c("=" * 60, CYAN))
        print()
        print(c("📊 摘要", BOLD))
        print(f"   YAML API: {total} 个")
        print(f"   代码路由: {len(self.code_routes)} 个")
        print(f"   API 文档: {len(self.docs)} 个")
        print(f"   {c('✅ 通过', GREEN)}: {len(passed)}")
        print(f"   {c('❌ 错误', RED)}: {len(self.errors)}")
        print(f"   {c('⚠️  警告', YELLOW)}: {len(self.warnings)}")
        if self.skipped:
            print(f"   {c('⏭️  跳过', DIM)}: {len(self.skipped)}")
        print()

        if self.errors:
            print(c("━" * 60, RED))
            print(c("❌ 错误列表", BOLD + RED))
            print(c("━" * 60, RED))
            for i, e in enumerate(self.errors, 1):
                print(f"  {c(f'[{i}]', RED)} [{e['check']}] {c(e['operation_id'], BOLD)}")
                print(f"      {e['message']}")
                if e["suggestion"]:
                    print(f"      {c('💡', CYAN)} {e['suggestion']}")
            print()

        if self.warnings:
            print(c("━" * 60, YELLOW))
            print(c("⚠️  警告列表", BOLD + YELLOW))
            print(c("━" * 60, YELLOW))
            for i, w in enumerate(self.warnings, 1):
                print(f"  {c(f'[{i}]', YELLOW)} [{w['check']}] {c(w['operation_id'], BOLD)}")
                print(f"      {w['message']}")
                if w["suggestion"]:
                    print(f"      {c('💡', CYAN)} {w['suggestion']}")
            print()

        if passed:
            print(c("━" * 60, GREEN))
            print(c("✅ 通过的 API", BOLD + GREEN))
            print(c("━" * 60, GREEN))
            for oid in sorted(passed):
                print(f"   {c('✅', GREEN)} {oid}")
            print()

        if self.skipped:
            print(c("━" * 60, DIM))
            print(c("⏭️  跳过的 API（已知特殊 case）", DIM))
            for s in self.skipped:
                print(f"   {c('⏭️', DIM)} {s['operation_id']} — {s['reason']}")
            print()

        print(c("=" * 60, CYAN))

    # ── 自动修复 ──────────────────────────────────────────────────────

    def run_fix(self):
        fixed = 0
        for op_id, yapi in self.yaml_apis.items():
            if op_id in self.docs or op_id in self.KNOWN_SPECIAL_CASES:
                continue
            if ".well-known" in yapi.get("path", ""):
                continue

            doc_path = self.docs_dir / f"{op_id}.md"
            doc_path.write_text(self._doc_template(op_id, yapi), encoding="utf-8")
            print(c(f"✅ 已生成: {doc_path}", GREEN))
            fixed += 1

        if fixed:
            print(c(f"共生成 {fixed} 个文档模板，请人工补充详细内容。", GREEN))
        else:
            print(c("没有需要生成的缺失文档。", CYAN))

    def _doc_template(self, op_id: str, yapi: dict) -> str:
        path = yapi.get("path", "")
        method = yapi.get("method", "")
        desc = yapi.get("description", "")
        params = yapi.get("parameters", [])

        rows = []
        for p in params:
            name = p.get("name", "")
            ptype = p.get("schema", {}).get("type", "string")
            req = "是" if p.get("required") else "否"
            pdesc = p.get("description", "")
            rows.append(f"| {name} | {ptype} | {req} | {pdesc} |")
        param_table = "\n".join(rows) if rows else "| (无) | | | |"

        return f"""# {desc or op_id}

## 接口说明

{desc or "TODO: 补充接口描述"}

## 请求信息

- 请求方法: {method}
- 请求路径: {path}

## 路径参数

| 参数名称 | 参数类型 | 必须 | 参数说明 |
|----------|----------|------|----------|
{param_table}

## 请求参数

TODO: 补充请求参数说明

## 请求示例

TODO: 补充请求示例

## 响应示例

TODO: 补充响应示例

## 响应参数说明

TODO: 补充响应参数说明

---

> ⚠️ 本文档由 `check_api_consistency.py --fix` 自动生成，请人工补充完善内容。
"""

    # ── 主流程 ────────────────────────────────────────────────────────

    def run(self, scope: str, fix: bool = False, target_api: str | None = None):
        if not self.json_output:
            print(c(f"🔍 API 一致性检查 — 范围: {scope}" + (f" — API: {target_api}" if target_api else ""), CYAN))
            print(c(f"📁 项目: {self.project_dir}", CYAN))
            print()

        self.collect_yaml(scope, target_api)
        self.collect_code(scope)
        self.collect_docs(scope)
        self.run_checks()
        self.check_definition()

        if fix:
            self.run_fix()
            if not self.json_output:
                print()

        self.print_report()
        return 1 if self.errors else 0


def find_project_dir() -> str:
    cwd = Path.cwd()
    if (cwd / "src" / "dashboard" / "apigateway").exists():
        return str(cwd)
    for p in cwd.parents:
        if (p / "src" / "dashboard" / "apigateway").exists():
            return str(p)
    script_dir = Path(__file__).resolve().parent
    candidate = script_dir / ".." / ".." / ".."
    if (candidate / "src" / "dashboard" / "apigateway").exists():
        return str(candidate.resolve())
    return str(cwd)


def main():
    parser = argparse.ArgumentParser(
        description="API 一致性检查工具 — 检查 API 代码、YAML 网关定义、文档三者一致性",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例:
  %(prog)s                              # 检查所有 v2 API
  %(prog)s --scope v2_sync              # 只检查 v2 sync API
  %(prog)s --api v2_sync_stages         # 检查单个 API
  %(prog)s --json                       # JSON 格式输出
  %(prog)s --fix                        # 生成缺失的文档模板
  %(prog)s --scope v2_open --fix        # 检查 v2 open 并修复缺失文档
""",
    )
    parser.add_argument(
        "--scope", default="all", choices=["all", "v2_open", "v2_inner", "v2_sync"], help="检查范围 (默认: all)"
    )
    parser.add_argument("--api", default=None, help="指定 operationId 检查单个 API（与 --scope 互斥）")
    parser.add_argument("--fix", action="store_true", help="自动生成缺失的 API 文档模板")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出（机器可读）")
    parser.add_argument("--project-dir", default=None, help="项目根目录 (默认自动探测)")
    args = parser.parse_args()

    # 参数互斥检测
    if args.api and args.scope != "all":
        parser.error("--api 和 --scope 不能同时使用，指定 --api 时会自动确定 scope")

    project_dir = args.project_dir or find_project_dir()

    # 验证项目目录
    expected = Path(project_dir) / "src" / "dashboard" / "apigateway"
    if not expected.exists():
        print(c(f"错误: 项目目录 '{project_dir}' 中未找到 src/dashboard/apigateway", RED), file=sys.stderr)
        print(c("请使用 --project-dir 指定正确的项目根目录", YELLOW), file=sys.stderr)
        sys.exit(2)

    checker = APIConsistencyChecker(project_dir, json_output=args.json)
    sys.exit(checker.run(args.scope, fix=args.fix, target_api=args.api))


if __name__ == "__main__":
    main()
