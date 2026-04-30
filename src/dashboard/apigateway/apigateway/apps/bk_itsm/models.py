# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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

from apigateway.common.mixins.models import TimestampedModelMixin


class ItsmSystemConfig(TimestampedModelMixin):
    """
    ITSM 系统配置
    保存 system_create 和 system_workflow_create 返回的 ID
    """

    # 系统标识（如 bk_apigateway）
    system_code = models.CharField(max_length=64, unique=True, help_text=_("系统标识"))
    # 系统名称
    system_name = models.CharField(max_length=256, help_text=_("系统名称"))
    # 系统描述
    system_desc = models.CharField(max_length=1024, blank=True, default="", help_text=_("系统描述"))
    # ITSM 返回的系统标识
    itsm_system_id = models.CharField(max_length=64, blank=True, default="", help_text=_("ITSM 系统 ID"))
    # 系统 token，用于调用需要 SYSTEM-TOKEN 的接口
    system_token = models.CharField(max_length=256, blank=True, default="", help_text=_("系统调用 Token"))

    # 流程标识（ITSM 返回的 workflow key）
    workflow_key = models.CharField(max_length=64, blank=True, default="", help_text=_("ITSM 流程标识"))
    # 流程名称
    workflow_name = models.CharField(max_length=256, blank=True, default="", help_text=_("流程名称"))
    # 流程分类
    workflow_category = models.CharField(max_length=64, blank=True, default="", help_text=_("流程分类"))
    # 门户 ID
    portal_id = models.CharField(max_length=64, blank=True, default="DEFAULT", help_text=_("门户 ID"))

    # 是否已注册
    is_registered = models.BooleanField(default=False, help_text=_("是否已完成系统+流程注册"))

    class Meta:
        verbose_name = _("ITSM 系统配置")
        verbose_name_plural = _("ITSM 系统配置")
        db_table = "bk_itsm_system_config"

    def __str__(self):
        return f"<ItsmSystemConfig: {self.system_code}>"
