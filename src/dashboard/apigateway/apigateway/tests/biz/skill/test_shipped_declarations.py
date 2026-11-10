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
import pytest

from apigateway.biz.skill import SKILL_DECLARATIONS_DIR
from apigateway.biz.skill.declaration import parse_declaration
from apigateway.biz.skill.renderer import render_skill_body
from apigateway.biz.skill.resource_loader import ReleasedResourceProvider
from apigateway.biz.skill.validator import validate_declaration
from apigateway.tests.biz.skill.conftest import release_fixture_gateway

pytestmark = pytest.mark.django_db

SHIPPED_NAMES = sorted(path.stem for path in SKILL_DECLARATIONS_DIR.glob("*.yaml"))


@pytest.fixture
def shipped_provider(resources_data):
    """发布声明用到的网关资源及其 OpenAPI schema。"""
    for gateway in sorted({item["gateway"] for item in resources_data["resources"]}):
        release_fixture_gateway(resources_data, gateway)
    return ReleasedResourceProvider()


class TestShippedDeclarations:
    @pytest.mark.parametrize("name", SHIPPED_NAMES)
    def test_validate_and_render(self, shipped_provider, name):
        declaration = parse_declaration((SKILL_DECLARATIONS_DIR / f"{name}.yaml").read_text(encoding="utf-8"))
        assert declaration.name == name

        result = validate_declaration(declaration, shipped_provider)

        assert result.errors == [], result.errors
        assert result.missing_resources == []
        assert result.warnings == [], result.warnings

        rendered = render_skill_body(declaration, shipped_provider)

        assert rendered.body
        assert rendered.warnings == []
