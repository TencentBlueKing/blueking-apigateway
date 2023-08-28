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

from apigateway.core.utils import get_path_display, get_resource_url


class ResourceOutputV1SLZ(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = SerializerTranslatedField(
        default_field="description_i18n", translated_fields={"en": "description_en"}
    )
    description_en = serializers.CharField(default=None, required=False, write_only=True)
    method = serializers.CharField()
    path = serializers.CharField()


class ReleasedResourceSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    method = serializers.CharField(read_only=True)
    path = serializers.CharField(read_only=True)


class ReleasedResourceListV1SLZ(ResourceOutputV1SLZ):
    app_verified_required = serializers.BooleanField()
    resource_perm_required = serializers.BooleanField()
    user_verified_required = serializers.BooleanField()
    labels = serializers.SerializerMethodField()
    description = SerializerTranslatedField(translated_fields={"en": "description_en"})

    def get_labels(self, obj):
        return self.context["resource_labels"].get(obj["id"], [])


class ListReleasedResourceV2SLZ(ResourceOutputV1SLZ):
    app_verified_required = serializers.BooleanField()
    resource_perm_required = serializers.BooleanField()
    user_verified_required = serializers.BooleanField()
    url = serializers.SerializerMethodField()
    description = SerializerTranslatedField(translated_fields={"en": "description_en"})
    match_subpath = serializers.BooleanField()
    path = None

    def get_url(self, obj):
        return get_resource_url(
            resource_url_tmpl=self.context["resource_url_tmpl"],
            gateway_name=self.context["api_name"],
            stage_name=self.context["stage_name"],
            resource_path=get_path_display(obj["path"], obj["match_subpath"]),
        )
