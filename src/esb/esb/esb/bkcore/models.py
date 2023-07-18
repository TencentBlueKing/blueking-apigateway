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
import json
import operator
from typing import List, Optional

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext as _
from jsonfield import JSONField
from tencent_apigateway_common.i18n.field import I18nProperty

from common.mixins.models import OperatorModelMixin, TimestampedModelMixin
from esb.bkcore import managers
from esb.bkcore.constants import DataTypeEnum, PermissionLevelEnum


def generate_expire_time() -> datetime.datetime:
    return timezone.now() + datetime.timedelta(days=180)


class ModelWithBoard(models.Model):

    board = models.CharField(max_length=64, default="default", blank=True, db_index=True)

    class Meta:
        abstract = True


class System(ModelWithBoard, TimestampedModelMixin, OperatorModelMixin):
    """系统"""

    name = models.CharField("名称", max_length=64, db_index=True)
    description_i18n = I18nProperty(models.CharField("描述", max_length=128))
    description = description_i18n.default_field()
    description_en = description_i18n.field("en", default=None, blank=True, null=True)
    comment_i18n = I18nProperty(models.TextField("备注", default="", blank=True))
    comment = comment_i18n.default_field()
    comment_en = comment_i18n.field("en", default=None, blank=True, null=True)
    timeout = models.IntegerField("超时时长", null=True, blank=True, help_text="单位秒")
    data_type = models.IntegerField(default=3, db_index=True)
    _maintainers = models.CharField(db_column="maintainers", max_length=1024, default="", blank=True)

    objects = managers.SystemManager()

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

    @property
    def description_display(self):
        if self.is_official:
            return _(self.description)
        return self.description

    @property
    def comment_display(self):
        if self.is_official:
            return _(self.comment)
        return self.comment


class ESBChannel(ModelWithBoard, TimestampedModelMixin, OperatorModelMixin):
    """Channel for ESB

    One channel links a path to a component
    """

    system = models.ForeignKey(System, on_delete=models.PROTECT)
    name = models.CharField("名称", max_length=128, default="", blank=True, help_text="组件API英文名")
    description_i18n = I18nProperty(models.CharField("描述", max_length=128))
    description = description_i18n.default_field()
    description_en = description_i18n.field("en", default=None, blank=True, null=True)

    method = models.CharField("请求方法", max_length=32, default="", blank=True)
    path = models.CharField("请求路径", max_length=255)
    component_codename = models.CharField("组件类代号", max_length=255)
    permission_level = models.CharField("权限级别", max_length=32)
    verified_user_required = models.BooleanField(default=True)
    timeout = models.IntegerField("超时时长", null=True, blank=True, help_text="单位秒")
    config = JSONField(default=dict, dump_kwargs={"indent": None}, blank=True)
    is_active = models.BooleanField("是否开启", default=True)
    is_public = models.BooleanField("是否公开", default=True)
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
    def is_confapi(self):
        return self.config.get("is_confapi", False)

    @property
    def api_path(self):
        return "/api/c/compapi/%s/" % self.path.strip("/")

    @property
    def api_version(self):
        if self.component_codename.startswith("generic.v2."):
            return "v2"
        return ""

    @property
    def component_permission_required(self):
        return self.permission_level != PermissionLevelEnum.UNLIMITED.value

    @property
    def channel_conf(self):
        return {
            "id": self.id,
            "permission_level": self.permission_level,
        }

    @property
    def comp_conf(self):
        """兼容组件 weixin.get_token 对老版本数据的使用方式"""
        return json.dumps(self.config or {})

    @property
    def description_display(self):
        if self.is_official:
            return _(self.description)
        return self.description

    def get_real_timeout(self, system_timeout: Optional[int]) -> int:
        if self.timeout:
            return self.timeout

        # 通过参数获取系统的超时时间，优化查询性能
        if system_timeout:
            return system_timeout

        return settings.REQUEST_TIMEOUT_SECS


class ESBChannelExtend(ModelWithBoard):
    component = models.OneToOneField(ESBChannel, on_delete=models.CASCADE)
    config_fields = JSONField(null=True, blank=True, dump_kwargs={"indent": None})

    objects = managers.ESBChannelExtendManager()

    def __str__(self):
        return f"<ESBChannelExtend: {self.component.name}>"

    class Meta:
        db_table = "esb_channel_extend"


class AppComponentPermission(ModelWithBoard, TimestampedModelMixin):
    """蓝鲸应用的组件API权限"""

    bk_app_code = models.CharField("蓝鲸应用编码", max_length=64)
    component_id = models.IntegerField("组件API ID")
    expires = models.DateTimeField("APP访问组件API的过期时间", default=generate_expire_time)

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


class AppPermissionApplyRecord(ModelWithBoard, TimestampedModelMixin):
    bk_app_code = models.CharField(max_length=32, db_index=True)
    applied_by = models.CharField(max_length=32)
    applied_time = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=512, blank=True, default="")
    expire_days = models.IntegerField(default=180)
    handled_by = models.CharField(max_length=32, blank=True, default="")
    handled_time = models.DateTimeField(blank=True, null=True)
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    _component_ids = models.TextField(db_column="component_ids")
    handled_component_ids = JSONField(default=dict, dump_kwargs={"indent": None}, blank=True)
    status = models.CharField(max_length=16, db_index=True)
    comment = models.CharField(max_length=512, blank=True, default="")

    objects = managers.AppPermissionApplyRecordManager()

    def __str__(self):
        return f"<AppPermissionApplyRecord: {self.id}>"

    class Meta:
        verbose_name = "APP申请ESB组件权限单据"
        verbose_name_plural = "APP申请ESB组件权限单据"
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
        components = ESBChannel.objects.get_components(ESBChannel.objects.filter(id__in=self.component_ids))

        # enrich components
        component_apply_status_map = self._get_component_apply_status()
        for component in components:
            component["apply_status"] = component_apply_status_map[component["id"]]

        return sorted(components, key=operator.itemgetter("name"))

    def _get_component_apply_status(self):
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
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    component = models.ForeignKey(ESBChannel, on_delete=models.CASCADE)
    status = models.CharField(max_length=16)

    objects = managers.AppPermissionApplyStatusManager()

    def __str__(self):
        return f"<AppPermissionApplyStatus: {self.id}>"

    class Meta:
        verbose_name = "APP访问组件API权限申请状态"
        verbose_name_plural = "APP访问组件API权限申请状态"
        unique_together = ("board", "bk_app_code", "system", "component")
        db_table = "esb_app_permission_apply_status"


class ComponentDoc(ModelWithBoard, TimestampedModelMixin):

    component = models.ForeignKey(ESBChannel, on_delete=models.CASCADE)
    language = models.CharField(max_length=32)
    content = models.TextField(blank=True, default="")
    content_md5 = models.CharField(max_length=128, default="", blank=True)

    def __str__(self):
        return f"<ComponentDoc: {self.component_id}>"

    class Meta:
        verbose_name = "组件API文档"
        verbose_name_plural = "组件API文档"
        db_table = "esb_component_doc"
        unique_together = ("board", "component", "language")


class DocCategory(ModelWithBoard, TimestampedModelMixin, OperatorModelMixin):
    """文档分类"""

    name_i18n = I18nProperty(models.CharField("名称", max_length=32))
    name = name_i18n.default_field(db_index=True)
    name_en = name_i18n.field("en", default=None, blank=True, null=True)
    priority = models.IntegerField("优先级", default=1000, help_text="数字小优先级越高")
    data_type = models.IntegerField(default=3, db_index=True)

    objects = managers.DocCategoryManager()

    def __str__(self):
        return f"<DocCategory: {self.name}>"

    class Meta:
        verbose_name = "文档分类"
        verbose_name_plural = "文档分类"
        unique_together = ("board", "name")
        db_table = "esb_doc_category"

    @property
    def is_official(self):
        return DataTypeEnum(self.data_type).is_official


class SystemDocCategory(ModelWithBoard, TimestampedModelMixin, OperatorModelMixin):
    doc_category = models.ForeignKey(DocCategory, on_delete=models.PROTECT)
    system = models.OneToOneField(System, on_delete=models.PROTECT)

    objects = managers.SystemDocCategoryManager()

    def __str__(self):
        return "<SystemDocCategory: {self.doc_category_id}/{self.system_id}>"

    class Meta:
        db_table = "esb_system_doc_category"


class FunctionController(ModelWithBoard, TimestampedModelMixin):
    """功能开关控制器"""

    func_code = models.CharField("功能code", max_length=64)
    func_name = models.CharField("功能名称", max_length=64)
    func_desc = models.TextField("功能描述", default="", blank=True)
    switch_status = models.BooleanField("是否开启", default=True)
    wlist = models.TextField(
        "功能测试白名单",
        default="",
        blank=True,
        help_text="支持两种格式数据，以逗号、分号分隔的字符串，及JSON格式字符串",
    )

    def __str__(self):
        return f"<FunctionController: {self.board}/{self.func_code}>"

    class Meta:
        db_table = "esb_function_controller"
        unique_together = ("board", "func_code")


class AccessToken(TimestampedModelMixin):
    bk_app_code = models.CharField("蓝鲸智云应用编码", max_length=128)
    user_id = models.CharField("用户标识", max_length=64)
    access_token = models.CharField("token内容", max_length=255)
    expires = models.DateTimeField("token过期时间")

    class Meta:
        db_table = "esb_access_token"
        unique_together = ("bk_app_code", "user_id")

    def expires_in(self):
        """返回该token还有多少秒过期"""
        return int((self.expires - timezone.now()).total_seconds())

    def has_expired(self):
        return self.expires_in() <= 0


class AppAccount(models.Model):
    """应用账号"""

    app_code = models.CharField("应用编码", max_length=30, unique=True)
    app_token = models.CharField("应用Token", max_length=128)
    introduction = models.TextField("应用简介", default="", blank=True)
    created_time = models.DateTimeField("创建时间", auto_now_add=True)

    def __str__(self):
        return f"<AppAccount: {self.app_code}>"

    class Meta:
        db_table = "esb_app_account"


class WxmpAccessToken(models.Model):
    """保存微信开放平台业务的 AccessToken"""

    wx_app_id = models.CharField("微信APPID", max_length=128)
    access_token = models.CharField("凭证", max_length=1024)
    expires = models.DateTimeField("凭证过期时间")
    last_updated_time = models.DateTimeField("最后访问时间", default=timezone.now)

    def __str__(self):
        return f"<WxmpAccessToken: {self.wx_app_id}>"

    class Meta:
        db_table = "esb_wxmp_access_token"
        verbose_name = "微信公众号AccessToken"
        verbose_name_plural = "微信公众号AccessToken"

    def touch(self):
        self.last_updated_time = timezone.now()

    def has_expired(self):
        return self.expires_in() < 300

    def expires_in(self):
        """返回该token还有多少秒过期"""
        return int((self.expires - timezone.now()).total_seconds())

    def get_info(self):
        return {
            "access_token": self.access_token,
            "expires_in": self.expires_in(),
        }
