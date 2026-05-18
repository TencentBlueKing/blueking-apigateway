#!/usr/bin/env python3
"""
单元测试: check_api_consistency.py 的核心解析和检查逻辑
"""
import sys
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

# 将脚本目录加入 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from check_api_consistency import (
    APIConsistencyChecker,
    normalize_path,
    parse_django_urls,
    parse_serializer_fields,
    parse_view_methods,
    parse_view_serializers,
)


# ── normalize_path ────────────────────────────────────────────────────


class TestNormalizePath:
    def test_django_type_param(self):
        assert normalize_path("<slug:gateway_name>/") == "{gateway_name}/"

    def test_django_int_param(self):
        assert normalize_path("<int:record_id>/") == "{record_id}/"

    def test_django_str_param(self):
        assert normalize_path("<str:resource_name>/") == "{resource_name}/"

    def test_no_type_prefix(self):
        assert normalize_path("<gateway_name>/") == "{gateway_name}/"

    def test_multiple_params(self):
        result = normalize_path("gateways/<slug:name>/resources/<int:id>/")
        assert result == "gateways/{name}/resources/{id}/"

    def test_trailing_slash_added(self):
        assert normalize_path("gateways") == "gateways/"

    def test_already_has_trailing_slash(self):
        assert normalize_path("gateways/") == "gateways/"

    def test_empty_string(self):
        assert normalize_path("") == ""


# ── parse_django_urls（AST 解析）───────────────────────────────────


class TestParseDjangoUrls:
    def test_simple_path(self, tmp_path):
        urls_py = tmp_path / "urls.py"
        urls_py.write_text(textwrap.dedent("""\
            from django.urls import path
            from . import views

            urlpatterns = [
                path("gateways/", views.GatewayListApi.as_view(), name="gateway.list"),
            ]
        """))
        routes = parse_django_urls(urls_py, prefix="/api/v2/open/")
        assert len(routes) == 1
        assert routes[0]["full_path"] == "/api/v2/open/gateways/"
        assert routes[0]["view_class"] == "GatewayListApi"
        assert routes[0]["name"] == "gateway.list"

    def test_nested_include(self, tmp_path):
        urls_py = tmp_path / "urls.py"
        urls_py.write_text(textwrap.dedent("""\
            from django.urls import include, path
            from . import views

            urlpatterns = [
                path("gateways/", include([
                    path("", views.GatewayListApi.as_view(), name="list"),
                    path("<slug:name>/", include([
                        path("", views.GatewayDetailApi.as_view(), name="detail"),
                        path("resources/", views.ResourceListApi.as_view(), name="resources"),
                    ])),
                ])),
            ]
        """))
        routes = parse_django_urls(urls_py, prefix="/api/v2/open/")
        assert len(routes) == 3
        paths = {r["full_path"]: r["view_class"] for r in routes}
        assert paths["/api/v2/open/gateways/"] == "GatewayListApi"
        assert paths["/api/v2/open/gateways/<slug:name>/"] == "GatewayDetailApi"
        assert paths["/api/v2/open/gateways/<slug:name>/resources/"] == "ResourceListApi"

    def test_augmented_assign(self, tmp_path):
        """urlpatterns += [...] 形式也应被解析"""
        urls_py = tmp_path / "urls.py"
        urls_py.write_text(textwrap.dedent("""\
            from django.urls import path
            from . import views

            urlpatterns = [
                path("a/", views.AApi.as_view(), name="a"),
            ]
            urlpatterns += [
                path("b/", views.BApi.as_view(), name="b"),
            ]
        """))
        routes = parse_django_urls(urls_py, prefix="/api/")
        assert len(routes) == 2
        classes = {r["view_class"] for r in routes}
        assert classes == {"AApi", "BApi"}

    def test_conditional_urlpatterns(self, tmp_path):
        """if 条件中的 urlpatterns += [...] 也应被解析"""
        urls_py = tmp_path / "urls.py"
        urls_py.write_text(textwrap.dedent("""\
            from django.urls import include, path
            from . import views

            urlpatterns = [
                path("a/", views.AApi.as_view(), name="a"),
            ]
            if True:
                urlpatterns += [
                    path("b/", views.BApi.as_view(), name="b"),
                ]
        """))
        routes = parse_django_urls(urls_py, prefix="/api/")
        assert len(routes) == 2

    def test_no_view_skipped(self, tmp_path):
        """没有 .as_view() 的 path 应该被跳过"""
        urls_py = tmp_path / "urls.py"
        urls_py.write_text(textwrap.dedent("""\
            from django.urls import path

            urlpatterns = [
                path("static/", lambda r: None),
            ]
        """))
        routes = parse_django_urls(urls_py, prefix="/api/")
        assert len(routes) == 0


# ── parse_view_methods ────────────────────────────────────────────


class TestParseViewMethods:
    def test_basic_methods(self, tmp_path):
        views_py = tmp_path / "views.py"
        views_py.write_text(textwrap.dedent("""\
            class GatewayListApi:
                def get(self, request):
                    pass
                def post(self, request):
                    pass
        """))
        result = parse_view_methods(views_py)
        assert "GatewayListApi" in result
        assert set(result["GatewayListApi"]) == {"GET", "POST"}

    def test_drf_methods(self, tmp_path):
        views_py = tmp_path / "views.py"
        views_py.write_text(textwrap.dedent("""\
            class GatewayRetrieveDestroyApi:
                def retrieve(self, request):
                    pass
                def destroy(self, request):
                    pass
        """))
        result = parse_view_methods(views_py)
        methods = set(result["GatewayRetrieveDestroyApi"])
        assert "GET" in methods  # retrieve → GET
        assert "DELETE" in methods  # destroy → DELETE

    def test_partial_update(self, tmp_path):
        views_py = tmp_path / "views.py"
        views_py.write_text(textwrap.dedent("""\
            class UpdateApi:
                def partial_update(self, request):
                    pass
        """))
        result = parse_view_methods(views_py)
        assert "PATCH" in result["UpdateApi"]

    def test_multiple_classes(self, tmp_path):
        views_py = tmp_path / "views.py"
        views_py.write_text(textwrap.dedent("""\
            class AApi:
                def get(self, request):
                    pass

            class BApi:
                def post(self, request):
                    pass
        """))
        result = parse_view_methods(views_py)
        assert set(result["AApi"]) == {"GET"}
        assert set(result["BApi"]) == {"POST"}


# ── parse_view_serializers ────────────────────────────────────────


class TestParseViewSerializers:
    def test_serializer_class(self, tmp_path):
        views_py = tmp_path / "views.py"
        views_py.write_text(textwrap.dedent("""\
            class GatewayListApi:
                serializer_class = serializers.GatewayListSLZ
                def get(self, request):
                    pass
        """))
        result = parse_view_serializers(views_py)
        assert result["GatewayListApi"]["serializer_class"] == "GatewayListSLZ"

    def test_input_slz(self, tmp_path):
        views_py = tmp_path / "views.py"
        views_py.write_text(textwrap.dedent("""\
            class GatewaySyncApi:
                def post(self, request):
                    slz = serializers.GatewaySyncInputSLZ(data=request.data)
        """))
        result = parse_view_serializers(views_py)
        assert result["GatewaySyncApi"]["input_slz"] == "GatewaySyncInputSLZ"


# ── parse_serializer_fields ──────────────────────────────────────


class TestParseSerializerFields:
    def test_basic_fields(self, tmp_path):
        slz_py = tmp_path / "serializers.py"
        slz_py.write_text(textwrap.dedent("""\
            from rest_framework import serializers

            class GatewayInputSLZ(serializers.Serializer):
                name = serializers.CharField()
                description = serializers.CharField(required=False)
                is_active = serializers.BooleanField()
        """))
        result = parse_serializer_fields(slz_py)
        assert "GatewayInputSLZ" in result
        fields = {f["name"]: f for f in result["GatewayInputSLZ"]}
        assert fields["name"]["required"] is True
        assert fields["description"]["required"] is False
        assert fields["is_active"]["type"] == "BooleanField"

    def test_hidden_field_excluded(self, tmp_path):
        slz_py = tmp_path / "serializers.py"
        slz_py.write_text(textwrap.dedent("""\
            from rest_framework import serializers

            class GatewayInputSLZ(serializers.Serializer):
                gateway = serializers.HiddenField(default=CurrentGatewayDefault())
                name = serializers.CharField()
        """))
        result = parse_serializer_fields(slz_py)
        field_names = [f["name"] for f in result["GatewayInputSLZ"]]
        assert "gateway" not in field_names
        assert "name" in field_names

    def test_serializer_method_field_output_only(self, tmp_path):
        slz_py = tmp_path / "serializers.py"
        slz_py.write_text(textwrap.dedent("""\
            from rest_framework import serializers

            class GatewayOutputSLZ(serializers.Serializer):
                name = serializers.CharField()
                extra = serializers.SerializerMethodField()
        """))
        result = parse_serializer_fields(slz_py)
        fields = {f["name"]: f for f in result["GatewayOutputSLZ"]}
        assert fields["extra"]["output_only"] is True

    def test_read_only_field(self, tmp_path):
        slz_py = tmp_path / "serializers.py"
        slz_py.write_text(textwrap.dedent("""\
            from rest_framework import serializers

            class SomeSLZ(serializers.Serializer):
                id = serializers.IntegerField(read_only=True)
                name = serializers.CharField()
        """))
        result = parse_serializer_fields(slz_py)
        fields = {f["name"]: f for f in result["SomeSLZ"]}
        assert fields["id"]["output_only"] is True
        assert fields["name"]["output_only"] is False

    def test_inheritance(self, tmp_path):
        """子类应该继承基类中定义的字段"""
        slz_py = tmp_path / "serializers.py"
        slz_py.write_text(textwrap.dedent("""\
            from rest_framework import serializers

            class BaseSLZ(serializers.Serializer):
                keyword = serializers.CharField(required=False)
                order_by = serializers.CharField(required=False)

            class GatewayListInputSLZ(BaseSLZ):
                name = serializers.CharField(required=False)
        """))
        result = parse_serializer_fields(slz_py)
        child_field_names = {f["name"] for f in result["GatewayListInputSLZ"]}
        assert "name" in child_field_names
        assert "keyword" in child_field_names  # 从 BaseSLZ 继承
        assert "order_by" in child_field_names  # 从 BaseSLZ 继承

    def test_meta_fields(self, tmp_path):
        slz_py = tmp_path / "serializers.py"
        slz_py.write_text(textwrap.dedent("""\
            from rest_framework import serializers

            class GatewayModelSLZ(serializers.ModelSerializer):
                class Meta:
                    fields = ["id", "name", "description"]
        """))
        result = parse_serializer_fields(slz_py)
        field_names = {f["name"] for f in result["GatewayModelSLZ"]}
        assert field_names == {"id", "name", "description"}


# ── APIConsistencyChecker 核心方法 ────────────────────────────────


class TestExtractDocParams:
    """测试文档参数提取"""

    def test_path_params(self):
        checker = APIConsistencyChecker.__new__(APIConsistencyChecker)
        content = """\
### 输入参数

#### 路径参数

| 参数名称     | 参数类型 | 必选 | 描述   |
|------------|----------|------|--------|
| gateway_name | string   | 是   | 网关名 |

#### 请求参数

| 参数名称 | 参数类型 | 必选 | 描述 |
|----------|----------|------|------|
| name     | string   | 是   | 名称 |
"""
        result = checker._extract_doc_params_detailed(content)
        assert "gateway_name" in result["path_params"]
        assert "name" in result["body_params"]
        assert "gateway_name" in result["all_params"]
        assert "name" in result["all_params"]

    def test_empty_path_params(self):
        checker = APIConsistencyChecker.__new__(APIConsistencyChecker)
        content = """\
### 输入参数

#### 路径参数



#### 请求参数

| 参数名称 | 参数类型 | 必选 | 描述 |
|----------|----------|------|------|
| name     | string   | 是   | 名称 |
"""
        result = checker._extract_doc_params_detailed(content)
        assert result["path_params"] == []
        assert "name" in result["body_params"]

    def test_response_section_stops_extraction(self):
        checker = APIConsistencyChecker.__new__(APIConsistencyChecker)
        content = """\
### 输入参数

#### 请求参数

| 参数名称 | 参数类型 | 必选 | 描述 |
|----------|----------|------|------|
| name     | string   | 是   | 名称 |

### 响应示例

| 字段 | 类型 | 描述 |
|------|------|------|
| id   | int  | ID   |
"""
        result = checker._extract_doc_params_detailed(content)
        assert "name" in result["all_params"]
        assert "id" not in result["all_params"]


class TestGetYamlParamNames:
    """测试 YAML 参数提取"""

    def test_path_and_query_params(self):
        checker = APIConsistencyChecker.__new__(APIConsistencyChecker)
        yapi = {
            "parameters": [
                {"name": "gateway_name", "in": "path"},
                {"name": "keyword", "in": "query"},
                {"name": "limit", "in": "query"},
            ],
            "request_body": {},
        }
        result = checker._get_yaml_param_names(yapi)
        assert result["path"] == ["gateway_name"]
        assert set(result["query"]) == {"keyword", "limit"}
        assert result["body"] == []

    def test_request_body_params(self):
        checker = APIConsistencyChecker.__new__(APIConsistencyChecker)
        yapi = {
            "parameters": [],
            "request_body": {
                "content": {
                    "application/json": {
                        "schema": {
                            "properties": {
                                "name": {"type": "string"},
                                "backends": {"type": "array"},
                            }
                        }
                    }
                }
            },
        }
        result = checker._get_yaml_param_names(yapi)
        assert set(result["body"]) == {"name", "backends"}


class TestPathsEquivalent:
    def test_exact_match(self):
        checker = APIConsistencyChecker.__new__(APIConsistencyChecker)
        assert checker._paths_equivalent("/api/v2/open/gateways/", "/api/v2/open/gateways/")

    def test_param_name_differs(self):
        """路径参数名不同但结构相同应该等价"""
        checker = APIConsistencyChecker.__new__(APIConsistencyChecker)
        assert checker._paths_equivalent(
            "/api/v2/open/gateways/{gateway_name}/",
            "/api/v2/open/gateways/{name}/"
        )


class TestColorDisabled:
    """测试非 TTY 时颜色禁用"""

    def test_c_function_no_color(self):
        from check_api_consistency import c
        # 当 color 为空字符串时应返回原文
        assert c("hello", "") == "hello"
