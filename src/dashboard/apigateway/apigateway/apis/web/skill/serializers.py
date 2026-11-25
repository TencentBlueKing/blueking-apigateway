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
from typing import Any, Callable, List, Optional

from django.utils.translation import gettext as _
from rest_framework import serializers

from apigateway.apps.skill.constants import (
    SKILL_DESCRIPTION_MAX_LENGTH,
    SKILL_DISPLAY_NAME_MAX_LENGTH,
    SkillStatusEnum,
)
from apigateway.biz.skill import (
    SKILL_PACKAGE_MAX_SIZE,
    check_skill_description,
    check_skill_display_name,
    check_skill_tags,
)


class SkillChangelogOutputSLZ(serializers.Serializer):
    date = serializers.CharField(read_only=True, help_text="日期，YYYY-MM-DD")
    content = serializers.CharField(read_only=True, help_text="更新说明")

    class Meta:
        ref_name = "apigateway.apis.web.skill.serializers.SkillChangelogOutputSLZ"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # 包里的 date 可能带时分秒，接口统一返回日期
        data["date"] = data["date"][:10]
        return data


class SkillVersionOutputSLZ(serializers.Serializer):
    version = serializers.CharField(read_only=True, help_text="版本号")
    is_current = serializers.SerializerMethodField(help_text="是否为线上版本")
    changelog = SkillChangelogOutputSLZ(read_only=True, help_text="更新说明")
    published_by = serializers.CharField(source="created_by", read_only=True, help_text="发布人")
    published_time = serializers.DateTimeField(source="created_time", read_only=True, help_text="发布时间")

    class Meta:
        ref_name = "apigateway.apis.web.skill.serializers.SkillVersionOutputSLZ"

    def get_is_current(self, obj) -> bool:
        return obj.id == self.context["current_version_id"]


class SkillFileOutputSLZ(serializers.Serializer):
    path = serializers.CharField(read_only=True, help_text="相对 {name}/ 的路径")
    content = serializers.CharField(read_only=True, help_text="文件内容")

    class Meta:
        ref_name = "apigateway.apis.web.skill.serializers.SkillFileOutputSLZ"


class SkillFileListOutputSLZ(serializers.Serializer):
    name = serializers.CharField(read_only=True, help_text="Skill 规范名，即解压后的目录名")
    version = serializers.CharField(read_only=True, help_text="版本号")
    files = SkillFileOutputSLZ(many=True, read_only=True, help_text="文件，内容和下载包逐字相同")

    class Meta:
        ref_name = "apigateway.apis.web.skill.serializers.SkillFileListOutputSLZ"


class SkillTagOutputSLZ(serializers.Serializer):
    name = serializers.CharField(read_only=True, help_text="标签名")
    skill_count = serializers.IntegerField(read_only=True, help_text="带这个标签的 Skill 数")

    class Meta:
        ref_name = "apigateway.apis.web.skill.serializers.SkillTagOutputSLZ"


class SkillTagListInputSLZ(serializers.Serializer):
    keyword = serializers.CharField(allow_blank=True, required=False, help_text="搜索标签名")

    class Meta:
        ref_name = "apigateway.apis.web.skill.serializers.SkillTagListInputSLZ"


class SkillApiRefOutputSLZ(serializers.Serializer):
    gateway_name = serializers.CharField(read_only=True, help_text="网关名")
    resource_name = serializers.CharField(read_only=True, help_text="资源名")

    class Meta:
        ref_name = "apigateway.apis.web.skill.serializers.SkillApiRefOutputSLZ"


class SkillValidationMessageOutputSLZ(serializers.Serializer):
    file = serializers.CharField(read_only=True, allow_null=True, help_text="包内文件，如 release-check/SKILL.md")
    field = serializers.CharField(read_only=True, allow_null=True, help_text="字段路径")
    message = serializers.CharField(read_only=True, help_text="说明")

    class Meta:
        ref_name = "apigateway.apis.web.skill.serializers.SkillValidationMessageOutputSLZ"


def validate_skill_package_file(value):
    """zip 包不超过 SKILL_PACKAGE_MAX_SIZE"""
    if value.size > SKILL_PACKAGE_MAX_SIZE:
        raise serializers.ValidationError(
            _("文件不能超过 {size} MB").format(size=SKILL_PACKAGE_MAX_SIZE // (1024 * 1024))
        )


def _check_basic_info(check: Callable[[Any], Any], value: Any) -> Any:
    """按声明的字段规则校验，ValueError 转成字段的 ValidationError"""
    try:
        return check(value)
    except ValueError as err:
        raise serializers.ValidationError(str(err))


class SkillBasicInfoInputSLZ(serializers.Serializer):
    """表单里的基本信息；上传时覆盖包里的同名字段，只改基本信息时直接写入；字段规则同声明"""

    display_name = serializers.CharField(max_length=SKILL_DISPLAY_NAME_MAX_LENGTH, help_text="名称")
    display_name_en = serializers.CharField(
        max_length=SKILL_DISPLAY_NAME_MAX_LENGTH,
        required=False,
        allow_blank=True,
        allow_null=True,
        default=None,
        help_text="英文名，空字符串或 null 表示没有",
    )
    description = serializers.CharField(max_length=SKILL_DESCRIPTION_MAX_LENGTH, help_text="描述")
    tags = serializers.ListField(child=serializers.CharField(allow_blank=True), help_text="标签")

    class Meta:
        ref_name = "apigateway.apis.web.skill.serializers.SkillBasicInfoInputSLZ"

    def validate_display_name(self, value: str) -> str:
        return _check_basic_info(check_skill_display_name, value)

    def validate_display_name_en(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        return _check_basic_info(check_skill_display_name, value)

    def validate_description(self, value: str) -> str:
        return _check_basic_info(check_skill_description, value)

    def validate_tags(self, value: List[str]) -> List[str]:
        return _check_basic_info(check_skill_tags, value)


class SkillPackageCheckInputSLZ(serializers.Serializer):
    file = serializers.FileField(
        validators=[validate_skill_package_file], help_text="zip 包，需含 declaration.yaml，不超过 2 MB"
    )
    skill_id = serializers.CharField(required=False, allow_blank=True, help_text="更新时传当前 Skill 的 skill_id")

    class Meta:
        ref_name = "apigateway.apis.web.skill.serializers.SkillPackageCheckInputSLZ"


class SkillPackageOutputSLZ(serializers.Serializer):
    name = serializers.CharField(read_only=True, help_text="规范名")
    display_name = serializers.CharField(read_only=True, help_text="名称")
    display_name_en = serializers.CharField(read_only=True, allow_null=True, help_text="英文名")
    description = serializers.CharField(read_only=True, help_text="描述")
    tags = serializers.ListField(child=serializers.CharField(), read_only=True, help_text="标签")
    version = serializers.CharField(read_only=True, help_text="版本号")
    changelog = SkillChangelogOutputSLZ(read_only=True, help_text="更新说明")
    stage = serializers.CharField(read_only=True, allow_null=True, help_text="调用的环境")
    apis = SkillApiRefOutputSLZ(many=True, read_only=True, help_text="调用的接口")

    class Meta:
        ref_name = "apigateway.apis.web.skill.serializers.SkillPackageOutputSLZ"


class SkillExistingOutputSLZ(serializers.Serializer):
    skill_id = serializers.CharField(read_only=True, help_text="对外 ID")
    current_version = serializers.CharField(read_only=True, help_text="线上版本号")
    latest_version = serializers.CharField(read_only=True, allow_null=True, help_text="已有的最高版本号")
    status = serializers.CharField(read_only=True, help_text="状态")

    class Meta:
        ref_name = "apigateway.apis.web.skill.serializers.SkillExistingOutputSLZ"


class SkillPackageCheckOutputSLZ(serializers.Serializer):
    errors = SkillValidationMessageOutputSLZ(many=True, read_only=True)
    warnings = SkillValidationMessageOutputSLZ(many=True, read_only=True)
    package = SkillPackageOutputSLZ(read_only=True, allow_null=True, help_text="包里的内容，解析失败时为 null")
    existing_skill = SkillExistingOutputSLZ(read_only=True, allow_null=True, help_text="本网关已有的同名 Skill")
    basic_info_diffs = serializers.ListField(
        child=serializers.CharField(), read_only=True, help_text="包里和线上不同的基本信息字段"
    )

    class Meta:
        ref_name = "apigateway.apis.web.skill.serializers.SkillPackageCheckOutputSLZ"


class SkillPublishInputSLZ(SkillBasicInfoInputSLZ):
    file = serializers.FileField(
        validators=[validate_skill_package_file], help_text="zip 包，需含 declaration.yaml，不超过 2 MB"
    )
    version = serializers.CharField(help_text="版本号，major.minor.patch")
    overwrite = serializers.BooleanField(default=False, help_text="版本号已存在时是否覆盖")

    class Meta:
        ref_name = "apigateway.apis.web.skill.serializers.SkillPublishInputSLZ"


class SkillPublishOutputSLZ(serializers.Serializer):
    skill_id = serializers.CharField(read_only=True, help_text="对外 ID")

    class Meta:
        ref_name = "apigateway.apis.web.skill.serializers.SkillPublishOutputSLZ"


class SkillListInputSLZ(serializers.Serializer):
    keyword = serializers.CharField(allow_blank=True, required=False, help_text="匹配名称、描述、标签、接口名")
    tag = serializers.CharField(allow_blank=True, required=False, help_text="标签名，不区分大小写")
    status = serializers.ChoiceField(
        choices=[SkillStatusEnum.PUBLISHED.value, SkillStatusEnum.ARCHIVED.value],
        required=False,
        help_text="状态，不传为全部",
    )
    order_by = serializers.ChoiceField(
        choices=["-updated_time", "name", "-download_count"], default="-updated_time", help_text="排序"
    )

    class Meta:
        ref_name = "apigateway.apis.web.skill.serializers.SkillListInputSLZ"


class SkillBaseOutputSLZ(serializers.Serializer):
    skill_id = serializers.CharField(source="code", read_only=True, help_text="对外 ID")
    name = serializers.CharField(read_only=True, help_text="规范名")
    display_name = serializers.CharField(read_only=True, help_text="中文名原值")
    display_name_en = serializers.CharField(read_only=True, allow_null=True, help_text="英文名原值")
    description = serializers.CharField(read_only=True, help_text="描述")
    tags = serializers.SerializerMethodField(help_text="标签")
    status = serializers.CharField(read_only=True, help_text="状态")
    download_count = serializers.IntegerField(read_only=True, help_text="下载数")
    updated_by = serializers.CharField(read_only=True, help_text="最后修改人")
    updated_time = serializers.DateTimeField(read_only=True, help_text="最后修改时间")

    class Meta:
        ref_name = "apigateway.apis.web.skill.serializers.SkillBaseOutputSLZ"

    def get_tags(self, obj) -> List[str]:
        return [tag.name for tag in obj.tags.all()]


class SkillListOutputSLZ(SkillBaseOutputSLZ):
    version = serializers.CharField(source="current_version.version", read_only=True, help_text="线上版本号")

    class Meta:
        ref_name = "apigateway.apis.web.skill.serializers.SkillListOutputSLZ"


class SkillRetrieveOutputSLZ(SkillBaseOutputSLZ):
    current_version = SkillVersionOutputSLZ(read_only=True, help_text="线上版本")
    stage = serializers.SerializerMethodField(help_text="调用的环境")
    apis = serializers.SerializerMethodField(help_text="线上版本调用的接口")
    version_count = serializers.SerializerMethodField(help_text="版本数")
    download_url = serializers.SerializerMethodField(help_text="免登录下载地址；已归档时为 null")
    created_by = serializers.CharField(read_only=True, help_text="第一次上传的人")
    created_time = serializers.DateTimeField(read_only=True, help_text="第一次上传的时间")

    class Meta:
        ref_name = "apigateway.apis.web.skill.serializers.SkillRetrieveOutputSLZ"

    def get_stage(self, obj) -> Optional[str]:
        return self.context["stage"]

    def get_apis(self, obj) -> List[dict]:
        return SkillApiRefOutputSLZ(self.context["apis"], many=True).data

    def get_version_count(self, obj) -> int:
        return self.context["version_count"]

    def get_download_url(self, obj) -> Optional[str]:
        return self.context["download_url"]


class SkillCurrentVersionUpdateInputSLZ(serializers.Serializer):
    version = serializers.CharField(help_text="要切换到的版本号")

    class Meta:
        ref_name = "apigateway.apis.web.skill.serializers.SkillCurrentVersionUpdateInputSLZ"


class SkillStatusUpdateInputSLZ(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[SkillStatusEnum.PUBLISHED.value, SkillStatusEnum.ARCHIVED.value],
        help_text="archived 为归档，published 为恢复",
    )

    class Meta:
        ref_name = "apigateway.apis.web.skill.serializers.SkillStatusUpdateInputSLZ"
