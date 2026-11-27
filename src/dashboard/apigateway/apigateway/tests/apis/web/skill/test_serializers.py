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

from apigateway.apis.web.skill.serializers import SkillBasicInfoInputSLZ

pytestmark = pytest.mark.no_meta_schema

VALID_DATA = {
    "display_name": "发布核对",
    "display_name_en": "Release Check",
    "description": "核对环境差异",
    "tags": ["只读"],
}


class TestSkillBasicInfoInputSLZ:
    def test_validate(self):
        data = {**VALID_DATA, "display_name": " 发布核对 ", "display_name_en": "", "tags": [" JOB ", "只读"]}

        slz = SkillBasicInfoInputSLZ(data=data)

        assert slz.is_valid(), slz.errors
        assert slz.validated_data == {
            "display_name": "发布核对",
            "display_name_en": None,
            "description": "核对环境差异",
            "tags": ["JOB", "只读"],
        }

    @pytest.mark.parametrize(
        "field, value",
        [
            ("display_name", "   "),
            ("display_name", "x" * 65),
            ("display_name", "发布\n核对"),
            ("display_name_en", "Release\rCheck"),
            ("display_name_en", "x" * 65),
            ("description", ""),
            ("description", "x" * 1025),
            ("tags", []),
            ("tags", [" "]),
            ("tags", ["x" * 65]),
            ("tags", ["JOB", " job "]),
        ],
    )
    def test_invalid(self, field, value):
        slz = SkillBasicInfoInputSLZ(data={**VALID_DATA, field: value})

        assert not slz.is_valid()
        assert field in slz.errors
