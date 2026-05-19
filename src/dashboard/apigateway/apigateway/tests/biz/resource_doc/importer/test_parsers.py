#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
#     http://opensource.org/licenses/MIT
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions and
# limitations under the License.
#
# We undertake not to change the open source license (MIT license) applicable
# to the current version of the project delivered to anyone in the future.
#
import pytest

from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.biz.resource_doc.exceptions import NoResourceDocError, UnsafeSwaggerRefError
from apigateway.biz.resource_doc.importer.models import ArchiveDoc
from apigateway.biz.resource_doc.importer.parsers import ArchiveParser, BaseParser, SwaggerParser
from apigateway.core.models import Resource


class TestBaseParser:
    def test_enrich_docs(self, fake_resource_doc, faker):
        fake_gateway = fake_resource_doc.gateway
        fake_resource = Resource.objects.get(id=fake_resource_doc.resource_id)
        parser = BaseParser(fake_gateway.id)

        docs = [
            ArchiveDoc(
                resource_name="no_exist",
                language=DocLanguageEnum.ZH,
                content=faker.pystr(),
            )
        ]
        parser._enrich_docs(docs)
        assert docs[0].resource is None
        assert docs[0].resource_doc is None
        assert docs[0].content_changed is True

        docs = [
            ArchiveDoc(
                resource_name=fake_resource.name,
                language=DocLanguageEnum.ZH,
                content="new content",
            )
        ]
        parser._enrich_docs(docs)
        assert docs[0].resource == fake_resource
        assert docs[0].resource_doc == fake_resource_doc
        assert docs[0].content_changed is True

        docs = [
            ArchiveDoc(
                resource_name=fake_resource.name,
                language=DocLanguageEnum.ZH,
                content=fake_resource_doc.content,
            )
        ]
        parser._enrich_docs(docs)
        assert docs[0].content_changed is False


class TestArchiveParser:
    @pytest.mark.parametrize(
        "files, expected",
        [
            (
                {
                    "zh/get_user.md": "/path/to/zh/get_user.md",
                    "en/get_user.md": "/path/to/en/get_user.md",
                    "zh/create_user.md.j2": "/path/to/zh/create_user.md.j2",
                    "zz/get_user.md": "/path/to/zz/get_user.md",
                    "zh/get_user.txt": "/path/to/zh/get_user.txt",
                },
                [
                    ArchiveDoc(
                        language=DocLanguageEnum("zh"),
                        resource_name="get_user",
                        filename="zh/get_user.md",
                        content="",
                    ),
                    ArchiveDoc(
                        language=DocLanguageEnum("en"),
                        resource_name="get_user",
                        filename="en/get_user.md",
                        content="",
                    ),
                    ArchiveDoc(
                        language=DocLanguageEnum("zh"),
                        resource_name="create_user",
                        filename="zh/create_user.md.j2",
                        content="",
                    ),
                ],
            )
        ],
    )
    def test_parse(self, mocker, files, expected):
        mocker.patch(
            "apigateway.biz.resource_doc.importer.parsers.Jinja2ToMarkdownGenerator.generate_doc_content",
            return_value="",
        )
        result = ArchiveParser(1)._parse(files)
        assert result == expected

    def test_parse__error(self):
        with pytest.raises(NoResourceDocError):
            ArchiveParser(1)._parse({})

    def test_filter_files(self):
        files = {
            "get_user.md": "",
            "en/get_user.md": "",
            "docs/en/get_user.md": "",
            "other/docs/en/get_user.md": "",
        }
        result = ArchiveParser(1)._filter_files(files)
        assert result == {
            "en/get_user.md": "",
            "docs/en/get_user.md": "",
        }

    @pytest.mark.parametrize(
        "filename, expected",
        [
            ("get_user.md", None),
            ("zh/get_user.md", "zh"),
            ("en/get_user.md", "en"),
            ("zz/get_user.md", None),
            ("docs/zh/get_user.md", "zh"),
            ("other/docs/zh/get_user.md", "zh"),
        ],
    )
    def test_extract_language(self, filename, expected):
        result = ArchiveParser(1)._extract_language(filename)
        assert result == expected

    @pytest.mark.parametrize(
        "filename, expected",
        [
            ("zh/get_user.md", "get_user"),
            ("en/get_user.md", "get_user"),
            ("zh/get_user.md.j2", "get_user"),
            ("zz/get_user.txt", None),
            ("docs/zh/get_user.md", "get_user"),
            ("other/docs/zh/get_user.md", "get_user"),
        ],
    )
    def test_extract_resource_name(self, filename, expected):
        result = ArchiveParser(1)._extract_resource_name(filename)
        assert result == expected


class TestSwagger:
    def test_parse(self, mocker):
        mocker.patch("apigateway.biz.resource_doc.importer.parsers.SwaggerParser._expand_swagger", return_value="")
        mocker.patch(
            "apigateway.biz.resource_doc.importer.parsers.SwaggerManager.load_from_swagger",
            return_value=mocker.MagicMock(
                **{
                    "validate.return_value": None,
                    "get_paths.return_value": {
                        "/user": {
                            "get": {
                                "operationId": "get_user",
                            }
                        }
                    },
                }
            ),
        )

        docs = SwaggerParser(1)._parse("swagger", DocLanguageEnum.ZH)
        assert docs[0].resource_name == "get_user"
        assert docs[0].language == DocLanguageEnum.ZH
        assert docs[0].content != ""
        assert docs[0].swagger != ""


class TestSwaggerParserValidateRefs:
    """测试 SwaggerParser._validate_refs 方法，确保拒绝外部 $ref 引用"""

    def test_valid_internal_ref_json(self):
        """内部引用（以 #/ 开头）应通过校验"""
        swagger = '{"paths": {"/user": {"get": {"responses": {"200": {"schema": {"$ref": "#/definitions/User"}}}}}}}'
        # 不应抛出异常
        SwaggerParser._validate_refs(swagger)

    def test_valid_internal_ref_yaml(self):
        """YAML 格式的内部引用应通过校验"""
        swagger = """
paths:
  /user:
    get:
      responses:
        "200":
          schema:
            $ref: "#/definitions/User"
"""
        SwaggerParser._validate_refs(swagger)

    def test_valid_no_refs(self):
        """没有 $ref 的 swagger 应通过校验"""
        swagger = '{"paths": {"/user": {"get": {"responses": {"200": {"description": "ok"}}}}}}'
        SwaggerParser._validate_refs(swagger)

    def test_reject_http_url_ref_json(self):
        """拒绝 HTTP URL 类型的 $ref（SSRF 风险）"""
        swagger = '{"paths": {"/user": {"get": {"responses": {"200": {"schema": {"$ref": "http://evil.com/payload.json"}}}}}}}'
        with pytest.raises(UnsafeSwaggerRefError):
            SwaggerParser._validate_refs(swagger)

    def test_reject_https_url_ref_json(self):
        """拒绝 HTTPS URL 类型的 $ref"""
        swagger = '{"paths": {"/user": {"get": {"responses": {"200": {"schema": {"$ref": "https://evil.com/payload.json"}}}}}}}'
        with pytest.raises(UnsafeSwaggerRefError):
            SwaggerParser._validate_refs(swagger)

    def test_reject_absolute_file_path_ref(self):
        """拒绝绝对文件路径类型的 $ref（本地文件读取风险）"""
        swagger = '{"paths": {"/user": {"get": {"responses": {"200": {"schema": {"$ref": "/etc/passwd"}}}}}}}'
        with pytest.raises(UnsafeSwaggerRefError):
            SwaggerParser._validate_refs(swagger)

    def test_reject_relative_file_path_ref(self):
        """拒绝相对文件路径类型的 $ref"""
        swagger = '{"paths": {"/user": {"get": {"responses": {"200": {"schema": {"$ref": "../secrets.json"}}}}}}}'
        with pytest.raises(UnsafeSwaggerRefError):
            SwaggerParser._validate_refs(swagger)

    def test_reject_http_ref_yaml(self):
        """YAML 格式中拒绝 HTTP URL 的 $ref"""
        swagger = """
paths:
  /user:
    get:
      responses:
        "200":
          schema:
            $ref: "http://internal-service.svc.cluster.local/api/secret"
"""
        with pytest.raises(UnsafeSwaggerRefError):
            SwaggerParser._validate_refs(swagger)

    def test_reject_nested_external_ref(self):
        """拒绝深层嵌套中的外部 $ref"""
        swagger = (
            '{"definitions": {"User": {"properties": {"address": {"$ref": "http://attacker.oastify.com/ex.json"}}}}}'
        )
        with pytest.raises(UnsafeSwaggerRefError):
            SwaggerParser._validate_refs(swagger)

    def test_mixed_refs_reject_if_any_external(self):
        """混合内部和外部 $ref 时，只要存在外部引用就应拒绝"""
        swagger = (
            '{"paths": {"/user": {"get": {"responses": {"200": {"schema": {"$ref": "#/definitions/User"}}}}}},'
            '"definitions": {"User": {"properties": {"evil": {"$ref": "http://evil.com/x"}}}}}'
        )
        with pytest.raises(UnsafeSwaggerRefError):
            SwaggerParser._validate_refs(swagger)

    def test_unparseable_content_rejected(self):
        """无法解析的内容应直接拒绝而非放行"""
        swagger = "this is not valid json or yaml {{{"
        with pytest.raises(UnsafeSwaggerRefError):
            SwaggerParser._validate_refs(swagger)

    def test_reject_file_scheme_ref(self):
        """拒绝 file:// 协议的 $ref"""
        swagger = '{"paths": {"/x": {"get": {"responses": {"200": {"schema": {"$ref": "file:///etc/passwd"}}}}}}}'
        with pytest.raises(UnsafeSwaggerRefError):
            SwaggerParser._validate_refs(swagger)


class TestSwaggerParserCollectUnsafeRefPaths:
    """测试 SwaggerParser._collect_unsafe_ref_paths 辅助方法"""

    def test_empty_dict(self):
        assert SwaggerParser._collect_unsafe_ref_paths({}) == []

    def test_empty_list(self):
        assert SwaggerParser._collect_unsafe_ref_paths([]) == []

    def test_safe_ref(self):
        node = {"$ref": "#/definitions/User"}
        assert SwaggerParser._collect_unsafe_ref_paths(node) == []

    def test_unsafe_ref(self):
        node = {"$ref": "http://evil.com/payload"}
        assert SwaggerParser._collect_unsafe_ref_paths(node) == ["$.$ref"]

    def test_nested_unsafe_ref(self):
        node = {"paths": {"/test": {"get": {"responses": {"200": {"schema": {"$ref": "/etc/shadow"}}}}}}}
        assert SwaggerParser._collect_unsafe_ref_paths(node) == ["$.paths./test.get.responses.200.schema.$ref"]

    def test_list_with_unsafe_ref(self):
        node = [{"$ref": "#/definitions/OK"}, {"$ref": "http://bad.com/x"}]
        assert SwaggerParser._collect_unsafe_ref_paths(node) == ["$[1].$ref"]

    def test_multiple_unsafe_refs(self):
        node = {
            "a": {"$ref": "http://a.com"},
            "b": {"$ref": "/etc/passwd"},
            "c": {"$ref": "#/definitions/Safe"},
        }
        result = SwaggerParser._collect_unsafe_ref_paths(node)
        assert "$.a.$ref" in result
        assert "$.b.$ref" in result
        assert len(result) == 2
