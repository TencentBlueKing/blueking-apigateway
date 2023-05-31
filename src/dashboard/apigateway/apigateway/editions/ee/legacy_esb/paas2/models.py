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
from django.db import models


class FunctionController(models.Model):
    """功能开关控制器"""

    func_code = models.CharField("功能code", max_length=64, unique=True)
    func_name = models.CharField("功能名称", max_length=64)
    switch_status = models.BooleanField("是否开启该功能", default=True)
    wlist = models.TextField("功能测试白名单", null=True, default="", blank=True)
    func_desc = models.TextField("功能描述", null=True, default="", blank=True)
    created_time = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta(object):
        db_table = "esb_function_controller"

    def __str__(self):
        return self.func_code


class AppAccount(models.Model):
    """应用帐号"""

    app_code = models.CharField("应用编码", max_length=30, unique=True)
    app_token = models.CharField("应用Token", max_length=128)
    introduction = models.TextField("应用简介", default="", blank=True)
    created_time = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta(object):
        db_table = "esb_app_account"

    def __str__(self):
        return self.app_code


class ESBAppPermissionApplyRecord(models.Model):
    """
    应用访问组件 API 权限申请记录
    """

    bk_app_code = models.CharField(db_column="app_code", max_length=32)
    system_name = models.CharField(db_column="sys_name", max_length=128)
    component_id = models.IntegerField(db_column="api_id")
    component_name = models.CharField(db_column="api_name", max_length=128)
    status = models.CharField(db_column="approval_result", max_length=32, default="applying")
    applied_by = models.CharField(db_column="operator", max_length=32)
    applied_time = models.DateTimeField(db_column="create_time", auto_now_add=True, blank=True, null=True)
    handled_by = models.CharField(db_column="approver", max_length=32, blank=True, null=True)
    handled_time = models.DateTimeField(db_column="approval_time", null=True, blank=True)

    class Meta:
        verbose_name = "PaaS2 应用访问组件 API 权限申请记录"
        verbose_name_plural = "PaaS2 应用访问组件 API 权限申请记录"
        db_table = "paas_app_esb_auth_apply_record"
        managed = False

    def __str__(self):
        return f"{self.applied_by}({self.bk_app_code})"
