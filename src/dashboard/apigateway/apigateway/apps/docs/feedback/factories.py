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
from abc import ABCMeta
from typing import Type, Union

from apigateway.common.error_codes import error_codes

from .constants import DocTypeEnum
from .models import Feedback, FeedbackRelatedAPIGateway, FeedbackRelatedComponent


class FeedbackRelatedObjectFactory:
    @staticmethod
    def get(doc_type: str) -> "FeedbackRelatedObject":
        if doc_type == DocTypeEnum.COMPONENT.value:
            return ReleatedComponent()
        if doc_type == DocTypeEnum.APIGATEWAY.value:
            return RelatedAPIGateway()

        raise error_codes.INVALID_ARGUMENT.format(f"unsupported doc_type: {doc_type}")


class FeedbackRelatedObject(metaclass=ABCMeta):
    related_model: Union[Type[FeedbackRelatedComponent], Type[FeedbackRelatedAPIGateway]]

    def create(
        self,
        feedback: Feedback,
        related_data: dict,
    ) -> Union[FeedbackRelatedComponent, FeedbackRelatedAPIGateway, None]:
        return self.related_model.objects.create(feedback=feedback, **related_data)


class ReleatedComponent(FeedbackRelatedObject):
    related_model = FeedbackRelatedComponent


class RelatedAPIGateway(FeedbackRelatedObject):
    related_model = FeedbackRelatedAPIGateway
