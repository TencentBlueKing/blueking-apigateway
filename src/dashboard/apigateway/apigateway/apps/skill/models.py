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

from django.db import models
from django.utils.translation import gettext_lazy as _

from apigateway.common.mixins.models import OperatorModelMixin, TimestampedModelMixin
from apigateway.core.models import Gateway

from .constants import (
    SKILL_CODE_MAX_LENGTH,
    SKILL_DESCRIPTION_MAX_LENGTH,
    SKILL_ID_PREFIXES,
    SKILL_NAME_MAX_LENGTH,
    SKILL_TAG_NAME_MAX_LENGTH,
    SKILL_VERSION_MAX_LENGTH,
    SkillStatusEnum,
    SkillTypeEnum,
)


class SkillTag(models.Model):
    """Skill 标签，推送时映射为 bk-aidev 的 tag_names"""

    name = models.CharField(max_length=SKILL_TAG_NAME_MAX_LENGTH, unique=True, help_text=_("标签名称"))

    def __str__(self):
        return f"<SkillTag: {self.pk}/{self.name}>"

    class Meta:
        verbose_name = _("Skill 标签")
        verbose_name_plural = _("Skill 标签")
        db_table = "skill_tag"


class SkillMetadata(TimestampedModelMixin, OperatorModelMixin):
    """Skill 元数据，以 (type, gateway, code) 为唯一标识"""

    code = models.CharField(max_length=SKILL_CODE_MAX_LENGTH, help_text=_("Skill 标识，用于拼接对外 ID"))
    type = models.CharField(max_length=16, choices=SkillTypeEnum.get_choices(), help_text=_("Skill 来源类型"))
    # 内置 Skill 为 NULL，MySQL 唯一索引不把多个 NULL 视为重复，(type, gateway, code) 只约束网关 Skill；
    # 内置 Skill 的 code 不重复由注入逻辑保证。
    gateway = models.ForeignKey(
        Gateway,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text=_("所属网关，内置 Skill 为空"),
    )
    name = models.CharField(max_length=SKILL_NAME_MAX_LENGTH, help_text=_("Skill 展示名"))
    description = models.CharField(max_length=SKILL_DESCRIPTION_MAX_LENGTH, help_text=_("Skill 描述"))
    status = models.CharField(
        max_length=16,
        choices=SkillStatusEnum.get_choices(),
        default=SkillStatusEnum.UNPUBLISHED.value,
        help_text=_("Skill 状态"),
    )
    # 用 QuerySet.update(F() + 1) 累加，不经过 save()，避免刷新 updated_time
    download_count = models.PositiveIntegerField(default=0, help_text=_("下载数"))

    # SET_NULL：删除 metadata（含随网关级联）时先置空再删版本。RESTRICT 会与 versions 的 CASCADE
    # 构成删除依赖环，Django 无法排序而先删 metadata，MySQL 立即检查外键报 1451；PROTECT 则报 ProtectedError。
    current_version = models.ForeignKey(
        "SkillVersion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text=_("当前版本"),
    )
    tags = models.ManyToManyField(
        SkillTag,
        blank=True,
        related_name="metadata_set",
        help_text=_("Skill 标签"),
    )

    def __str__(self):
        return f"<SkillMetadata: {self.pk}/{self.code}>"

    class Meta:
        verbose_name = _("Skill 元数据")
        verbose_name_plural = _("Skill 元数据")
        db_table = "skill_metadata"
        unique_together = ("type", "gateway", "code")

    @property
    def skill_id(self) -> str:
        """对外 ID，读取时拼出，不入库；内置 Skill 为 p_{code}，网关 Skill 为 g_{网关名}_{code}"""
        if self.type == SkillTypeEnum.GATEWAY.value:
            return f"{SKILL_ID_PREFIXES[self.type]}{self.gateway.name}_{self.code}"
        return f"{SKILL_ID_PREFIXES[self.type]}{self.code}"


class SkillConfig(TimestampedModelMixin, OperatorModelMixin):
    """Skill 编排草稿，与 metadata 一对一，发版时复制到 SkillVersion"""

    metadata = models.OneToOneField(SkillMetadata, on_delete=models.CASCADE, related_name="config")
    orchestration = models.JSONField(default=dict, help_text=_("编排内容"))

    def __str__(self):
        return f"<SkillConfig: {self.pk}/{self.metadata_id}>"

    class Meta:
        verbose_name = _("Skill 编排")
        verbose_name_plural = _("Skill 编排")
        db_table = "skill_config"


class SkillVersion(TimestampedModelMixin, OperatorModelMixin):
    """Skill 的一次发版；version、changelog、orchestration、artifact 创建后不再修改

    artifact: {"SKILL.md": "<正文>"}，键为包内相对路径，值为冻结的正文（含一级标题，不含 frontmatter）
    """

    metadata = models.ForeignKey(SkillMetadata, on_delete=models.CASCADE, related_name="versions")
    version = models.CharField(max_length=SKILL_VERSION_MAX_LENGTH, help_text=_("版本号"))
    changelog = models.TextField(blank=True, default="", help_text=_("版本说明"))
    orchestration = models.JSONField(default=dict, help_text=_("发版时的编排内容"))
    artifact = models.JSONField(default=dict, help_text=_("冻结的 Skill 包文件内容"))

    def __str__(self):
        return f"<SkillVersion: {self.pk}/{self.metadata_id}/{self.version}>"

    class Meta:
        verbose_name = _("Skill 版本")
        verbose_name_plural = _("Skill 版本")
        db_table = "skill_version"
        unique_together = ("metadata", "version")


class SkillVersionRelation(models.Model):
    """从某一版 steps[].calls 拆出的网关名、资源名，按 (gateway_name, resource_name) 去重，供检索"""

    metadata = models.ForeignKey(SkillMetadata, on_delete=models.CASCADE)
    version = models.ForeignKey(SkillVersion, on_delete=models.CASCADE, related_name="relations")
    gateway_name = models.CharField(max_length=64, help_text=_("网关名"))
    resource_name = models.CharField(max_length=256, help_text=_("资源名"))

    def __str__(self):
        return f"<SkillVersionRelation: {self.pk}/{self.version_id}/{self.gateway_name}/{self.resource_name}>"

    class Meta:
        verbose_name = _("Skill 版本关联资源")
        verbose_name_plural = _("Skill 版本关联资源")
        db_table = "skill_version_relation"
        unique_together = ("version", "gateway_name", "resource_name")
        indexes = [
            models.Index(fields=["gateway_name", "resource_name"]),
            models.Index(fields=["resource_name"]),
        ]
