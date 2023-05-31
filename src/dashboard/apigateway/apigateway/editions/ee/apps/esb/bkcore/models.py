# -*- coding: utf-8 -*-
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
import datetime
import operator
from typing import List, Optional

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from jsonfield import JSONField
from tencent_apigateway_common.i18n.field import I18nProperty

from apigateway.apps.esb.bkcore import managers
from apigateway.apps.esb.constants import ComponentDocTypeEnum, DataTypeEnum, LanguageEnum
from apigateway.apps.permission.constants import ApplyStatusEnum, PermissionApplyExpireDaysEnum, PermissionLevelEnum
from apigateway.apps.permission.models import generate_expire_time
from apigateway.common.mixins.models import OperatorModelMixin, TimestampedModelMixin
from apigateway.core.constants import ReleaseStatusEnum
from apigateway.utils.time import NeverExpiresTime


class ModelWithBoard(models.Model):

    board = models.CharField(max_length=64, default="default", blank=True, db_index=True)

    class Meta:
        abstract = True


class ComponentSystem(ModelWithBoard, TimestampedModelMixin, OperatorModelMixin):
    """系统"""

    name = models.CharField(max_length=64, db_index=True)
    description_i18n = I18nProperty(models.CharField(max_length=128))
    description = description_i18n.default_field()
    description_en = description_i18n.field("en", default=None, blank=True, null=True)

    comment_i18n = I18nProperty(models.TextField(default="", blank=True))
    comment = comment_i18n.default_field()
    comment_en = comment_i18n.field("en", default=None, blank=True, null=True)

    timeout = models.IntegerField(null=True, blank=True, help_text=_("单位秒"))
    data_type = models.IntegerField(default=3, db_index=True)
    _maintainers = models.CharField(db_column="maintainers", max_length=1024, default="", blank=True)

    objects = managers.ComponentSystemManager()

    def __str__(self):
        return f"<System: {self.name}>"

    class Meta:
        unique_together = ("board", "name")
        db_table = "esb_component_system"

    @property
    def maintainers(self) -> List[str]:
        if not self._maintainers:
            return []
        return self._maintainers.split(";")

    @maintainers.setter
    def maintainers(self, data: List[str]):
        self._maintainers = ";".join(data)

    @property
    def is_official(self):
        return DataTypeEnum(self.data_type).is_official


class ESBChannel(ModelWithBoard, TimestampedModelMixin, OperatorModelMixin):
    """Channel for ESB

    One channel links a path to a component
    """

    system = models.ForeignKey(ComponentSystem, on_delete=models.PROTECT)
    name = models.CharField(max_length=128, default="", blank=True, help_text=_("组件API英文名"))
    description_i18n = I18nProperty(models.CharField(max_length=128))
    description = description_i18n.default_field()
    description_en = description_i18n.field("en", default=None, blank=True, null=True)

    method = models.CharField(_("请求方法"), max_length=32, default="", blank=True)
    path = models.CharField(_("请求路径"), max_length=255)
    component_codename = models.CharField(_("组件类代号"), max_length=255)
    permission_level = models.CharField(max_length=32, choices=PermissionLevelEnum.get_django_choices())
    verified_user_required = models.BooleanField(default=True)
    timeout = models.IntegerField(null=True, blank=True, help_text=_("单位秒"))
    config = JSONField(default=dict, dump_kwargs={"indent": None}, blank=True)
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=True)
    data_type = models.IntegerField(default=3, db_index=True)

    objects = managers.ESBChannelManager()

    def __str__(self):
        return f"<ESBChannel: {self.id}/{self.name}>"

    class Meta:
        unique_together = ("board", "method", "path")
        db_table = "esb_channel"

    @property
    def is_official(self):
        return DataTypeEnum(self.data_type).is_official

    @property
    def api_path(self):
        return "/api/c/compapi/%s/" % self.path.strip("/")


class ESBChannelExtend(ModelWithBoard):
    component = models.OneToOneField(ESBChannel, on_delete=models.CASCADE)
    config_fields = JSONField(null=True, blank=True, dump_kwargs={"indent": None})

    objects = managers.ESBChannelExtendManager()

    def __str__(self):
        return f"<ESBChannelExtend: {self.component.name}>"

    class Meta:
        db_table = "esb_channel_extend"


class ComponentResourceBinding(ModelWithBoard):
    """组件与网关资源绑定关系，如果组件在 ESBChannel 中存在，则使用组件ID，否则使用 method+path 表示"""

    component_id = models.IntegerField(default=0)
    component_method = models.CharField(max_length=32, default="", blank=True)
    component_path = models.CharField(max_length=255, default="", blank=True)
    resource_id = models.IntegerField(_("网关资源 ID"), unique=True)

    objects = managers.ComponentResourceBindingManager()

    def __str__(self):
        return f"<ComponentResourceBinding: {self.component_id}/{self.resource_id}>"

    class Meta:
        db_table = "esb_component_resource_binding"

    @property
    def component_key(self) -> Optional[str]:
        if self.component_id:
            return str(self.component_id)
        elif self.component_path:
            return f"{self.component_method}:{self.component_path}"

        return None


class AppComponentPermission(ModelWithBoard, TimestampedModelMixin):
    """蓝鲸应用的组件API权限"""

    bk_app_code = models.CharField(_("蓝鲸应用编码"), max_length=64)
    component_id = models.IntegerField(_("组件API ID"))
    expires = models.DateTimeField(default=generate_expire_time)

    objects = managers.AppComponentPermissionManager()

    def __str__(self):
        return f"<AppComponentPermission: {self.bk_app_code}/{self.component_id}>"

    class Meta:
        db_table = "esb_app_component_permission"
        unique_together = ("board", "bk_app_code", "component_id")

    @property
    def expires_in(self) -> Optional[int]:
        """返回过期时间"""
        if self.expires:
            return int((self.expires - timezone.now()).total_seconds())

        return None

    @property
    def expires_display(self) -> Optional[datetime.datetime]:
        if NeverExpiresTime.is_never_expired(self.expires):
            return None

        return self.expires


class AppPermissionApplyRecord(ModelWithBoard, TimestampedModelMixin):
    bk_app_code = models.CharField(max_length=32, db_index=True)
    applied_by = models.CharField(max_length=32)
    applied_time = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=512, blank=True, default="")
    expire_days = models.IntegerField(default=PermissionApplyExpireDaysEnum.SIX_MONTH.value)
    handled_by = models.CharField(max_length=32, blank=True, default="")
    handled_time = models.DateTimeField(blank=True, null=True)
    system = models.ForeignKey(ComponentSystem, on_delete=models.CASCADE)
    _component_ids = models.TextField(db_column="component_ids")
    handled_component_ids = JSONField(default=dict, dump_kwargs={"indent": None}, blank=True)
    status = models.CharField(max_length=16, choices=ApplyStatusEnum.get_choices(), db_index=True)
    comment = models.CharField(max_length=512, blank=True, default="")

    objects = managers.AppPermissionApplyRecordManager()

    def __str__(self):
        return f"<AppPermissionApplyRecord: {self.id}>"

    class Meta:
        verbose_name = _("APP申请ESB组件权限单据")
        verbose_name_plural = _("APP申请ESB组件权限单据")
        db_table = "esb_app_permission_apply_record"

    @property
    def component_ids(self) -> List[int]:
        if not self._component_ids:
            return []
        return [int(i) for i in self._component_ids.split(";")]

    @component_ids.setter
    def component_ids(self, data: List[int]):
        self._component_ids = ";".join([str(i) for i in data])

    @property
    def apply_status(self):
        return self.status

    @property
    def system_name(self):
        return self.system.name

    @property
    def components(self):
        components = ESBChannel.objects.get_component_map_by_ids(self.component_ids).values()

        # enrich components
        component_apply_status_map = self.get_component_apply_status_map()
        for component in components:
            component["apply_status"] = component_apply_status_map[component["id"]]

        return sorted(components, key=operator.itemgetter("apply_status", "name"))

    def get_component_apply_status_map(self):
        if self.handled_component_ids:
            return {
                component_id: status
                for status, component_ids in self.handled_component_ids.items()
                for component_id in component_ids
            }

        return {component_id: self.status for component_id in self.component_ids}


class AppPermissionApplyStatus(ModelWithBoard, TimestampedModelMixin):
    """
    应用访问资源权限申请状态：申请中
    """

    record = models.ForeignKey(AppPermissionApplyRecord, on_delete=models.CASCADE, blank=True, null=True)
    bk_app_code = models.CharField(max_length=32, db_index=True)
    system = models.ForeignKey(ComponentSystem, on_delete=models.CASCADE)
    component = models.ForeignKey(ESBChannel, on_delete=models.CASCADE)
    status = models.CharField(max_length=16, choices=ApplyStatusEnum.get_choices())

    objects = managers.AppPermissionApplyStatusManager()

    def __str__(self):
        return f"<AppPermissionApplyStatus: {self.id}>"

    class Meta:
        verbose_name = _("APP访问组件API权限申请状态")
        verbose_name_plural = _("APP访问组件API权限申请状态")
        unique_together = ("board", "bk_app_code", "system", "component")
        db_table = "esb_app_permission_apply_status"


class ComponentDoc(ModelWithBoard, TimestampedModelMixin):

    component = models.ForeignKey(ESBChannel, on_delete=models.CASCADE)
    language = models.CharField(max_length=32, choices=LanguageEnum.get_django_choices())
    content = models.TextField(blank=True, default="")
    content_md5 = models.CharField(max_length=128, default="", blank=True)

    objects = managers.ComponentDocManager()

    def __str__(self):
        return f"<ComponentDoc: {self.component_id}>"

    class Meta:
        verbose_name = _("组件API文档")
        verbose_name_plural = _("组件API文档")
        db_table = "esb_component_doc"
        unique_together = ("board", "component", "language")

    @property
    def doc_configs(self):
        component = self.component
        return {
            "doc_type": ComponentDocTypeEnum.MARKDOWN.value,
            "api_path": component.api_path,
            "suggest_method": component.config.get("suggest_method") or component.method,
        }


class ComponentReleaseHistory(ModelWithBoard, TimestampedModelMixin, OperatorModelMixin):
    """记录组件同步到网关的数据，及同步数据、发布网关版本的状态"""

    resource_version_id = models.IntegerField(_("资源版本ID"), db_index=True)
    data = JSONField(help_text="component sync data")

    comment = models.CharField(max_length=512, blank=True, default="")
    status = models.CharField(
        _("发布状态"),
        max_length=16,
        choices=ReleaseStatusEnum.choices(),
        default=ReleaseStatusEnum.PENDING.value,
    )
    message = models.TextField(blank=True, default="")

    objects = managers.ComponentReleaseHistoryManager()

    class Meta:
        verbose_name = _("组件同步网关及发布历史")
        verbose_name_plural = _("组件同步网关及发布历史")
        db_table = "esb_component_release_history"


class DocCategory(ModelWithBoard, TimestampedModelMixin, OperatorModelMixin):
    """文档分类"""

    name_i18n = I18nProperty(models.CharField(max_length=32))
    name = name_i18n.default_field(db_index=True)
    name_en = name_i18n.field("en", default=None, blank=True, null=True)
    priority = models.IntegerField(default=1000, help_text=_("数字大优先级高"))
    data_type = models.IntegerField(default=3, db_index=True)

    objects = managers.DocCategoryManager()

    def __str__(self):
        return f"<DocCategory: {self.name}>"

    class Meta:
        verbose_name = _("文档分类")
        verbose_name_plural = _("文档分类")
        unique_together = ("board", "name")
        db_table = "esb_doc_category"

    @property
    def is_official(self):
        return DataTypeEnum(self.data_type).is_official


class SystemDocCategory(ModelWithBoard, TimestampedModelMixin, OperatorModelMixin):
    doc_category = models.ForeignKey(DocCategory, on_delete=models.PROTECT)
    system = models.OneToOneField(ComponentSystem, on_delete=models.PROTECT)

    objects = managers.SystemDocCategoryManager()

    def __str__(self):
        return "<SystemDocCategory: {self.doc_category_id}/{self.system_id}>"

    class Meta:
        db_table = "esb_system_doc_category"


class FunctionController(ModelWithBoard, TimestampedModelMixin):
    """功能开关控制器"""

    func_code = models.CharField(_("功能code"), max_length=64)
    func_name = models.CharField(_("功能名称"), max_length=64)
    func_desc = models.TextField(_("功能描述"), default="", blank=True)
    switch_status = models.BooleanField(_("是否开启"), default=True)
    wlist = models.TextField(
        _("功能测试白名单"),
        default="",
        blank=True,
        help_text=_("支持两种格式数据，以逗号、分号分隔的字符串，及JSON格式字符串"),
    )

    objects = managers.FunctionControllerManager()

    def __str__(self):
        return f"<FunctionController: {self.board}/{self.func_code}>"

    class Meta:
        db_table = "esb_function_controller"
        unique_together = ("board", "func_code")


class AccessToken(TimestampedModelMixin):
    bk_app_code = models.CharField(_("蓝鲸应用编码"), max_length=128)
    user_id = models.CharField(max_length=64)
    access_token = models.CharField(max_length=255)
    expires = models.DateTimeField()

    class Meta:
        db_table = "esb_access_token"
        unique_together = ("bk_app_code", "user_id")


class AppAccount(models.Model):
    """应用帐号"""

    app_code = models.CharField(_("蓝鲸应用编码"), max_length=30, unique=True)
    app_token = models.CharField(_("应用Token"), max_length=128)
    introduction = models.TextField(default="", blank=True)
    created_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"<AppAccount: {self.app_code}>"

    class Meta:
        db_table = "esb_app_account"


class WxmpAccessToken(models.Model):
    """保存微信开放平台业务的 AccessToken"""

    wx_app_id = models.CharField(_("微信APPID"), max_length=128)
    access_token = models.CharField(_("凭证"), max_length=1024)
    expires = models.DateTimeField(_("凭证过期时间"))
    last_updated_time = models.DateTimeField(_("最后访问时间"), default=timezone.now)

    def __str__(self):
        return f"<WxmpAccessToken: {self.wx_app_id}>"

    class Meta:
        db_table = "esb_wxmp_access_token"
        verbose_name = _("微信公众号AccessToken")
        verbose_name_plural = _("微信公众号AccessToken")


class RealTimelineEvent(ModelWithBoard, TimestampedModelMixin):
    """实时 timeline 事件"""

    # 此模型属于运行数据(status)，为避免新增 dbrouter，统一将模型定义放到 bkcore

    system_name = models.CharField(max_length=32)
    type = models.CharField(_("事件类型"), max_length=64)
    data = JSONField()
    ts_happened_at = models.FloatField(_("事件时间戳"))

    class Meta:
        unique_together = ("board", "system_name", "ts_happened_at")
        db_table = "esb_real_timeline_event"

    def as_dict(self):
        return {
            "system_name": self.system_name,
            "type": self.type,
            "data": self.data,
            "mts": int(self.ts_happened_at * 1000),
        }
