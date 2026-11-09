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

from apigateway.apps.skill.constants import SKILL_CODE_PREFIXES, SkillStatusEnum, SkillTypeEnum


class TestSkillTypeEnum:
    def test_values(self):
        assert SkillTypeEnum.get_values() == ["platform", "gateway"]

    def test_every_type_has_code_prefix(self):
        assert set(SKILL_CODE_PREFIXES) == set(SkillTypeEnum.get_values())


class TestSkillStatusEnum:
    def test_values(self):
        assert SkillStatusEnum.get_values() == ["unpublished", "published", "offline"]
