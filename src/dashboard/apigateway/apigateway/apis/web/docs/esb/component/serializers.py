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
from rest_framework import serializers
from tencent_apigateway_common.i18n.field import SerializerTranslatedField

from apigateway.apps.permission.constants import PermissionLevelEnum


class ComponentSearchInputSLZ(serializers.Serializer):
    query = serializers.CharField(required=False, allow_blank=True)


class ComponentSearchOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = SerializerTranslatedField(translated_fields={"en": "description_en"}, default_field="description")
    system_name = serializers.CharField(source="system.name")


class ComponentOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = SerializerTranslatedField(
        translated_fields={"en": "description_en"}, default_field="description", read_only=True
    )
    verified_app_required = serializers.SerializerMethodField()
    verified_user_required = serializers.SerializerMethodField()
    component_permission_required = serializers.SerializerMethodField()

    def get_verified_app_required(self, obj):
        return True

    def get_verified_user_required(self, obj):
        return True

    def get_component_permission_required(self, obj):
        return obj.permission_level != PermissionLevelEnum.UNLIMITED.value
