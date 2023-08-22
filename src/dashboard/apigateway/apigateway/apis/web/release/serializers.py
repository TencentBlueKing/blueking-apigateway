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
from apigateway.core.constants import PublishEventNameTypeEnum, PublishEventStatusEnum, ReleaseStatusEnum
from apigateway.core.models import ResourceVersion, Stage


class ReleaseBatchInputSLZ(serializers.Serializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault())
    stage_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)
    resource_version_id = serializers.IntegerField(required=True)

    def validate_stage_ids(self, value):
        count = Stage.objects.filter(api=self.context["api"], id__in=value).count()
        if len(value) != count:
            raise Http404

        return value

    def validate_resource_version_id(self, value):
        if not ResourceVersion.objects.filter(gateway=self.context["api"], id=value).exists():
            raise Http404

        return value


class ReleaseHistoryQueryInputSLZ(serializers.Serializer):
    query = serializers.CharField(allow_blank=True, required=False)
    stage_id = serializers.IntegerField(allow_null=True, required=False)
    created_by = serializers.CharField(allow_blank=True, required=False)
    time_start = TimestampField(allow_null=True, required=False)
    time_end = TimestampField(allow_null=True, required=False)


class ReleaseHistoryOutputSLZ(serializers.Serializer):
    stage_names = serializers.SerializerMethodField(read_only=True)
    resource_version_display = serializers.SerializerMethodField(read_only=True)
    created_time = serializers.DateTimeField()
    created_by = serializers.CharField(read_only=True)
    # 发布来源
    source = serializers.CharField(read_only=True)
    # 发布耗时
    cost = serializers.SerializerMethodField(read_only=True)
    # 发布状态
    status = serializers.SerializerMethodField(read_only=True)

    # 是否正在发布(用户前端显示加载图标)
    is_running = serializers.SerializerMethodField(read_only=True)

    def get_stage_names(self, obj):
        return list(obj.stages.order_by("name").values_list("name", flat=True))

    def get_resource_version_display(self, obj):
        return obj.resource_version.object_display

    def get_status(self, obj):
        event = self.context["publish_events_map"].get(obj.id, None)
        if event:
            return f"{event.name} {event.status}"

        # 兼容历史数据
        return obj.message

    def get_cost(self, obj):
        # 获取最新事件
        event = self.context["publish_events_map"].get(obj.id, None)
        if not event:
            return 0
        # 如果失败，返回event的创建时间和release_history创建时间之差
        if event.status == PublishEventStatusEnum.FAILURE.value or (
            event.status != PublishEventStatusEnum.DOING.value
            and event.name == PublishEventNameTypeEnum.LoadConfiguration.value
        ):
            return (event.created_time - obj.created_time).total_seconds()
        # 0代表还没到达终态
        return 0

    def get_is_running(self, obj):
        # 获取最新事件
        event = self.context["publish_events_map"].get(obj.id, None)
        if not event:
            # 兼容老数据
            return obj.status not in [ReleaseStatusEnum.SUCCESS.value, ReleaseStatusEnum.FAILURE.value]
        else:
            # 最新事件是否是doing
            return event.status == PublishEventStatusEnum.DOING.value
