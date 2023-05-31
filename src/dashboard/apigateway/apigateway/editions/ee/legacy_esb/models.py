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
import abc
import datetime
import hashlib
import json
import re
import urllib
from typing import Any, Dict, List, Optional

from django.db import models
from django.utils import timezone
from django.utils.encoding import force_bytes

from apigateway.apps.esb.constants import DataTypeEnum
from apigateway.apps.permission.constants import PermissionLevelEnum
from apigateway.core.constants import HTTP_METHOD_ANY, LoadBalanceTypeEnum, ProxyTypeEnum
from apigateway.legacy_esb.constants import BK_SYSTEMS, SystemDocCategoryEnum
from apigateway.legacy_esb.managers import SystemDocCategoryManager

# NOTE: 旧版本模型定义，仅支持旧版数据迁移，禁止其它包依赖此模块


_MAX_DOC_CATEGORY_PRIORITY = 9000
_MAX_APIGATEWAY_TIMEOUT = 600


# 需与 django Model 共用，因 metaclass 冲突，不能指定 metaclass=abc.ABCMeta
class LegacyModelMigrator:
    @abc.abstractmethod
    def clone_to_ng_obj(self) -> models.Model:
        """根据旧版对象克隆一个新版对象"""
        raise NotImplementedError

    @abc.abstractmethod
    def update_ng_obj_fields(self, ng_obj: models.Model) -> models.Model:
        """根据旧版对象更新新版对象"""
        raise NotImplementedError

    @abc.abstractmethod
    def is_changed(self, ng_obj: models.Model) -> bool:
        """新、旧版本对比，检查数据是否更新"""
        raise NotImplementedError

    def has_different_field_value(self, src_obj: Any, dst_obj: Any, fields: List[str]) -> bool:
        for field in fields:
            if getattr(src_obj, field) != getattr(dst_obj, field):
                return True

        return False


def _convert_is_official_to_data_type(is_official: bool) -> int:
    """将配置 is_official 转换为 data_type"""
    # 此转换策略，仅针对数据迁移，不具有普适性，因此未放到 DataTypeEnum 定义中
    if is_official:
        return DataTypeEnum.OFFICIAL_PUBLIC.value
    return DataTypeEnum.CUSTOM.value


class ComponentSystem(LegacyModelMigrator, models.Model):
    """组件系统"""

    name = models.CharField("系统名称", max_length=64)
    description = models.CharField("系统标签", db_column="label", max_length=128, help_text="系统简要说明")
    component_admin = models.CharField("组件开发负责人", max_length=128, default="", blank=True)
    interface_admin = models.CharField("系统接口负责人", max_length=128, default="", blank=True)
    system_link = models.CharField("系统链接", max_length=1024, default="", blank=True, help_text="标准的HTTP链接，多个以分号分隔")
    belong_to = models.CharField("系统所属组织", max_length=128, default="", blank=True)
    comment = models.TextField("备注", db_column="remark", default="", blank=True)
    execute_timeout = models.IntegerField("执行类超时时长", null=True, blank=True, help_text="单位秒，未设置时超时时长为30秒")
    query_timeout = models.IntegerField("查询类超时时长", null=True, blank=True, help_text="单位秒，未设置时超时时长为30秒")
    doc_category_id = models.IntegerField("文档分类ID", null=True, blank=True)

    class Meta:
        db_table = "esb_component_system"

    def __str__(self):
        return self.name

    def clone_to_ng_obj(self):
        from apigateway.apps.esb.bkcore.models import ComponentSystem as NGComponentSystem

        return NGComponentSystem(
            id=self.id,
            name=self.name,
            description=self.description,
            comment=self.comment,
            timeout=self.timeout,
            data_type=self.data_type,
            _maintainers=";".join(self.maintainers),
        )

    def update_ng_obj_fields(self, ng_obj):
        ng_obj.__dict__.update(
            {
                "name": self.name,
                "description": self.description,
                "comment": self.comment,
                "timeout": self.timeout,
                "data_type": self.data_type,
                "_maintainers": ";".join(self.maintainers),
            }
        )
        return ng_obj

    def is_changed(self, ng_obj):
        return self.has_different_field_value(
            self,
            ng_obj,
            fields=[
                "name",
                "description",
                "comment",
                "timeout",
                "maintainers",
            ],
        )

    @property
    def is_official(self):
        return self.name in BK_SYSTEMS

    @property
    def data_type(self) -> int:
        return _convert_is_official_to_data_type(self.is_official)

    @property
    def timeout(self) -> Optional[int]:
        if self.query_timeout and self.execute_timeout:
            return max(self.query_timeout, self.execute_timeout)

        return None

    @property
    def maintainers(self):
        maintainers = re.findall(r"[^,; ]+", f"{self.component_admin};{self.interface_admin}")
        return sorted(list(set(maintainers)), key=maintainers.index)


class ESBChannel(LegacyModelMigrator, models.Model):
    """Channel for ESB

    One channel links a path to a component
    """

    TYPE_CHOICE = (
        (1, "执行API"),
        (2, "查询API"),
    )
    PERM_LEVEL_CHOICE = (
        (0, "无限制"),
        (1, "普通权限"),
        (2, "敏感权限"),
        (3, "特殊权限"),
    )

    description = models.CharField("通道名称", db_column="name", max_length=64, help_text='通道名称，长度限制为64字符，例如"查询服务器列表"')
    path = models.CharField("通道路径", max_length=255, help_text='通道请求路径，例如"/host/get_host_list/"')
    method = models.CharField("请求类型", max_length=32, null=True, default="", blank=True)
    component_system = models.ForeignKey(ComponentSystem, verbose_name="所属组件系统", null=True, on_delete=models.PROTECT)
    component_codename = models.CharField("对应组件代号", max_length=255, help_text='组件代号，例如 "generic.host.get_host_list"')
    name = models.CharField("组件英文名", db_column="component_name", max_length=64, default="", blank=True, null=True)
    is_active = models.BooleanField("是否开启", default=True)
    last_modified_time = models.DateTimeField("最后更新", auto_now=True)
    created_time = models.DateTimeField("创建时间", auto_now_add=True)
    timeout = models.IntegerField("超时时长", db_column="timeout_time", blank=True, null=True)
    type = models.IntegerField("组件类型", choices=TYPE_CHOICE, default=2)
    comp_conf = models.TextField("组件配置", default="", null=True, blank=True)
    perm_level = models.IntegerField("权限级别", choices=PERM_LEVEL_CHOICE, default=0)
    is_hidden = models.BooleanField("组件是否隐藏", default=False, help_text="是否显示文档，及是否在权限申请中展示")
    rate_limit_required = models.BooleanField("是否校验访问频率", default=False)
    rate_limit_conf = models.TextField(
        "请求频率配置",
        null=True,
        blank=True,
        help_text=(
            "限制访问频率，允许多种规则，例如"
            '{"app_ratelimit": {"__default": {"token":1000, "minute": 1}, "gcloud": {"token":1000, "minute": 1}}}'
        ),
    )
    extra_info = models.TextField("额外信息", default="", blank=True, help_text="存储组件额外信息，用于文档展示等")

    class Meta:
        db_table = "esb_channel"
        unique_together = ("path", "method")

    def __str__(self):
        return self.name

    def clone_to_ng_obj(self):
        from apigateway.apps.esb.bkcore.models import ESBChannel as NGESBChannel

        assert self.ng_system, "ng_system can't be none"

        return NGESBChannel(
            id=self.id,
            system=self.ng_system,
            method=self.method,
            path=self.path,
            name=self.name,
            description=self.description,
            component_codename=self.component_codename,
            permission_level=self.permission_level,
            timeout=self.timeout,
            config=self.config,
            is_active=self.is_active,
            is_public=self.is_public,
            data_type=self.ng_system.data_type,
        )

    def update_ng_obj_fields(self, ng_obj):
        assert self.ng_system, "ng_system can't be none"

        ng_obj.__dict__.update(
            {
                "system": self.ng_system,
                "method": self.method,
                "path": self.path,
                "name": self.name,
                "description": self.description,
                "component_codename": self.component_codename,
                "permission_level": self.permission_level,
                "timeout": self.timeout,
                "config": self.config,
                "is_active": self.is_active,
                "is_public": self.is_public,
                "data_type": self.ng_system.data_type,
            }
        )
        return ng_obj

    def is_changed(self, ng_obj):
        return self.has_different_field_value(
            self,
            ng_obj,
            fields=[
                "method",
                "path",
                "name",
                "description",
                "component_codename",
                "permission_level",
                "timeout",
                "config",
                "is_active",
                "is_public",
            ],
        )

    @property
    def system_id(self):
        return self.component_system_id

    @property
    def permission_level(self) -> str:
        legacy_to_new = {
            0: PermissionLevelEnum.UNLIMITED.value,
            1: PermissionLevelEnum.NORMAL.value,
            2: PermissionLevelEnum.SENSITIVE.value,
            3: PermissionLevelEnum.SPECIAL.value,
        }
        return legacy_to_new[self.perm_level]

    @property
    def is_public(self) -> bool:
        return not self.is_hidden

    @property
    def config(self) -> Dict[str, Any]:
        try:
            return dict(json.loads(self.comp_conf))
        except Exception:
            return {}


class UserAuthToken(models.Model):
    """AuthToken"""

    app_code = models.CharField("蓝鲸智云应用编码", max_length=128)
    username = models.CharField("用户名", max_length=64)
    auth_token = models.CharField("token内容", max_length=255)
    expires = models.DateTimeField("token过期时间")
    last_accessed_time = models.DateTimeField("最后访问时间", auto_now_add=True)
    created_time = models.DateTimeField("创建时间", auto_now_add=True)

    def __str__(self):
        return self.auth_token

    class Meta:
        db_table = "esb_user_auth_token"


class ESBBuffetComponent(models.Model):
    """ESB 组件自助接入"""

    HTTP_METHOD_CHOICES = [
        ("GET", "GET"),
        ("POST", "POST"),
        ("_ORIG", "[所有] 透传原始请求类型(不建议使用)"),
    ]
    FAVOR_CTYPE_CHOICES = [
        ("json", "json"),
        ("form", "form"),
    ]
    TYPE_CHOICE = (
        (1, "执行API"),
        (2, "查询API"),
    )

    description = models.CharField("名称", db_column="name", max_length=256)
    system = models.ForeignKey(ComponentSystem, verbose_name="所属系统", null=True, blank=True, on_delete=models.PROTECT)

    dest_url = models.CharField("目标接口地址", max_length=2048)
    dest_http_method = models.CharField("HTTP请求类型", max_length=8, choices=HTTP_METHOD_CHOICES)
    favor_post_ctype = models.CharField("编码POST参数方式", max_length=64, default="json", choices=FAVOR_CTYPE_CHOICES)
    extra_headers = models.CharField("额外请求头信息", max_length=2048, default="", blank=True)
    extra_params = models.CharField("额外请求参数", max_length=2048, default="", blank=True)

    registed_path = models.CharField("注册到的组件路径", max_length=255)
    registed_http_method = models.CharField("注册到的请求类型", max_length=8, choices=HTTP_METHOD_CHOICES)

    submitter = models.CharField(max_length=256, null=True, default="", blank=True)
    approver = models.CharField(max_length=256, null=True, default="", blank=True)
    approver_message = models.CharField(max_length=1024, null=True, default="", blank=True)
    status = models.IntegerField("状态", default=0)

    mappings_input = models.CharField(
        "输入Mappings", null=True, default="", blank=True, max_length=1024, help_text="JSON格式数据"
    )
    mappings_output = models.CharField(
        "输出Mappings", null=True, default="", blank=True, max_length=1024, help_text="JSON格式数据"
    )
    last_modified_time = models.DateTimeField(auto_now=True)
    created_time = models.DateTimeField(auto_now_add=True)
    timeout_time = models.IntegerField("超时时长", blank=True, null=True, help_text="单位秒，未设置时以所属组件系统超时时长为准")
    type = models.IntegerField("组件类型", choices=TYPE_CHOICE, default=2)

    def __str__(self):
        return self.description

    class Meta:
        db_table = "esb_buffet_component"

    def to_resource(self):
        return {
            "name": self._name,
            "description": self.description,
            "method": self._convert_method(self.registed_http_method),
            "path": self.registed_path,
            "is_public": False,
            "allow_apply_permission": False,
            "labels": [],
            "proxy_type": ProxyTypeEnum.HTTP.value,
            "proxy_configs": {
                ProxyTypeEnum.HTTP.value: {
                    "method": self._convert_method(self.dest_http_method),
                    "path": self._backend_path,
                    "timeout": min(self._timeout, _MAX_APIGATEWAY_TIMEOUT),
                    "upstreams": {
                        "loadbalance": LoadBalanceTypeEnum.RR.value,
                        "hosts": [
                            {
                                "host": self._backend_host,
                                "weight": 100,
                            }
                        ],
                    },
                    "transform_headers": {
                        "set": self._enrich_extra_headers(),
                    },
                }
            },
            "auth_config": {
                "auth_verified_required": False,
                "app_verified_required": False,
                "resource_perm_required": False,
            },
            "disabled_stages": [],
        }

    @property
    def _name(self) -> str:
        name = "_".join(re.findall(r"[a-zA-Z0-9]+", self.registed_path))
        return f"{self._convert_method(self.registed_http_method)}_{name}".lower()

    @property
    def _timeout(self) -> Optional[int]:
        system_timeout = None
        if self.system:
            system_timeout = self.system.timeout

        if system_timeout and self.timeout_time:
            return max(system_timeout, self.timeout_time)

        return _MAX_APIGATEWAY_TIMEOUT

    def _convert_method(self, method: str) -> str:
        if method == "_ORIG":
            return HTTP_METHOD_ANY
        return method

    @property
    def _backend_host(self):
        parsed_url = urllib.parse.urlparse(self.dest_url)
        return f"{parsed_url.scheme}://{parsed_url.netloc}"

    @property
    def _backend_path(self):
        parsed_url = urllib.parse.urlparse(self.dest_url)
        return parsed_url.path

    def _enrich_extra_headers(self) -> Dict[str, str]:
        headers = self._canonical_extra_headers
        if self.dest_http_method != "POST" or "content-type" in [key.lower() for key in headers]:
            return headers

        if self.favor_post_ctype == "form":
            headers.update({"Content-Type": "application/x-www-form-urlencoded"})
        else:
            headers.update({"Content-Type": "application/json"})

        return headers

    @property
    def _canonical_extra_headers(self) -> Dict[str, str]:
        return {key.replace("_", "-"): value for key, value in self.extra_headers_dict.items()}

    @property
    def extra_headers_dict(self):
        try:
            return dict(json.loads(self.extra_headers))
        except Exception:
            return {}


class ESBBuffetMapping(models.Model):
    """ESB 组件自助接入，参数mapping"""

    name = models.CharField("名称", max_length=40, unique=True)
    type = models.IntegerField("类型", null=True, blank=True)
    source_type = models.IntegerField("源码类型")
    source = models.TextField("源码", null=True, default="", blank=True)
    owner = models.CharField(max_length=256, null=True, default="", blank=True)
    is_active = models.BooleanField(default=True)
    last_modified_time = models.DateTimeField(auto_now=True)
    created_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "esb_buffet_component_mapping"


class ModelWithBoard(models.Model):
    """标记组件所属的board"""

    board = models.CharField(max_length=64, null=True, blank=True, db_index=True)

    class Meta:
        abstract = True


class ComponentAPIDoc(ModelWithBoard):
    """
    @summary: 组件API文档
    """

    component_id = models.IntegerField("组件ID", unique=True, help_text="对应 ESBChannel 中的组件ID")
    doc_md = models.TextField("组件文档（MD格式）", blank=True, null=True)
    doc_html = models.TextField("组件文档（HTML格式）", blank=True, null=True)
    doc_md_md5 = models.CharField(max_length=128, default="", blank=True)
    created_time = models.DateTimeField("创建时间", auto_now_add=True)
    updated_time = models.DateTimeField("创建时间", auto_now=True)

    def __str__(self):
        return "%s" % self.component_id

    class Meta:
        verbose_name = "组件接口文档"
        verbose_name_plural = "组件接口文档"
        db_table = "esb_api_doc"

    def split_doc_by_language(self) -> List[dict]:
        return [
            {
                "component_id": self.component_id,
                "language": language,
                "content": content,
                "content_md5": hashlib.md5(force_bytes(content)).hexdigest(),
            }
            for language, content in self.doc_markdowns.items()
        ]

    @property
    def doc_markdowns(self):
        try:
            return json.loads(self.doc_md)
        except Exception:
            return {}


def init_app_comp_perm_expires():
    return timezone.now() + datetime.timedelta(days=180)


class AppComponentPerm(LegacyModelMigrator, models.Model):
    """APP申请的组件权限"""

    bk_app_code = models.CharField("蓝鲸应用编码", db_column="app_code", max_length=64)
    component_id = models.IntegerField("组件ID")
    expires = models.DateTimeField("APP访问组件过期时间", default=init_app_comp_perm_expires)
    created_time = models.DateTimeField("创建时间", auto_now_add=True)
    last_accessed_time = models.DateTimeField("APP最后访问组件时间", default=timezone.now)

    def __str__(self):
        return "<bk_app_code: %s, component_id: %s>" % (self.bk_app_code, self.component_id)

    class Meta:
        verbose_name = "APP组件权限"
        verbose_name_plural = "APP组件权限"
        db_table = "esb_app_component_perm"
        unique_together = ("bk_app_code", "component_id")

    def clone_to_ng_obj(self):
        from apigateway.apps.esb.bkcore.models import AppComponentPermission as NGAppComponentPermission

        return NGAppComponentPermission(
            id=self.id,
            bk_app_code=self.bk_app_code,
            component_id=self.component_id,
            expires=self.expires,
        )

    def update_ng_obj_fields(self, ng_obj):
        ng_obj.__dict__.update(
            {
                "bk_app_code": self.bk_app_code,
                "component_id": self.component_id,
                "expires": self.expires,
            }
        )
        return ng_obj

    def is_changed(self, ng_obj):
        return self.has_different_field_value(
            self,
            ng_obj,
            fields=[
                "bk_app_code",
                "component_id",
                "expires",
            ],
        )


class WxmpAccessToken(models.Model):
    """保存微信开放平台业务的 AccessToken"""

    wx_app_id = models.CharField("微信APPID", max_length=128)
    access_token = models.CharField("凭证", max_length=1024)
    expires = models.DateTimeField("凭证过期时间")
    last_updated_time = models.DateTimeField("最后访问时间", default=timezone.now)

    class Meta:
        db_table = "esb_wxmp_access_token"
        verbose_name = "微信公众号AccessToken"
        verbose_name_plural = "微信公众号AccessToken"

    def __str__(self):
        return self.wx_app_id


class SystemDocCategory(LegacyModelMigrator, models.Model):
    """系统文档分类"""

    name = models.CharField("分类名称", max_length=32, db_index=True)
    priority = models.IntegerField("优先级", default=1000, help_text="展示时，数字小的展示在前面")
    created_time = models.DateTimeField("创建时间", auto_now_add=True)

    objects = SystemDocCategoryManager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "系统文档分类"
        verbose_name_plural = "系统文档分类"
        db_table = "esb_system_doc_category"

    @property
    def is_official(self):
        return self.name in dict(SystemDocCategoryEnum.get_django_choices())

    def clone_to_ng_obj(self):
        from apigateway.apps.esb.bkcore.models import DocCategory as NGDocCategory

        return NGDocCategory(
            id=self.id,
            name=self.name,
            priority=self._ng_priority,
            data_type=self.data_type,
        )

    def update_ng_obj_fields(self, ng_obj):
        ng_obj.__dict__.update(
            {
                "name": self.name,
                "priority": self._ng_priority,
                "data_type": self.data_type,
            }
        )
        return ng_obj

    @property
    def data_type(self) -> int:
        return _convert_is_official_to_data_type(self.is_official)

    @property
    def _ng_priority(self) -> int:
        # 旧版 priority 值越小优先级越高
        # 新版 priority 值越大优先级越高
        # 迁移时，为保障优先级顺序，设置 priority 最大值减去旧版值
        return _MAX_DOC_CATEGORY_PRIORITY - self.priority

    def is_changed(self, ng_obj) -> bool:
        return self.name != ng_obj.name
