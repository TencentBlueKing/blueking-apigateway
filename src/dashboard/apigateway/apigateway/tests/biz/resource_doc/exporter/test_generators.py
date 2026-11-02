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
import json

import pytest
from django_dynamic_fixture import G

from apigateway.apps.support.models import ResourceDocVersion
from apigateway.biz.resource_doc import NoResourceDocError
from apigateway.biz.resource_doc.exporter import DocArchiveGenerator, ResourceVersionDocArchiveGenerator
from apigateway.core.models import Resource, ResourceVersion


class TestDocArchiveGenerator:
    def test_generate(self, tmp_path, fake_resource_doc):

        fake_gateway = fake_resource_doc.gateway
        resource = Resource.objects.get(id=fake_resource_doc.resource_id)

        generator = DocArchiveGenerator()
        result = generator.generate(str(tmp_path), fake_gateway.id, [fake_resource_doc.resource_id])
        assert result == [f"{fake_resource_doc.language}/{resource.name}.md"]
        assert (tmp_path / result[0]).read_text() == fake_resource_doc.content

        with pytest.raises(NoResourceDocError):
            generator.generate(str(tmp_path), fake_gateway.id, [0])


class TestResourceVersionDocArchiveGenerator:
    def test_generate(self, tmp_path, fake_gateway):

        rv = G(
            ResourceVersion,
            gateway=fake_gateway,
            version="1.0.0",
            _data=json.dumps(
                [
                    {"id": 1, "name": "get_user"},
                    {"id": 2, "name": "create_user"},
                ]
            ),
        )
        G(
            ResourceDocVersion,
            gateway=fake_gateway,
            resource_version=rv,
            _data=json.dumps(
                [
                    {"resource_id": 1, "language": "zh", "content": "# 获取用户"},
                    {"resource_id": 2, "language": "zh", "content": "# 创建用户"},
                    {"resource_id": 1, "language": "en", "content": "# Get User"},
                ]
            ),
        )

        generator = ResourceVersionDocArchiveGenerator()
        result = generator.generate(str(tmp_path), rv)
        assert {name: (tmp_path / name).read_text() for name in result} == {
            "zh/get_user.md": "# 获取用户",
            "zh/create_user.md": "# 创建用户",
            "en/get_user.md": "# Get User",
        }

        # 没有对应的文档版本时应抛出异常
        rv_no_doc = G(
            ResourceVersion,
            gateway=fake_gateway,
            version="2.0.0",
            _data=json.dumps([{"id": 1, "name": "get_user"}]),
        )
        with pytest.raises(NoResourceDocError):
            generator.generate(str(tmp_path), rv_no_doc)

    def test_generate_skip_unknown_resource_id(self, tmp_path, fake_gateway):

        rv = G(
            ResourceVersion,
            gateway=fake_gateway,
            version="1.0.0",
            _data=json.dumps([{"id": 1, "name": "get_user"}]),
        )
        G(
            ResourceDocVersion,
            gateway=fake_gateway,
            resource_version=rv,
            _data=json.dumps(
                [
                    {"resource_id": 1, "language": "zh", "content": "# 获取用户"},
                    {"resource_id": 999, "language": "zh", "content": "# 未知资源"},
                ]
            ),
        )

        generator = ResourceVersionDocArchiveGenerator()
        result = generator.generate(str(tmp_path), rv)
        assert result == ["zh/get_user.md"]
        assert (tmp_path / result[0]).read_text() == "# 获取用户"
        assert len(list(tmp_path.rglob("*.md"))) == 1
