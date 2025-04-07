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

from apigateway.common.i18n.field import SerializerTranslatedField


class GatewayListInputSLZ(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True)
    fuzzy = serializers.BooleanField(required=False)

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.GatewayListInputSLZ"


class GatewayListOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = SerializerTranslatedField(default_field="description_i18n", allow_blank=True, read_only=True)
    maintainers = serializers.SerializerMethodField()
    doc_maintainers = serializers.SerializerMethodField()

    def get_maintainers(self, obj):
        return obj.maintainers

    def get_doc_maintainers(self, obj):
        return obj.doc_maintainers

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.GatewayListOutputSLZ"


class GatewayRetrieveOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = SerializerTranslatedField(default_field="description_i18n", allow_blank=True, read_only=True)
    maintainers = serializers.SerializerMethodField()
    doc_maintainers = serializers.SerializerMethodField()

    def get_maintainers(self, obj):
        return obj.maintainers

    def get_doc_maintainers(self, obj):
        return obj.doc_maintainers

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.GatewayRetrieveOutputSLZ"
