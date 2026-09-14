#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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
import os
from dataclasses import replace
from tempfile import TemporaryDirectory
from textwrap import dedent
from typing import cast

import pytest
from jinja2.exceptions import TemplateSyntaxError

from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.biz.resource_doc import OpenAPIDocGenerationError
from apigateway.biz.resource_doc.exceptions import (
    ResourceDocJinja2TemplateError,
    ResourceDocJinja2TemplateNotFound,
    ResourceDocJinja2TemplateSyntaxError,
)
from apigateway.biz.resource_doc.importer import Jinja2ToMarkdownGenerator, OpenAPIToMarkdownGenerator
from apigateway.biz.resource_doc.importer.models import (
    ExampleDoc,
    MediaTypeDoc,
    OperationDocContext,
    ParameterDoc,
    RequestBodyDoc,
    ResponseDoc,
    SchemaDoc,
    SchemaFieldDoc,
)
from apigateway.biz.resource_doc.importer.presenters import OperationDocBuilder
from apigateway.utils.file import write_to_file


class TestJinja2ToMarkdownGenerator:
    def test_generate_doc_content(self):
        with TemporaryDirectory() as output_dir:
            filepath_1 = os.path.join(output_dir, "get_user.md.j2")
            filepath_2 = os.path.join(output_dir, "create_user.md")

            write_to_file("get_user", filepath_1)
            write_to_file("create_user", filepath_2)

            result = Jinja2ToMarkdownGenerator("zh/get_user.md.j2", filepath_1).generate_doc_content()
            assert result == "get_user"

            result = Jinja2ToMarkdownGenerator("zh/create_user.md", filepath_2).generate_doc_content()
            assert result == "create_user"

    @pytest.mark.parametrize(
        "filepath, expected",
        [
            ("get_user.md.j2", True),
            ("get_user.md", False),
            ("get_user.j2", False),
        ],
    )
    def test_is_jinja2_template(self, faker, filepath, expected):
        generator = Jinja2ToMarkdownGenerator(faker.pystr(), filepath)
        assert generator._is_jinja2_template() is expected

    def test_render_jinja2_template(self, mocker):
        with TemporaryDirectory() as output_dir:
            filepath = os.path.join(output_dir, "get_user.md.j2")
            generator = Jinja2ToMarkdownGenerator("get_user.md.j2", filepath)

            write_to_file("{% include '_common.md.j2' %}, get_user", filepath)
            write_to_file("hi", os.path.join(output_dir, "_common.md.j2"))
            assert generator._render_jinja2_template() == "hi, get_user"

            write_to_file("{% include '_common.md.j2 %}, get_user", filepath)
            with pytest.raises(ResourceDocJinja2TemplateSyntaxError) as err:
                generator._render_jinja2_template()
            assert output_dir not in str(err.value)

            write_to_file("{% include '_not_found.md.j2' %}, get_user", filepath)
            with pytest.raises(ResourceDocJinja2TemplateNotFound):
                generator._render_jinja2_template()

            mocker.patch(
                "apigateway.biz.resource_doc.importer.generators.SandboxedEnvironment.get_template",
                side_effect=ValueError(),
            )
            write_to_file("{% include '_common.md.j2' %}, get_user", filepath)
            with pytest.raises(ResourceDocJinja2TemplateError):
                generator._render_jinja2_template()


@pytest.fixture
def operation_context():
    request_schema = SchemaDoc(
        type="object",
        description="Profile payload",
        fields=[
            SchemaFieldDoc(
                path="name",
                type="string",
                required=True,
                description="Display name",
                constraints="minLength: 1",
                example="Alice",
            )
        ],
        example="",
    )
    response_schema = SchemaDoc(
        type="object",
        description="",
        fields=[
            SchemaFieldDoc(
                path="id",
                type="integer&lt;int64&gt;",
                required=True,
                description="User ID",
                constraints="",
                example="1",
            )
        ],
        example="",
    )
    return OperationDocContext(
        operation_id="update_user",
        method="POST",
        path="/users/{user_id}",
        summary="Update user",
        description="Updates a user profile.",
        deprecated=True,
        tags=["users"],
        parameters=[
            ParameterDoc(
                name="verbose",
                location="query",
                type="boolean",
                required=False,
                description="Return details",
                default="false",
                example="true",
                constraints="",
            )
        ],
        request_body=RequestBodyDoc(
            required=True,
            description="Profile data",
            contents=[
                MediaTypeDoc(
                    media_type="application/json",
                    schema=request_schema,
                    examples=[ExampleDoc(name="profile", summary="Example profile", value='{"name": "Alice"}')],
                )
            ],
        ),
        responses=[
            ResponseDoc(
                status_code="200",
                status_text="OK",
                description="Updated user",
                headers=[
                    ParameterDoc(
                        name="X-Request-ID",
                        location="header",
                        type="string",
                        required=False,
                        description="Request ID",
                        default="",
                        example="req-1",
                        constraints="",
                    )
                ],
                contents=[
                    MediaTypeDoc(
                        media_type="application/json",
                        schema=response_schema,
                        examples=[],
                    )
                ],
            )
        ],
    )


@pytest.fixture
def empty_operation_context():
    return OperationDocContext(
        operation_id="health",
        method="GET",
        path="/health",
        summary="",
        description="",
        deprecated=False,
        tags=[],
        parameters=[],
        request_body=None,
        responses=[],
    )


def test_generate_openapi_doc_in_english(operation_context):
    content = OpenAPIToMarkdownGenerator(operation_context, DocLanguageEnum.EN).generate_doc_content()

    assert (
        content
        == dedent(
            """
        ### API information

        | Method | Path | Operation ID | Tags | Deprecated |
        | --- | --- | --- | --- | :---: |
        | <code>POST</code> | <code>/users/{user_id}</code> | <code>update_user</code> | users | Yes |

        ### Description

        Update user

        Updates a user profile.

        ### Request parameters

        #### Query parameters

        | Name | Type | Required | Description | Default | Constraints | Example |
        | --- | --- | :---: | --- | --- | --- | --- |
        | verbose | <code>boolean</code> | No | Return details | false |  | true |

        ### Request body

        Required: Yes

        Profile data

        #### application/json

        Type: <code>object</code>

        Profile payload

        | Field | Type | Required | Description | Constraints | Example |
        | --- | --- | :---: | --- | --- | --- |
        | name | <code>string</code> | Yes | Display name | minLength: 1 | Alice |

        ##### Example: profile - Example profile

        ```json
        {"name": "Alice"}
        ```

        ### Responses

        | Status code | Status | Description |
        | --- | --- | --- |
        | <code>200</code> | OK | Updated user |

        #### 200 - OK

        ##### Response headers

        | Name | Type | Required | Description | Default | Constraints | Example |
        | --- | --- | :---: | --- | --- | --- | --- |
        | X-Request-ID | <code>string</code> | No | Request ID |  |  | req-1 |

        ##### application/json

        Type: <code>object</code>

        | Field | Type | Required | Description | Constraints | Example |
        | --- | --- | :---: | --- | --- | --- |
        | id | <code>integer&lt;int64&gt;</code> | Yes | User ID |  | 1 |
        """
        ).strip()
    )


def test_generate_openapi_doc_in_chinese(operation_context):
    content = OpenAPIToMarkdownGenerator(operation_context, DocLanguageEnum.ZH).generate_doc_content()

    assert (
        content
        == dedent(
            """
        ### API 信息

        | 方法 | 路径 | 操作 ID | 标签 | 已废弃 |
        | --- | --- | --- | --- | :---: |
        | <code>POST</code> | <code>/users/{user_id}</code> | <code>update_user</code> | users | 是 |

        ### 描述

        Update user

        Updates a user profile.

        ### 请求参数

        #### 查询参数

        | 名称 | 类型 | 必填 | 描述 | 默认值 | 约束 | 示例 |
        | --- | --- | :---: | --- | --- | --- | --- |
        | verbose | <code>boolean</code> | 否 | Return details | false |  | true |

        ### 请求体

        必填: 是

        Profile data

        #### application/json

        类型: <code>object</code>

        Profile payload

        | 字段 | 类型 | 必填 | 描述 | 约束 | 示例 |
        | --- | --- | :---: | --- | --- | --- |
        | name | <code>string</code> | 是 | Display name | minLength: 1 | Alice |

        ##### 示例: profile - Example profile

        ```json
        {"name": "Alice"}
        ```

        ### 响应

        | 状态码 | 状态 | 描述 |
        | --- | --- | --- |
        | <code>200</code> | OK | Updated user |

        #### 200 - OK

        ##### 响应头

        | 名称 | 类型 | 必填 | 描述 | 默认值 | 约束 | 示例 |
        | --- | --- | :---: | --- | --- | --- | --- |
        | X-Request-ID | <code>string</code> | 否 | Request ID |  |  | req-1 |

        ##### application/json

        类型: <code>object</code>

        | 字段 | 类型 | 必填 | 描述 | 约束 | 示例 |
        | --- | --- | :---: | --- | --- | --- |
        | id | <code>integer&lt;int64&gt;</code> | 是 | User ID |  | 1 |
        """
        ).strip()
    )


def test_generate_openapi_doc_omits_empty_sections(empty_operation_context):
    content = OpenAPIToMarkdownGenerator(
        empty_operation_context,
        DocLanguageEnum.EN,
    ).generate_doc_content()

    assert "### API information" in content
    assert "### Description" not in content
    assert "### Request parameters" not in content
    assert "### Request body" not in content
    assert "### Responses" not in content


def test_generate_openapi_doc_omits_empty_response_details(empty_operation_context):
    context = replace(
        empty_operation_context,
        responses=[
            ResponseDoc(
                status_code="204",
                status_text="No Content",
                description="No content",
                headers=[],
                contents=[MediaTypeDoc(media_type="application/json", schema=None, examples=[])],
            )
        ],
    )

    content = OpenAPIToMarkdownGenerator(context, DocLanguageEnum.EN).generate_doc_content()

    assert "| <code>204</code> | No Content | No content |" in content
    assert "#### 204 - No Content" not in content


def test_generate_openapi_doc_rejects_unsupported_language(empty_operation_context):
    language = cast("DocLanguageEnum", "fr")
    with pytest.raises(OpenAPIDocGenerationError):
        OpenAPIToMarkdownGenerator(empty_operation_context, language).generate_doc_content()


def test_generate_openapi_doc_wraps_template_error(mocker, empty_operation_context):
    mocker.patch(
        "apigateway.biz.resource_doc.importer.generators.SandboxedEnvironment.get_template",
        side_effect=TemplateSyntaxError("broken template", 1),
    )
    with pytest.raises(OpenAPIDocGenerationError):
        OpenAPIToMarkdownGenerator(empty_operation_context, DocLanguageEnum.EN).generate_doc_content()


@pytest.mark.parametrize("language", [DocLanguageEnum.EN, DocLanguageEnum.ZH])
@pytest.mark.parametrize(
    ("payload", "escaped"),
    [
        ("<img src=x onerror=\"alert('x')\">", "&lt;img src=x onerror=&quot;alert(&#x27;x&#x27;)&quot;&gt;"),
        ("<script>alert(1)</script>", "&lt;script&gt;alert(1)&lt;/script&gt;"),
        ("&lt;img src=x&gt;", "&amp;lt;img src=x&amp;gt;"),
    ],
)
def test_generated_openapi_doc_escapes_user_html(language, payload, escaped):
    schema = {
        "type": "object",
        "description": payload,
        "properties": {payload: {"type": "string", "description": payload, "example": payload}},
    }
    operation = {
        "operationId": payload,
        "summary": payload,
        "description": f"**Details**\n\n{payload}\n\n- first\n- second",
        "tags": [payload],
        "parameters": [
            {
                "name": payload,
                "in": "query",
                "description": payload + "\nnext",
                "schema": {"type": "string", "default": payload, "pattern": payload},
            }
        ],
        "requestBody": {"description": payload, "content": {payload: {"schema": schema}}},
        "responses": {"200": {"description": payload, "headers": {payload: {"description": payload}}}},
    }
    context = OperationDocBuilder({"paths": {"/users": {"get": operation}}}).build()

    content = OpenAPIToMarkdownGenerator(context, language).generate_doc_content()

    assert payload not in content
    assert f"**Details**\n\n{escaped}\n\n- first\n- second" in content
    assert f"{escaped}<br>next" in content
    assert content.count(escaped) >= 13
    assert "&lt;br&gt;next" not in content


def test_generated_openapi_doc_keeps_example_inside_code_fence(empty_operation_context):
    payload = '```\n<img src=x onerror="alert(1)">\n````'
    context = replace(
        empty_operation_context,
        request_body=RequestBodyDoc(
            required=False,
            description="",
            contents=[
                MediaTypeDoc(
                    media_type="text/plain", schema=None, examples=[ExampleDoc(name="", summary="", value=payload)]
                )
            ],
        ),
    )

    content = OpenAPIToMarkdownGenerator(context, DocLanguageEnum.EN).generate_doc_content()

    assert f"`````json\n{payload}\n`````" in content
