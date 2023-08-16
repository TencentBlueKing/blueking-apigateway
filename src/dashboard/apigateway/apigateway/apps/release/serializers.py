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
from django.http import Http404
from rest_framework import serializers

from apigateway.common.fields import CurrentGatewayDefault, TimestampField
from apigateway.core.models import Release, ReleaseHistory, ResourceVersion, Stage


class ReleaseBatchSLZ(serializers.ModelSerializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault())
    stage_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)
    resource_version_id = serializers.IntegerField(required=True)

    class Meta:
        model = Release
        fields = [
            "gateway",
            "stage_ids",
            "resource_version_id",
            "comment",
        ]
        lookup_field = "id"

    def validate_stage_ids(self, value):
        count = Stage.objects.filter(api=self.context["api"], id__in=value).count()
        if len(value) != count:
            raise Http404

        return value

    def validate_resource_version_id(self, value):
        if not ResourceVersion.objects.filter(gateway=self.context["api"], id=value).exists():
            raise Http404

        return value


class ReleaseHistoryQuerySLZ(serializers.Serializer):
    query = serializers.CharField(allow_blank=True, required=False)
    stage_id = serializers.IntegerField(allow_null=True, required=False)
    created_by = serializers.CharField(allow_blank=True, required=False)
    time_start = TimestampField(allow_null=True, required=False)
    time_end = TimestampField(allow_null=True, required=False)


class ReleaseHistorySLZ(serializers.ModelSerializer):
    stage_names = serializers.SerializerMethodField()
    resource_version_name = serializers.SerializerMethodField()
    resource_version_title = serializers.SerializerMethodField()
    resource_version_comment = serializers.SerializerMethodField()
    resource_version_display = serializers.SerializerMethodField()

    class Meta:
        model = ReleaseHistory
        fields = (
            "stage_names",
            "created_time",
            "comment",
            "resource_version_name",
            "resource_version_title",
            "resource_version_comment",
            "resource_version_display",
            "created_by",
            "status",
            "message",
        )

    def get_stage_name(self, obj):
        return obj.stage.name

    def get_stage_names(self, obj):
        return list(obj.stages.order_by("name").values_list("name", flat=True))

    def get_resource_version_name(self, obj):
        return obj.resource_version.name

    def get_resource_version_title(self, obj):
        return obj.resource_version.title

    def get_resource_version_comment(self, obj):
        return obj.resource_version.comment

    def get_resource_version_display(self, obj):
        return obj.resource_version.object_display
