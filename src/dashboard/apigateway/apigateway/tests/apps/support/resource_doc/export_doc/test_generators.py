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
from ddf import G

from apigateway.apps.support.models import ResourceDoc
from apigateway.apps.support.resource_doc.exceptions import NoResourceDocError
from apigateway.apps.support.resource_doc.export_doc.generators import DocArchiveGenerator
from apigateway.core.models import Gateway, Resource

pytestmark = pytest.mark.django_db


class TestDocArchiveGenerator:
    def test_generate(self, mocker, faker):
        mocker.patch(
            "apigateway.apps.support.resource_doc.export_doc.generators.write_to_file",
            return_value=None,
        )

        gateway = G(Gateway)
        r1 = G(Resource, api=gateway, name=faker.pystr())
        r2 = G(Resource, api=gateway, name=faker.pystr())
        G(ResourceDoc, api=gateway, resource_id=r1.id, language="zh")

        generator = DocArchiveGenerator()
        result = generator.generate("/tmp", gateway.id, [r1.id])
        assert result == [f"zh/{r1.name}.md"]

        with pytest.raises(NoResourceDocError):
            generator.generate("/tmp", gateway.id, [r2.id])
