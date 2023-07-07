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
from django.utils.translation import gettext as _

from apigateway.common.mixins.models import TimestampedModelMixin
from apigateway.core.models import Gateway
from apigateway.iam.constants import UserRoleEnum


class IAMGradeManager(TimestampedModelMixin):
    """
    网关的 IAM 分级管理员

    分级管理员管理用户加入用户组的申请
    """

    gateway = models.ForeignKey(Gateway, on_delete=models.PROTECT)
    grade_manager_id = models.IntegerField(help_text="IAM 分级管理员 ID")

    class Meta:
        verbose_name = _("IAM 分级管理员")
        verbose_name_plural = _("IAM 分级管理员")
        unique_together = ("gateway", "grade_manager_id")
        db_table = "iam_grade_manager"

    def __str__(self):
        return f"<IAMGradeManager: {self.pk}>"


class IAMUserGroup(TimestampedModelMixin):
    """网关用户角色的 IAM 用户组"""

    gateway = models.ForeignKey(Gateway, on_delete=models.PROTECT)
    role = models.CharField(max_length=32, default=UserRoleEnum.DEVELOPER.value)
    user_group_id = models.IntegerField(help_text="IAM 用户组 ID")

    class Meta:
        verbose_name = _("IAM 用户组")
        verbose_name_plural = _("IAM 用户组")
        unique_together = ("gateway", "role")
        db_table = "iam_user_group"

    def __str__(self):
        return f"<IAMUserGroup: {self.pk}/{self.role}>"
