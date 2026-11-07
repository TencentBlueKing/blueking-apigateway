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

from typing import Optional

from django.db import models
from django.utils.translation import gettext_lazy as _

from apigateway.common.i18n.field import I18nProperty
from apigateway.common.mixins.models import OperatorModelMixin, TimestampedModelMixin
from apigateway.core.models import Gateway

from .constants import (
    SKILL_CODE_MAX_LENGTH,
    SKILL_DESCRIPTION_MAX_LENGTH,
    SKILL_DISPLAY_NAME_MAX_LENGTH,
    SKILL_ID_PREFIXES,
    SKILL_NAME_MAX_LENGTH,
    SKILL_TAG_NAME_MAX_LENGTH,
    SKILL_VERSION_MAX_LENGTH,
    SkillStatusEnum,
    SkillTypeEnum,
)
from .deletion import restrict_current_version


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
    """Skill 元数据，code 为对外 ID，新建时由 build_code() 拼出"""

    # 内置 Skill 的 gateway 为 NULL，MySQL 唯一索引不把多个 NULL 视为重复，(type, gateway, name) 拦不住
    # 同名的内置 Skill，所以把对外 ID 存下来并加唯一约束。name 不含下划线，能从 code 无歧义地拆出网关名。
    code = models.CharField(max_length=SKILL_CODE_MAX_LENGTH, unique=True, help_text=_("对外 ID"))
    type = models.CharField(max_length=16, choices=SkillTypeEnum.get_choices(), help_text=_("Skill 来源类型"))
    gateway = models.ForeignKey(
        Gateway,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text=_("所属网关，内置 Skill 为空"),
    )
    name = models.CharField(max_length=SKILL_NAME_MAX_LENGTH, help_text=_("Skill 名称，即 SKILL.md 的 name"))
    display_name_i18n = I18nProperty(
        models.CharField(max_length=SKILL_DISPLAY_NAME_MAX_LENGTH, help_text=_("Skill 展示名"))
    )
    display_name = display_name_i18n.default_field()
    display_name_en = display_name_i18n.field("en", null=True, default=None)
    description = models.CharField(max_length=SKILL_DESCRIPTION_MAX_LENGTH, help_text=_("Skill 描述"))
    metadata = models.JSONField(default=dict, blank=True, help_text=_("扩展元数据"))
    status = models.CharField(
        max_length=16,
        choices=SkillStatusEnum.get_choices(),
        default=SkillStatusEnum.UNPUBLISHED.value,
        help_text=_("Skill 状态"),
    )
    # 用 QuerySet.update(F() + 1) 累加，不经过 save()，避免刷新 updated_time。
    # 其他写入需用 save(update_fields=...)，否则旧实例的整行保存会把并发累加的值写回旧值。
    download_count = models.PositiveIntegerField(default=0, help_text=_("下载数"))

    # 被引用的版本不能单独删除。删 metadata（含随网关级联）时引用方在同一批里，先置空再删版本。
    # 不用 RESTRICT：它和 versions 的 CASCADE 构成删除顺序环，MySQL 报 1451。不用 PROTECT：删 metadata 会 ProtectedError。
    # 必须指向本 Skill 的版本；指向其他 Skill 的版本会让那个 Skill（及其网关）删除时报 RestrictedError。
    current_version = models.ForeignKey(
        "SkillVersion",
        on_delete=restrict_current_version,
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
        unique_together = ("type", "gateway", "name")

    @staticmethod
    def build_code(type: str, gateway_name: Optional[str], name: str) -> str:
        """内置 Skill 为 p_{name}，网关 Skill 为 g_{网关名}_{name}"""
        if type == SkillTypeEnum.GATEWAY.value:
            return f"{SKILL_ID_PREFIXES[type]}{gateway_name}_{name}"
        return f"{SKILL_ID_PREFIXES[type]}{name}"


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
    version = models.CharField(max_length=SKILL_VERSION_MAX_LENGTH, help_text=_("版本号，保存时转为小写"))
    changelog = models.TextField(blank=True, default="", help_text=_("版本说明"))
    orchestration = models.JSONField(default=dict, help_text=_("发版时的编排内容"))
    artifact = models.JSONField(default=dict, help_text=_("冻结的 Skill 包文件内容"))

    def save(self, *args, **kwargs):
        self.version = self.version.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"<SkillVersion: {self.pk}/{self.metadata_id}/{self.version}>"

    class Meta:
        verbose_name = _("Skill 版本")
        verbose_name_plural = _("Skill 版本")
        db_table = "skill_version"
        unique_together = ("metadata", "version")


class SkillVersionRelation(models.Model):
    """从某一版 steps[].calls 拆出的网关名、资源名，按 (gateway_name, resource_name) 去重，供检索

    metadata 是用于直接按 Skill 检索的冗余外键，写入时必须取自 version.metadata_id。
    """

    metadata = models.ForeignKey(SkillMetadata, on_delete=models.CASCADE, related_name="version_relations")
    version = models.ForeignKey(SkillVersion, on_delete=models.CASCADE, related_name="relations")
    gateway_name = models.CharField(max_length=64, help_text=_("网关名"))
    resource_name = models.CharField(max_length=256, help_text=_("资源名"))

    def __str__(self):
        return f"<SkillVersionRelation: {self.pk}/{self.version_id}/{self.gateway_name}/{self.resource_name}>"

    class Meta:
        verbose_name = _("Skill 版本关联资源")
        verbose_name_plural = _("Skill 版本关联资源")
        db_table = "skill_version_relation"
        unique_together = ("gateway_name", "resource_name", "version")
        indexes = [
            models.Index(fields=["resource_name"]),
        ]
