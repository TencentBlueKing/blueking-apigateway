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
from jinja2.exceptions import TemplateError, TemplateSyntaxError

from apigateway.biz.resource_doc.exceptions import (
    ResourceDocJinja2TemplateError,
    ResourceDocJinja2TemplateSyntaxError,
)


class TestResourceDocJinja2TemplateError:
    def test_str(self, faker):
        filename = faker.pystr()
        err = ResourceDocJinja2TemplateError(filename, TemplateError("error"))
        assert filename in str(err)


class TestResourceDocJinja2TemplateSyntaxError:
    def test_str(self, faker):
        filename = faker.pystr()

        err = ResourceDocJinja2TemplateSyntaxError(
            faker.pystr(), filename, TemplateSyntaxError("error", faker.pyint())
        )
        assert filename in str(err)

        err = ResourceDocJinja2TemplateSyntaxError(
            faker.pystr(), filename, TemplateSyntaxError("error", faker.pyint(), filename=faker.pystr())
        )
        assert filename in str(err)

        # 异常中文件名匹配 base_path 时，消息中去除文件名中的 base_path 部分
        err = ResourceDocJinja2TemplateSyntaxError(
            "/tmp/test", filename, TemplateSyntaxError("error", faker.pyint(), filename="/tmp/test/foo.md")
        )
        assert "/tmp/test" not in str(err)
