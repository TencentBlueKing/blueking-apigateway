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
from django.utils.translation import gettext as _
from rest_framework import serializers

from apigateway.apps.esb.bkcore.models import ESBChannel


class ComponentIDValidator:
    requires_context = True

    def __call__(self, value, serializer_field):
        if not value:
            return

        component_ids = value
        if isinstance(value, int):
            component_ids = [value]

        assert isinstance(component_ids, list)

        system_id = serializer_field.context["system_id"]
        count = ESBChannel.objects.filter(system_id=system_id, id__in=component_ids).count()
        if count != len(set(component_ids)):
            raise serializers.ValidationError(_("系统【id={system_id}】下指定的部分组件ID不存在。").format(system_id=system_id))
