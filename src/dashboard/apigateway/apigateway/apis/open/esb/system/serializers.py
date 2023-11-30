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
from django.conf import settings
from rest_framework import serializers

from apigateway.apis.web.constants import UserAuthTypeEnum
from apigateway.apps.esb.helpers import BoardConfigManager
from apigateway.apps.esb.utils import get_related_boards
from apigateway.tencent_apigateway_common.i18n.field import SerializerTranslatedField


class SystemQueryV1SLZ(serializers.Serializer):
    user_auth_type = serializers.ChoiceField(choices=UserAuthTypeEnum.get_choices())

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        data["boards"] = get_related_boards(data["user_auth_type"])
        return data


class SystemV1SLZ(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = SerializerTranslatedField(translated_fields={"en": "description_en"}, allow_blank=True)
    description_en = serializers.CharField(required=False)
    maintainers = serializers.SerializerMethodField()
    tag = serializers.SerializerMethodField()

    def get_maintainers(self, obj):
        """获取 ESB 系统的管理员"""
        return settings.ESB_MANAGERS

    def get_tag(self, obj):
        return BoardConfigManager.get_optional_display_label(obj.board)
