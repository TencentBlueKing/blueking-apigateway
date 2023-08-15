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
from django.db import transaction
from rest_framework import viewsets

from apigateway.utils.responses import V1OKJsonResponse

from .factories import FeedbackRelatedObjectFactory
from .serializers import FeedbackCreateSLZ


class FeedbackViewSet(viewsets.GenericViewSet):
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """新增文档反馈"""
        slz = FeedbackCreateSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        # 1. save feedback
        slz.save(
            created_by=request.user.username,
            updated_by=request.user.username,
        )

        # 2. save related data
        doc_type = slz.validated_data["doc_type"]
        if slz.has_related_field(doc_type):
            related_field_key = slz.get_related_field_key(doc_type)
            related_obj = FeedbackRelatedObjectFactory.get(doc_type)
            related_obj.create(slz.instance, slz.validated_data.get(related_field_key))

        # TODO
        # 3. 发送通知
        # 反馈文档有帮助，不发送通知
        if slz.validated_data.get("positive"):
            return V1OKJsonResponse("OK", data={})

        return V1OKJsonResponse("OK", data={})
