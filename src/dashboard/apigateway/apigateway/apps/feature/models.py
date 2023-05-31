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
from django.utils.translation import gettext_lazy as _

from apigateway.apps.feature.constants import UserFeatureFlagEnum
from apigateway.apps.feature.managers import UserFeatureFlagManager
from apigateway.common.mixins.models import TimestampedModelMixin


class UserFeatureFlag(TimestampedModelMixin):
    """针对用户的功能特性标记"""

    username = models.CharField(max_length=64, db_index=True)
    name = models.CharField(_("特性名称(key)"), max_length=64, choices=UserFeatureFlagEnum.get_choices())
    effect = models.BooleanField(_("是否允许(value)"), default=False)

    objects = UserFeatureFlagManager()

    def __str__(self):
        return f"<UserFeatureFlag: {self.username}/{self.name}>"

    class Meta:
        db_table = "feature_user_feature_flag"
        unique_together = ("username", "name")
