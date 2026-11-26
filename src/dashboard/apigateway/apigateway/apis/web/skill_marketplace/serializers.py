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
from typing import List, Optional

from rest_framework import serializers

from apigateway.apis.web.skill.serializers import SkillApiRefOutputSLZ, SkillVersionOutputSLZ
from apigateway.apps.skill.constants import SkillTypeEnum
from apigateway.biz.skill import SkillHandler
from apigateway.common.i18n.field import SerializerTranslatedField


class SkillMarketplaceListInputSLZ(serializers.Serializer):
    type = serializers.ChoiceField(choices=SkillTypeEnum.get_choices(), required=False, help_text="类型，不传为全部")
    tag = serializers.CharField(allow_blank=True, required=False, help_text="标签名，不区分大小写")
    keyword = serializers.CharField(allow_blank=True, required=False, help_text="匹配名称、描述、标签、网关名、接口名")
    order_by = serializers.ChoiceField(
        choices=["-published_time", "-download_count", "name"], default="-published_time", help_text="排序"
    )

    class Meta:
        ref_name = "apigateway.apis.web.skill_marketplace.serializers.SkillMarketplaceListInputSLZ"


class SkillMarketplaceCountInputSLZ(serializers.Serializer):
    tag = serializers.CharField(allow_blank=True, required=False, help_text="标签名，不区分大小写")
    keyword = serializers.CharField(allow_blank=True, required=False, help_text="同列表")

    class Meta:
        ref_name = "apigateway.apis.web.skill_marketplace.serializers.SkillMarketplaceCountInputSLZ"


class SkillMarketplaceCountOutputSLZ(serializers.Serializer):
    platform = serializers.IntegerField(read_only=True, help_text="平台内置 Skill 数")
    gateway = serializers.IntegerField(read_only=True, help_text="网关 Skill 数")

    class Meta:
        ref_name = "apigateway.apis.web.skill_marketplace.serializers.SkillMarketplaceCountOutputSLZ"


class SkillMarketplaceTagListInputSLZ(serializers.Serializer):
    type = serializers.ChoiceField(choices=SkillTypeEnum.get_choices(), required=False, help_text="类型")
    keyword = serializers.CharField(allow_blank=True, required=False, help_text="搜索标签名")

    class Meta:
        ref_name = "apigateway.apis.web.skill_marketplace.serializers.SkillMarketplaceTagListInputSLZ"


class SkillGatewayRefOutputSLZ(serializers.Serializer):
    name = serializers.CharField(read_only=True, help_text="网关名")
    display_name = serializers.CharField(read_only=True, help_text="网关展示名，没填时为网关名")

    class Meta:
        ref_name = "apigateway.apis.web.skill_marketplace.serializers.SkillGatewayRefOutputSLZ"


class SkillMarketplaceBaseOutputSLZ(serializers.Serializer):
    skill_id = serializers.CharField(source="code", read_only=True, help_text="对外 ID")
    type = serializers.CharField(read_only=True, help_text="类型")
    name = serializers.CharField(read_only=True, help_text="规范名")
    display_name = SerializerTranslatedField(default_field="display_name_i18n", read_only=True, help_text="名称")
    description = serializers.CharField(read_only=True, help_text="描述")
    tags = serializers.SerializerMethodField(help_text="标签")
    gateway = serializers.SerializerMethodField(help_text="所属网关，内置 Skill 为 null")
    download_count = serializers.IntegerField(read_only=True, help_text="下载数")

    class Meta:
        ref_name = "apigateway.apis.web.skill_marketplace.serializers.SkillMarketplaceBaseOutputSLZ"

    def get_tags(self, obj) -> List[str]:
        return [tag.name for tag in obj.tags.all()]

    def get_gateway(self, obj) -> Optional[dict]:
        if obj.gateway is None:
            return None
        return SkillGatewayRefOutputSLZ(
            {"name": obj.gateway.name, "display_name": obj.gateway.display_name_or_name}
        ).data


class SkillMarketplaceListOutputSLZ(SkillMarketplaceBaseOutputSLZ):
    version = serializers.CharField(source="current_version.version", read_only=True, help_text="线上版本号")
    related_gateways = serializers.SerializerMethodField(help_text="线上版本调用到的网关")
    published_time = serializers.DateTimeField(
        source="current_version.created_time", read_only=True, help_text="线上版本的发布时间"
    )

    class Meta:
        ref_name = "apigateway.apis.web.skill_marketplace.serializers.SkillMarketplaceListOutputSLZ"

    def get_related_gateways(self, obj) -> List[dict]:
        return SkillGatewayRefOutputSLZ(self.context["related_gateways"].get(obj.id, []), many=True).data


class SkillMarketplaceRetrieveOutputSLZ(SkillMarketplaceBaseOutputSLZ):
    current_version = SkillVersionOutputSLZ(read_only=True, help_text="线上版本")
    stage = serializers.SerializerMethodField(help_text="网关 Skill 调用的环境，内置 Skill 为 null")
    apis = serializers.SerializerMethodField(help_text="线上版本调用的接口")
    version_count = serializers.SerializerMethodField(help_text="版本数")
    download_url = serializers.SerializerMethodField(help_text="页面下载地址，需登录")
    public_download_url = serializers.SerializerMethodField(help_text="免登录下载地址，给 npx 临时使用")

    class Meta:
        ref_name = "apigateway.apis.web.skill_marketplace.serializers.SkillMarketplaceRetrieveOutputSLZ"

    def get_stage(self, obj) -> Optional[str]:
        return self.context["stage"]

    def get_apis(self, obj) -> List[dict]:
        return SkillApiRefOutputSLZ(self.context["apis"], many=True).data

    def get_version_count(self, obj) -> int:
        return self.context["version_count"]

    def get_download_url(self, obj) -> str:
        return SkillHandler.build_market_download_url(obj)

    def get_public_download_url(self, obj) -> Optional[str]:
        return SkillHandler.build_public_download_url(obj)
